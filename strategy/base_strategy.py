"""
策略抽象基类
定义标准策略接口，方便扩展其他策略（如低价策略、溢价率策略等）
"""
from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class BaseStrategy(ABC):
    """策略抽象基类"""
    
    def __init__(self, name: str):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        分析数据，返回筛选结果
        
        Args:
            df: 转债数据
            
        Returns:
            DataFrame: 筛选后的转债数据（包含策略相关字段）
        """
        pass
    
    @abstractmethod
    def get_params(self) -> Dict:
        """
        获取策略参数
        
        Returns:
            Dict: 策略参数字典
        """
        pass

