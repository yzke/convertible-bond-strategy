"""
Akshare数据源实现
"""
import akshare as ak
import pandas as pd
import logging
from data.provider import DataProvider

# 配置日志
logger = logging.getLogger(__name__)

class AkshareProvider(DataProvider):
    """Akshare数据提供者"""
    
    # 类常量：过滤规则
    FILTER_KEYWORDS = ['ST', '*ST', '退']
    
    # 列名映射（可能随Akshare版本变化）
    # 列名映射（对应Akshare返回的中文列名）
    COLUMN_MAPPING = {
        '代码': 'code',
        '转债名称': 'name',
        '现价': 'price',
        '涨跌幅': 'change_pct',
        '正股代码': 'stock_code',
        '正股名称': 'stock_name',
        '正股价': 'stock_price',
        '正股涨跌': 'stock_change_pct',
        '正股PB': 'stock_pb',
        '转股价': 'convert_price',
        '转股价值': 'convert_value',
        '转股溢价率': 'premium_rate',
        '债券评级': 'rating',
        '回售触发价': 'put_trigger_price',
        '强赎触发价': 'call_trigger_price',
        '转债占比': 'bond_ratio',
        '到期时间': 'maturity_date',
        '剩余年限': 'remain_years',
        '剩余规模': 'remain_amount',
        '成交额': 'turnover_amount',
        '换手率': 'turnover_rate',
        '到期税前收益': 'ytm',
        '双低': 'double_low'
    }




    def get_bond_list(self) -> pd.DataFrame:
        """
        获取所有转债基础信息
        
        Returns:
            DataFrame: 清洗后的转债数据
            空DataFrame表示获取失败
        """
        try:
            logger.info("正在获取转债列表...")
            df = ak.bond_cb_jsl()
            
            if df.empty:
                logger.warning("获取到的数据为空")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条转债原始数据")
            
            # 🔴 A. 打印原始列名，方便调试字段变动
            logger.info(f"原始列名: {list(df.columns)}")
            
            # 重命名列，只映射存在的列
            existing_mapping = {k: v for k, v in self.COLUMN_MAPPING.items() if k in df.columns}
            if len(existing_mapping) < len(self.COLUMN_MAPPING):
                missing = set(self.COLUMN_MAPPING.keys()) - set(existing_mapping.keys())
                logger.warning(f"部分字段缺失: {missing} (可能是Akshare字段变动)")
            
            df = df.rename(columns=existing_mapping)
            
            # 🔴 B. 稳健的百分比字段清洗
            df = self._clean_percentage_fields(df)
            
            # 过滤掉ST等特殊转债
            df = self._filter_special_bonds(df)
            
            # 移除空值过多的行
            df = df.dropna(subset=['code', 'name', 'price'])
            
            logger.info(f"数据清洗后剩余 {len(df)} 条有效数据")
            
            return df
            
        except ImportError as e:
            logger.error(f"缺少依赖库: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取转债列表失败: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _clean_percentage_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗百分比字段，兼容字符串和数值型
        
        策略：
        1. 先转为字符串
        2. 删除百分号
        3. 转为数值（失败则填充为0）
        
        这样可以兼容：
        - "12.34%" → 12.34
        - 12.34 → 12.34
        - "12.34" → 12.34
        """
        percentage_fields = ['premium_rate', 'turnover_rate']
        
        for field in percentage_fields:
            if field in df.columns:
                # 🔴 B. 兼容处理：先转字符删百分号，如果失败则转数值，最后强制填充空值为0
                df[field] = pd.to_numeric(
                    df[field].astype(str).str.replace('%', ''),
                    errors='coerce'
                ).fillna(0)
        
        return df
    
    def _filter_special_bonds(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        过滤特殊转债（ST、退市等）
        
        注意：此方法只过滤转债名称中的关键词，不检查正股状态。
        对于小资金实验，这足以挡住90%的风险。
        如需更严格的过滤，需要额外获取正股状态。
        """
        # 构建过滤条件
        mask = pd.Series([True] * len(df), index=df.index)
        
        for keyword in self.FILTER_KEYWORDS:
            mask &= ~df['name'].str.contains(keyword, na=False,regex=False)
        
        filtered_df = df[mask]
        
        if len(filtered_df) < len(df):
            logger.info(f"过滤掉 {len(df) - len(filtered_df)} 条特殊转债")
        
        return filtered_df

