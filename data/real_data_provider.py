"""
真实数据提供者 (v2)
整合 EfinanceProvider + AkshareProvider，混合数据源
"""
import pandas as pd
import logging
from data.akshare_provider import AkshareProvider
from data.efinance_provider import EfinanceProvider

logger = logging.getLogger(__name__)


class RealDataProvider:

    def __init__(self):
        self.akshare_provider = AkshareProvider()
        self.efinance_provider = EfinanceProvider()

    def fetch_convertible_bonds(self) -> pd.DataFrame:
        logger.info("=" * 60)
        logger.info("开始获取可转债数据 (efinance + akshare 混合)...")
        logger.info("=" * 60)

        # Step 1: efinance for broad universe (price, rating, stock info)
        df_ef = pd.DataFrame()
        try:
            df_ef = self.efinance_provider.get_bond_list()
            logger.info(f"efinance: {len(df_ef)} 只")
        except Exception as e:
            logger.warning(f"efinance 失败，回退纯 akshare: {e}")

        # Step 2: akshare for premium_rate, remain_amount, double_low
        df_ak = pd.DataFrame()
        try:
            df_ak = self.akshare_provider.get_bond_list()
            logger.info(f"akshare: {len(df_ak)} 只")
        except Exception as e:
            logger.warning(f"akshare 失败: {e}")

        # Step 3: Merge
        if not df_ef.empty and not df_ak.empty:
            # Use efinance as base, supplement with akshare premium_rate
            ak_cols = ['code', 'premium_rate', 'remain_amount', 'double_low']
            ak_supp = df_ak[[c for c in ak_cols if c in df_ak.columns]].copy()
            df = df_ef.merge(ak_supp, on='code', how='left', suffixes=('', '_ak'))
            # Prefer akshare remain_amount if available
            if 'remain_amount_ak' in df.columns:
                df['remain_amount'] = df['remain_amount_ak'].fillna(df['remain_amount'])
                df = df.drop(columns=['remain_amount_ak'])
            logger.info(f"合并后: {len(df)} 只，{df['premium_rate'].notna().sum()} 只有溢价率")
        elif not df_ef.empty:
            df = df_ef
            logger.info("仅 efinance 数据")
        elif not df_ak.empty:
            df = df_ak
            logger.info("仅 akshare 数据")
        else:
            logger.error("无法获取任何数据")
            return pd.DataFrame()

        # Drop bonds without minimum required fields
        df = df.dropna(subset=['code', 'name', 'price'])

        logger.info(f"最终: {len(df)} 只可转债")
        logger.info("=" * 60)
        return df

    def fetch_bond_info(self, code: str) -> pd.DataFrame:
        logger.info(f"获取转债 {code} 的详细信息...")
        try:
            import akshare as ak
            df = ak.bond_cb_jsl()
            if df.empty:
                return pd.DataFrame()
            bond_df = df[df['代码'] == code]
            return bond_df
        except Exception as e:
            logger.error(f"获取失败: {e}")
            return pd.DataFrame()
