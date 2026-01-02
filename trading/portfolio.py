"""
投资组合管理
负责管理资金、持仓和交易

修正内容：
1. ✅ 平均成本计算不包含手续费
2. ✅ 修正 profit_rate 的除零风险
3. ✅ 添加输入参数验证（symbol, price, amount, quantity）
4. ✅ 优化手续费计算逻辑（避免重复计算）
5. ✅ buy 方法返回 (success, quantity, total_cost) 元组
6. ✅ update_market_price 参数验证改为 price <= 0
7. ✅ 添加 _validate_symbol 方法（修正：允许5位或6位代码）
8. ✅ 添加辅助方法（get_position, get_cash, get_position_count）
9. ✅ 添加 __repr__ 方法
"""
from typing import Dict, Optional, Tuple
import pandas as pd
import logging

# 配置日志
logger = logging.getLogger(__name__)

class Portfolio:
    """模拟投资组合"""
    
    def __init__(
        self,
        initial_cash: float = 100000.0,
        buy_commission_rate: float = 0.0003,  # 买入佣金率（万三）
        sell_commission_rate: float = 0.0003,  # 卖出佣金率（万三）
        stamp_duty_rate: float = 0.001,       # 印花税率（千一，仅卖出）
        min_commission: float = 5.0           # 最低佣金（5元）
    ):
        """
        初始化投资组合
        
        Args:
            initial_cash: 初始资金，默认10万
            buy_commission_rate: 买入佣金率，默认0.03%
            sell_commission_rate: 卖出佣金率，默认0.03%
            stamp_duty_rate: 印花税率，默认0.1%（仅卖出）
            min_commission: 最低佣金，默认5元
        """
        # 参数验证
        if initial_cash <= 0:
            raise ValueError("初始资金必须大于0")
        if not (0 <= buy_commission_rate <= 1):
            raise ValueError("买入佣金率必须在0到1之间")
        if not (0 <= sell_commission_rate <= 1):
            raise ValueError("卖出佣金率必须在0到1之间")
        if not (0 <= stamp_duty_rate <= 1):
            raise ValueError("印花税率必须在0到1之间")
        if min_commission < 0:
            raise ValueError("最低佣金不能为负数")
        
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # {symbol: {'quantity': 100, 'avg_price': 105.0}}
        self.market_values = {} # {symbol: current_price}
        
        # 记录历史交易日志
        self.trade_history = []
        
        # 手续费参数
        self.buy_commission_rate = buy_commission_rate
        self.sell_commission_rate = sell_commission_rate
        self.stamp_duty_rate = stamp_duty_rate
        self.min_commission = min_commission
    
    def __repr__(self) -> str:
        """返回投资组合的字符串表示（便于调试）"""
        return (
            f"Portfolio(cash={self.cash:.2f}, "
            f"positions={len(self.positions)}, "
            f"total_asset={self.get_total_asset():.2f})"
        )
    
    def _validate_symbol(self, symbol: str) -> None:
        """
        验证标的代码是否有效
        
        修正：允许5位或6位代码（可转债代码通常是6位，如123001）
        
        Args:
            symbol: 标的代码
            
        Raises:
            ValueError: 标的代码无效时抛出
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"标的代码必须是非空字符串: {symbol}")
        if not symbol.isdigit():
            raise ValueError(f"标的代码必须只包含数字: {symbol}")
        if len(symbol) not in [5, 6]:
            logger.warning(f"标的代码格式可能不正确（应为5或6位）: {symbol}")
    
    def update_market_price(self, symbol: str, price: float) -> None:
        """
        更新某标的最新市价
        
        修正：
        - 添加 symbol 参数验证
        - 修正价格验证为 price <= 0
        
        Args:
            symbol: 标的代码
            price: 最新市价
            
        Raises:
            ValueError: 参数无效时抛出
        """
        self._validate_symbol(symbol)
        if price <= 0:
            raise ValueError(f"价格必须大于0: {price}")
        self.market_values[symbol] = price
    
    def _calculate_buy_commission(self, amount: float) -> float:
        """计算买入手续费"""
        commission = amount * self.buy_commission_rate
        return max(commission, self.min_commission)
    
    def _calculate_sell_commission(self, amount: float) -> float:
        """计算卖出手续费（佣金 + 印花税）"""
        commission = amount * self.sell_commission_rate
        stamp_duty = amount * self.stamp_duty_rate
        return max(commission, self.min_commission) + stamp_duty
    
    def buy(self, symbol: str, price: float, amount: float) -> Tuple[bool, int, float]:
        """
        买入（按金额买入）
        
        修正：
        1. ✅ 添加 symbol 参数验证
        2. ✅ 平均成本计算不包含手续费
        3. ✅ 优化手续费计算逻辑（避免重复计算）
        4. ✅ 返回 (success, quantity, total_cost) 元组
        
        Args:
            symbol: 标的代码
            price: 价格
            amount: 投入金额（元）
            
        Returns:
            Tuple[bool, int, float]: (是否成功, 实际买入数量, 总成本)
        """
        # 参数验证
        self._validate_symbol(symbol)
        if price <= 0:
            logger.error(f"价格必须大于0: {price}")
            return False, 0, 0.0
        if amount <= 0:
            logger.error(f"金额必须大于0: {amount}")
            return False, 0, 0.0
        
        # 计算最大可买数量（张）
        max_quantity = int(amount / price)
        
        # 修正：可转债必须是10的倍数（1手=10张）
        quantity = (max_quantity // 10) * 10
        
        if quantity == 0:
            logger.error(
                f"金额不足买入1手（10张），需要约 {price * 10:.2f} 元"
            )
            return False, 0, 0.0
        
        # 实际成本（按实际购买数量计算）
        actual_cost = quantity * price
        actual_commission = self._calculate_buy_commission(actual_cost)
        total_actual_cost = actual_cost + actual_commission
        
        # 检查资金是否足够
        if total_actual_cost > self.cash:
            logger.error(
                f"资金不足！需要 {total_actual_cost:.2f}（含手续费 {actual_commission:.2f}），可用 {self.cash:.2f}"
            )
            return False, 0, 0.0
        
        # 扣款
        self.cash -= total_actual_cost
        
        # 更新持仓
        if symbol not in self.positions:
            self.positions[symbol] = {'quantity': 0, 'avg_price': 0.0}
        
        pos = self.positions[symbol]
        
        # 修正：重新计算平均成本（不包含手续费）
        total_cost_old = pos['quantity'] * pos['avg_price']
        total_quantity = pos['quantity'] + quantity
        
        if total_quantity > 0:
            # 平均成本只计算资产的实际购买价格，不包含手续费
            pos['avg_price'] = (total_cost_old + actual_cost) / total_quantity
        
        pos['quantity'] = total_quantity
        
        self._record_trade(symbol, 'buy', quantity, price, actual_commission)
        logger.info(
            f"买入成功: {symbol} 数量:{quantity}张 ({quantity/10:.0f}手) "
            f"价格:{price:.2f} 手续费:{actual_commission:.2f} 成本价:{pos['avg_price']:.2f} "
            f"总成本:{total_actual_cost:.2f}"
        )
        return True, quantity, total_actual_cost
    
    def sell(self, symbol: str, price: float, quantity: int) -> bool:
        """
        卖出
        
        修正：
        1. ✅ 添加 symbol 参数验证
        
        Args:
            symbol: 标的代码
            price: 价格
            quantity: 卖出数量（张）
            
        Returns:
            bool: 是否卖出成功
        """
        # 参数验证
        self._validate_symbol(symbol)
        if price <= 0:
            logger.error(f"价格必须大于0: {price}")
            return False
        if quantity <= 0:
            logger.error(f"数量必须大于0: {quantity}")
            return False
        if quantity % 10 != 0:
            logger.error(f"卖出数量必须是10的倍数: {quantity}")
            return False
        
        if symbol not in self.positions or self.positions[symbol]['quantity'] < quantity:
            logger.error(
                f"持仓不足！持有 {self.positions.get(symbol, {}).get('quantity', 0)}，卖出 {quantity}"
            )
            return False
        
        # 执行卖出
        self.positions[symbol]['quantity'] -= quantity
        income = quantity * price
        
        # 计算手续费
        commission = self._calculate_sell_commission(income)
        net_income = income - commission
        
        self.cash += net_income
        
        # 如果持仓为0，移除
        if self.positions[symbol]['quantity'] == 0:
            del self.positions[symbol]
        
        self._record_trade(symbol, 'sell', quantity, price, commission)
        logger.info(
            f"卖出成功: {symbol} 数量:{quantity}张 ({quantity/10:.0f}手) "
            f"价格:{price:.2f} 手续费:{commission:.2f} 净收入:{net_income:.2f}"
        )
        return True
    
    def get_total_asset(self) -> float:
        """获取总资产 (现金 + 持仓市值)"""
        market_value = 0.0
        for symbol, pos in self.positions.items():
            price = self.market_values.get(symbol, pos['avg_price'])
            market_value += pos['quantity'] * price
        return self.cash + market_value
    
    def _record_trade(self, symbol: str, action: str, quantity: int, price: float, commission: float = 0.0):
        """记录交易日志"""
        self.trade_history.append({
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price,
            'commission': commission
        })
    
    def get_summary(self) -> pd.DataFrame:
        """获取持仓汇总"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for symbol, pos in self.positions.items():
            price = self.market_values.get(symbol, pos['avg_price'])
            market_val = pos['quantity'] * price
            profit = market_val - (pos['quantity'] * pos['avg_price'])
            
            # 修正：添加 avg_price > 0 的检查，避免除零错误
            total_cost = pos['quantity'] * pos['avg_price']
            profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0.0
            
            data.append({
                'symbol': symbol,
                'quantity': pos['quantity'],
                'quantity_hands': pos['quantity'] / 10,  # 手数
                'avg_price': pos['avg_price'],
                'current_price': price,
                'market_value': market_val,
                'profit': profit,
                'profit_rate': profit_rate
            })
        
        return pd.DataFrame(data)
    
    def get_trade_history(self) -> pd.DataFrame:
        """获取交易历史"""
        return pd.DataFrame(self.trade_history)
    
    # 新增辅助方法
    def get_position(self, symbol: str) -> Optional[Dict]:
        """获取某个标的的持仓信息"""
        return self.positions.get(symbol)
    
    def get_cash(self) -> float:
        """获取可用资金"""
        return self.cash
    
    def get_position_count(self) -> int:
        """获取持仓数量"""
        return len(self.positions)

