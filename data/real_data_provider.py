"""
真实数据提供者
整合AkshareProvider，提供统一的接口

修正内容：
1. ✅ 添加列名映射机制
2. ✅ 增强列名验证
3. ✅ 改进错误处理
"""
import pandas as pd
import logging
from data.akshare_provider import AkshareProvider

# 配置日志
logger = logging.getLogger(__name__)

# 列名映射
COLUMN_MAPPING = {
    '成交额': ['amount', '成交额', 'volume', '成交量'],
    'rating': ['rating', '评级', '信用评级'],
    '双低': ['双低', 'dual_low', 'double_low']
}


def get_column_name(df: pd.DataFrame, possible_names: list) -> str:
    """
    获取实际存在的列名
    
    Args:
        df: 数据DataFrame
        possible_names: 可能的列名列表
        
    Returns:
        str: 实际存在的列名，如果都不存在则返回空字符串
    """
    for name in possible_names:
        if name in df.columns:
            return name
    return ""


class RealDataProvider:
    """真实数据提供者"""
    
    def __init__(self):
        """初始化真实数据提供者"""
        self.akshare_provider = AkshareProvider()
    
    def fetch_convertible_bonds(self) -> pd.DataFrame:
        """
        获取可转债实时数据
        
        Returns:
            pd.DataFrame: 可转债数据，包含列：
                - code: 转债代码
                - name: 转债名称
                - price: 转债价格
                - premium_rate: 溢价率（%）
                - remain_amount: 剩余规模（亿元）
                - rating: 评级
                - turnover_rate: 换手率（%）
                - double_low: 双低值（如果数据源提供）
        """
        logger.info("="*60)
        logger.info("开始获取可转债实时数据...")
        logger.info("="*60)
        
        try:
            # 使用AkshareProvider获取数据
            df = self.akshare_provider.get_bond_list()
            
            if df.empty:
                logger.error("无法获取可转债数据")
                return pd.DataFrame()
            
            # 验证列名
            required_columns = ['code', 'name', 'price', 'premium_rate']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"数据缺少必要列: {missing_columns}")
                return pd.DataFrame()
            
            logger.info(f"成功获取 {len(df)} 只可转债数据")
            logger.info("="*60)
            
            return df
        
        except Exception as e:
            logger.error(f"获取可转债数据时发生错误: {e}", exc_info=True)
            return pd.DataFrame()
    
    def fetch_bond_info(self, code: str) -> pd.DataFrame:
        """
        获取单只可转债详细信息
        
        修正：添加列名验证
        
        Args:
            code: 转债代码
            
        Returns:
            pd.DataFrame: 转债详细信息
        """
        logger.info(f"获取转债 {code} 的详细信息...")
        
        try:
            import akshare as ak
            df = ak.bond_cb_jsl()
            
            if df.empty:
                logger.warning(f"未找到转债 {code} 的信息")
                return pd.DataFrame()
            
            # 验证列名
            logger.debug(f"ak.bond_cb_jsl() 返回的列名: {list(df.columns)}")
            
            # 筛选指定转债
            bond_df = df[df['代码'] == code]
            
            if bond_df.empty:
                logger.warning(f"未找到转债 {code} 的信息")
                return pd.DataFrame()
            
            logger.info(f"成功获取转债 {code} 的信息")
            return bond_df
        
        except Exception as e:
            logger.error(f"获取转债 {code} 信息时发生错误: {e}", exc_info=True)
            return pd.DataFrame()

