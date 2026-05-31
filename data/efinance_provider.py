import pandas as pd
import logging
import efinance as ef

logger = logging.getLogger(__name__)

class EfinanceProvider:
    def get_bond_list(self):
        try:
            logger.info("efinance: getting realtime quotes...")
            rt = ef.bond.get_realtime_quotes()
            logger.info(f"efinance: got {len(rt)} bonds")

            logger.info("efinance: getting base info...")
            bi = ef.bond.get_all_base_info()
            logger.info(f"efinance: got {len(bi)} base info records")

            df = rt.merge(
                bi[['债券代码', '债券评级', '正股代码', '正股名称', '到期日期', '发行规模(亿)']],
                on='债券代码', how='left'
            )

            df = df.rename(columns={
                '债券代码': 'code', '债券名称': 'name', '最新价': 'price',
                '涨跌幅': 'change_pct', '换手率': 'turnover_rate',
                '债券评级': 'rating', '正股代码': 'stock_code',
                '正股名称': 'stock_name', '到期日期': 'maturity_date',
                '发行规模(亿)': 'remain_amount',
            })

            df = df.dropna(subset=['price'])
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df[df['price'] > 0]
            df['premium_rate'] = float('nan')
            df['remain_amount'] = pd.to_numeric(df.get('remain_amount', 0), errors='coerce')

            cols = ['code', 'name', 'price', 'premium_rate', 'remain_amount', 'rating',
                    'change_pct', 'turnover_rate', 'stock_code', 'stock_name', 'maturity_date']
            available = [c for c in cols if c in df.columns]
            logger.info(f"efinance: final {len(df)} bonds ready")
            return df[available]
        except Exception as e:
            logger.error(f"efinance failed: {e}", exc_info=True)
            return pd.DataFrame()
