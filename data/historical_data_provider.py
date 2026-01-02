"""
历史数据提供者
获取可转债历史数据

修正内容：
1. ✅ 添加 numpy 导入
2. ✅ 修复模拟数据格式错误
3. ✅ 修复未定义变量 n 的问题
4. ✅ 添加随机种子设置
5. ✅ 改进警告信息
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Optional

# 配置日志
logger = logging.getLogger(__name__)


class HistoricalDataProvider:
    """历史数据提供者"""
    
    def __init__(self, random_seed: int = 42):
        """
        初始化历史数据提供者
        
        Args:
            random_seed: 随机种子，用于模拟数据
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
    
    def fetch_historical_data(
        self,
        start_date: str,
        end_date: str,
        codes: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取历史数据
        
        修正：
        1. ✅ 添加 numpy 导入
        2. ✅ 修复模拟数据格式错误
        3. ✅ 修复未定义变量 n 的问题
        4. ✅ 改进警告信息
        
        Args:
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            codes: 转债代码列表，None表示获取所有转债
            
        Returns:
            pd.DataFrame: 历史数据，包含列：
                - date: 日期
                - code: 转债代码
                - name: 转债名称
                - price: 转债价格
                - premium_rate: 溢价率（%）
                - remain_amount: 剩余规模（亿元）
        """
        logger.info("="*60)
        logger.info(f"开始获取历史数据: {start_date} ~ {end_date}")
        if codes:
            logger.info(f"转债代码: {codes}")
        logger.info("="*60)
        
        try:
            # 修正：使用正确的随机种子
            np.random.seed(self.random_seed)
            
            # 获取历史数据
            # 注意：akshare的历史数据接口可能需要调整
            # 这里使用模拟数据作为示例
            logger.warning(
                "⚠️  akshare历史数据接口可能不支持，使用模拟数据。"
                "实际生产环境请替换为真实数据源。"
            )
            
            # 模拟历史数据
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
            
            data = []
            for date in dates:
                # 修正：在循环内定义 n，避免未定义变量错误
                n = 100
                
                # 修正：创建DataFrame而不是包含列表/Series的字典
                daily_df = pd.DataFrame({
                    'date': [date] * n,
                    'code': [f"12{i:04d}" for i in range(1, n+1)],
                    'name': [f"转债{i:03d}" for i in range(1, n+1)],
                    'price': [100 + np.random.randn() * 5 for _ in range(n)],
                    'premium_rate': [np.random.uniform(-5, 30) for _ in range(n)],
                    'remain_amount': [np.random.uniform(0.5, 10) for _ in range(n)]
                })
                data.append(daily_df)
            
            # 合并所有数据
            result_df = pd.concat(data, ignore_index=True)
            
            logger.info(f"成功获取 {len(dates)} 个交易日的数据")
            logger.info(f"总数据量: {len(result_df)} 条")
            logger.info("="*60)
            
            return result_df
        
        except Exception as e:
            logger.error(f"获取历史数据时发生错误: {e}", exc_info=True)
            return pd.DataFrame()

