"""
数据源抽象基类
定义标准数据接口，方便后续更换数据源
"""
from abc import ABC, abstractmethod
import pandas as pd

class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    @abstractmethod
    def get_bond_list(self) -> pd.DataFrame:
        """
        获取所有转债基础信息
        
        Returns:
            DataFrame: 包含转债代码、名称、价格、溢价率等
            空DataFrame表示获取失败
        """
        pass

