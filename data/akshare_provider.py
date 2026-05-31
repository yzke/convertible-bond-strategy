"""
Akshare数据源实现 (集思录Cookie增强版 + 自动登录刷新)
"""
import akshare as ak
import pandas as pd
import logging
from data.provider import DataProvider
from jisilu_login import get_valid_cookie, refresh_cookie

# 配置日志
logger = logging.getLogger(__name__)

class AkshareProvider(DataProvider):
    """Akshare数据提供者 — 自动管理集思录 Cookie"""

    # 类常量：过滤规则
    FILTER_KEYWORDS = ['ST', '*ST', '退']

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
        获取所有转债基础信息（自动管理 Cookie）
        """
        # 获取有效 cookie（自动加载或重新登录）
        try:
            cookie = get_valid_cookie()
        except Exception as e:
            logger.error(f"Cookie 加载失败: {e}")
            return pd.DataFrame()

        # 尝试获取数据，cookie 失效时自动刷新重试
        for attempt in range(2):
            try:
                logger.info(f"正在获取转债列表{' (自动刷新)' if attempt > 0 else ''} ...")
                df = ak.bond_cb_jsl(cookie=cookie)

                if df is None or df.empty:
                    logger.warning("获取到的数据为空")
                    if attempt == 0:
                        cookie = refresh_cookie()
                    continue

                # 如果数据太少（<50条），说明 cookie 已失效
                if len(df) < 50 and attempt == 0:
                    logger.warning(f"仅获取到 {len(df)} 条数据，Cookie 可能已过期，尝试刷新...")
                    cookie = refresh_cookie()
                    continue

                logger.info(f"获取到 {len(df)} 条转债原始数据")
                break

            except Exception as e:
                logger.error(f"获取转债列表失败 (attempt {attempt+1}/2): {e}")
                if attempt == 0:
                    try:
                        cookie = refresh_cookie()
                    except Exception:
                        pass
                else:
                    return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        # 重命名列
        existing_mapping = {k: v for k, v in self.COLUMN_MAPPING.items() if k in df.columns}
        df = df.rename(columns=existing_mapping)

        # 稳健的百分比字段清洗
        df = self._clean_percentage_fields(df)

        # 过滤掉ST等特殊转债
        df = self._filter_special_bonds(df)

        # 移除空值过多的行
        df = df.dropna(subset=['code', 'name', 'price'])

        logger.info(f"数据清洗后剩余 {len(df)} 条有效数据")

        return df

    def _clean_percentage_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        percentage_fields = ['premium_rate', 'turnover_rate']
        for field in percentage_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(
                    df[field].astype(str).str.replace('%', ''),
                    errors='coerce'
                ).fillna(0)
        return df

    def _filter_special_bonds(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = pd.Series([True] * len(df), index=df.index)
        for keyword in self.FILTER_KEYWORDS:
            mask &= ~df['name'].str.contains(keyword, na=False, regex=False)
        return df[mask]
