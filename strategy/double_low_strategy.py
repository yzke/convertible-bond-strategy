"""
双低策略实现
双低 = 价格 + 溢价率

注意：数据源中的溢价率已经是数值形式（例如 5.00 代表 5.00%），
因此直接相加即可，无需乘以 100。

双低值越小，代表价格越低且溢价率越低，投资价值越高。
"""
import pandas as pd
import logging
from typing import Dict, Optional
from strategy.base_strategy import BaseStrategy

# 配置日志
logger = logging.getLogger(__name__)

class DoubleLowStrategy(BaseStrategy):
    """双低策略"""
    
    # 国内可转债评级顺序（从低到高）
    RATING_ORDER = [
        'C', 'CC', 'CCC',
        'B-', 'B', 'B+',
        'BB-', 'BB', 'BB+',
        'BBB-', 'BBB', 'BBB+',
        'A-', 'A', 'A+',
        'AA-', 'AA', 'AA+',
        'AAA'
    ]
    
    def __init__(
        self,
        max_price: float = 130.0,
        max_amount: float = 10.0,
        min_rating: Optional[str] = 'A',
        allow_unknown_rating: bool = False,
        top_n: int = 10,
        filter_negative_premium: bool = False
    ):
        """
        初始化双低策略
        
        Args:
            max_price: 最大价格（元），默认130
            max_amount: 最大剩余规模（亿元），默认10
            min_rating: 最低评级（含），默认'A'，设为None表示不筛选评级
            allow_unknown_rating: 是否允许空值/未知评级的转债通过，默认False
                                 注意：如果为True，未知评级会被包含，但不会被视为AAA
            top_n: 返回前N个转债，默认10
            filter_negative_premium: 是否过滤负溢价率转债，默认False
        """
        super().__init__("双低策略")
        self.max_price = max_price
        self.max_amount = max_amount
        self.min_rating = min_rating
        self.allow_unknown_rating = allow_unknown_rating
        self.top_n = top_n
        self.filter_negative_premium = filter_negative_premium
    
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        分析数据，返回双低值最低的前N个转债
        
        Args:
            df: 转债数据，必须包含 price, premium_rate, remain_amount 字段
                其中 premium_rate 应为数值类型（如 5.0 代表 5%）
            
        Returns:
            DataFrame: 筛选后的转债数据，新增 double_low 字段
        """
        # 检查必要字段
        required_fields = ['code', 'name', 'price', 'premium_rate', 'remain_amount']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            logger.warning(f"数据缺少必要字段: {missing_fields}")
            return pd.DataFrame()
        
        logger.info(f"开始双低策略分析，原始数据量: {len(df)}")
        
        # 复制数据，避免修改原始DataFrame
        result_df = df.copy()
        
        # 过滤空值
        result_df = result_df.dropna(subset=['price', 'premium_rate', 'remain_amount'])
        logger.info(f"过滤空值后数据量: {len(result_df)}")
        
        # 计算双低值：价格 + 溢价率
        result_df['double_low'] = result_df['price'] + result_df['premium_rate']
        
        # 筛选条件1：价格低于阈值
        condition1 = result_df['price'] <= self.max_price
        logger.info(f"价格≤{self.max_price}元: {condition1.sum()} 条")
        
        # 筛选条件2：剩余规模低于阈值
        condition2 = result_df['remain_amount'] <= self.max_amount
        logger.info(f"规模≤{self.max_amount}亿: {condition2.sum()} 条")
        
        # 筛选条件3：评级过滤（如果设置了）
        if self.min_rating:
            condition3 = self._filter_by_rating(result_df, self.min_rating)
            logger.info(f"评级≥{self.min_rating}: {condition3.sum()} 条")
        else:
            condition3 = pd.Series([True] * len(result_df), index=result_df.index)
        
        # 筛选条件4：负溢价率过滤（可选）
        if self.filter_negative_premium:
            condition4 = result_df['premium_rate'] >= 0
            logger.info(f"溢价率≥0%: {condition4.sum()} 条")
        else:
            condition4 = pd.Series([True] * len(result_df), index=result_df.index)
        
        # 组合所有条件
        mask = condition1 & condition2 & condition3 & condition4
        
        # 应用筛选
        filtered_df = result_df[mask]
        logger.info(f"筛选后数据量: {len(filtered_df)} 条")
        
        # 按双低值升序排序
        filtered_df = filtered_df.sort_values('double_low', ascending=True)
        
        # 取前N个
        final_df = filtered_df.head(self.top_n)
        
        logger.info(f"最终返回前 {len(final_df)} 个转债")
        
        return final_df
    
    def _filter_by_rating(self, df: pd.DataFrame, min_rating: str) -> pd.Series:
        """
        根据评级过滤
        
        逻辑修正：
        1. 将已知评级映射为数值索引进行比较
        2. 对于未知评级，不提升其索引，而是通过布尔逻辑单独处理
        
        Args:
            df: 转债数据
            min_rating: 最低评级（含）
            
        Returns:
            Series: 布尔值Series，True表示符合评级要求
        """
        if 'rating' not in df.columns:
            logger.warning(f"数据缺少 rating 字段，跳过评级筛选")
            return pd.Series([True] * len(df), index=df.index)
        
        # 获取最低评级的索引
        try:
            min_index = self.RATING_ORDER.index(min_rating)
        except ValueError:
            logger.warning(f"未知评级: {min_rating}，跳过评级筛选")
            return pd.Series([True] * len(df), index=df.index)
        
        # 1. 标记未知评级（空值 或 不在评级列表中的字符串）
        is_unknown = df['rating'].isna() | ~df['rating'].isin(self.RATING_ORDER)
        
        # 2. 将评级转换为数值索引
        # 对于已知评级，获取其索引；对于未知评级，暂时赋值为 -1（不满足任何 >= min_index 的条件）
        def get_rating_index(rating):
            try:
                return self.RATING_ORDER.index(rating)
            except (ValueError, TypeError, AttributeError):
                return -1  # 未知评级默认不通过
        
        rating_indices = df['rating'].apply(get_rating_index)
        
        # 3. 基础筛选：评级索引 >= 最低评级索引
        # 此时未知评级（-1）肯定不通过
        mask = rating_indices >= min_index
        
        # 4. 如果允许未知评级，通过逻辑或（OR）将未知评级加入结果集
        # 这样既保留了数值比较的准确性，又实现了允许未知评级的灵活性
        if self.allow_unknown_rating:
            mask = mask | is_unknown
        
        return mask
    
    def get_params(self) -> Dict:
        """
        获取策略参数
        
        Returns:
            Dict: 策略参数字典
        """
        return {
            'strategy_name': self.name,
            'max_price': self.max_price,
            'max_amount': self.max_amount,
            'min_rating': self.min_rating,
            'allow_unknown_rating': self.allow_unknown_rating,
            'top_n': self.top_n,
            'filter_negative_premium': self.filter_negative_premium
        }

