"""
交易订单定义

修正内容：
1. ✅ 使用工厂方法创建订单，确保amount和quantity的一致性
2. ✅ 明确买入和卖出订单的语义差异
3. ✅ 添加 __repr__ 方法（便于调试）
"""
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

class OrderType(Enum):
    """订单类型"""
    BUY = "buy"   # 买入
    SELL = "sell" # 卖出

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"     # 待成交
    FILLED = "filled"       # 已成交
    CANCELLED = "cancelled" # 已撤销
    REJECTED = "rejected"   # 已拒绝（资金不足等）

@dataclass
class Order:
    """订单对象
    
    修正：
    - amount: 买入订单的委托金额（元）
    - quantity: 卖出订单的委托数量（张）
    - 成交后，amount和quantity应该满足：amount ≈ quantity × price
    """
    order_id: str          # 订单ID
    symbol: str             # 标的代码
    order_type: OrderType  # 订单类型
    price: float            # 成交价格
    amount: float           # 委托金额（元）- 买入订单使用
    quantity: int           # 成交数量（张）- 卖出订单使用
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = None
    filled_time: datetime = None
    
    def __post_init__(self):
        if self.create_time is None:
            self.create_time = datetime.now()
    
    def __repr__(self) -> str:
        """返回订单的字符串表示（便于调试）"""
        return (
            f"Order(order_id={self.order_id}, symbol={self.symbol}, "
            f"type={self.order_type.value}, price={self.price:.2f}, "
            f"quantity={self.quantity}, amount={self.amount:.2f}, "
            f"status={self.status.value})"
        )
    
    @classmethod
    def create_buy_order(
        cls,
        order_id: str,
        symbol: str,
        price: float,
        amount: float,
        quantity: int,
        status: OrderStatus = OrderStatus.FILLED
    ) -> 'Order':
        """
        创建买入订单（工厂方法）
        
        Args:
            order_id: 订单ID
            symbol: 标的代码
            price: 成交价格
            amount: 委托金额（元）
            quantity: 实际成交数量（张）
            status: 订单状态
            
        Returns:
            Order: 订单对象
        """
        # 数据一致性检查
        expected_amount = price * quantity
        if abs(amount - expected_amount) > 0.01:
            # 如果不一致，使用实际成交数据
            amount = expected_amount
        
        return cls(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.BUY,
            price=price,
            amount=amount,
            quantity=quantity,
            status=status
        )
    
    @classmethod
    def create_sell_order(
        cls,
        order_id: str,
        symbol: str,
        price: float,
        quantity: int,
        status: OrderStatus = OrderStatus.FILLED
    ) -> 'Order':
        """
        创建卖出订单（工厂方法）
        
        Args:
            order_id: 订单ID
            symbol: 标的代码
            price: 成交价格
            quantity: 成交数量（张）
            status: 订单状态
            
        Returns:
            Order: 订单对象
        """
        amount = price * quantity
        
        return cls(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.SELL,
            price=price,
            amount=amount,
            quantity=quantity,
            status=status
        )

