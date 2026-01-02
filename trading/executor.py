"""
交易执行器
负责根据策略结果执行交易

修正内容：
1. ✅ 适配 Portfolio.buy 的新返回值 (success, quantity, total_cost)
2. ✅ 使用工厂方法创建订单，确保数据一致性
3. ✅ 添加 is_backtest 参数，明确区分回测和实盘模式
4. ✅ 移除资金判断逻辑，直接尝试买入（推荐方案）
5. ✅ 缓冲金额可配置
6. ✅ 统一使用 logging 模块
7. ✅ 添加 execute_strategy 参数验证
8. ✅ 捕获 update_market_price 异常，避免单个失败影响整体
9. ✅ 添加类型注解
10. ✅ 添加辅助方法（get_orders, get_order_count, clear_orders）
11. ✅ 添加异常处理
"""
from typing import List
from trading.order import Order, OrderType, OrderStatus
from trading.portfolio import Portfolio
import pandas as pd
import logging

# 配置日志
logger = logging.getLogger(__name__)

class TradeExecutor:
    """交易执行器"""
    
    def __init__(
        self,
        portfolio: Portfolio,
        is_backtest: bool = True,
        cash_buffer: float = 100.0
    ):
        """
        初始化交易执行器
        
        Args:
            portfolio: 投资组合
            is_backtest: 是否为回测模式（True=回测，False=实盘）
            cash_buffer: 缓冲金额（元），用于判断资金是否足够
        """
        self.portfolio = portfolio
        self.is_backtest = is_backtest
        self.cash_buffer = cash_buffer
        self.orders = []
    
    def _get_sell_price(self, symbol: str) -> float:
        """
        获取卖出价格
        
        修正：
        - 回测模式：如果没有实时价，使用持仓成本价模拟
        - 实盘模式：必须获取实时价，否则抛出异常
        
        Args:
            symbol: 标的代码
            
        Returns:
            float: 卖出价格
            
        Raises:
            ValueError: 实盘模式下无法获取价格时抛出
        """
        current_price = self.portfolio.market_values.get(symbol, 0)
        
        if current_price == 0:
            if self.is_backtest:
                # 回测模式：使用持仓成本价模拟
                if symbol in self.portfolio.positions:
                    current_price = self.portfolio.positions[symbol]['avg_price']
                    logger.warning(
                        f"[回测模式] 无法获取 {symbol} 实时价，使用成本价 {current_price:.2f} 模拟卖出"
                    )
                else:
                    logger.error(f"无法获取 {symbol} 价格，且不在持仓中")
                    raise ValueError(f"无法获取 {symbol} 价格")
            else:
                # 实盘模式：必须获取实时价
                logger.error(f"[实盘模式] 无法获取 {symbol} 实时价，无法执行卖出")
                raise ValueError(f"[实盘模式] 无法获取 {symbol} 实时价")
        
        return current_price
    
    def _validate_execute_strategy_params(
        self,
        target_symbols: pd.DataFrame,
        cash_per_trade: float
    ) -> None:
        """
        验证 execute_strategy 方法的参数
        
        Args:
            target_symbols: 策略推荐的DataFrame
            cash_per_trade: 每只标的投入金额
            
        Raises:
            ValueError: 参数无效时抛出
        """
        # 验证 target_symbols
        if not isinstance(target_symbols, pd.DataFrame):
            raise ValueError("target_symbols 必须是 pandas.DataFrame")
        
        if target_symbols.empty:
            raise ValueError("target_symbols 不能为空")
        
        required_columns = ['code', 'price']
        for col in required_columns:
            if col not in target_symbols.columns:
                raise ValueError(f"target_symbols 必须包含列: {col}")
        
        # 验证 cash_per_trade
        if cash_per_trade <= 0:
            raise ValueError(f"cash_per_trade 必须大于0: {cash_per_trade}")
    
    def execute_strategy(self, target_symbols: pd.DataFrame, cash_per_trade: float) -> None:
        """
        执行策略调仓（轮动模式）
        
        修正逻辑：
        1. 卖出：不在目标名单中的持仓
        2. 买入：在目标名单中且未持有的
        
        Args:
            target_symbols: 策略推荐的DataFrame，必须包含 code, price
            cash_per_trade: 每只标的投入金额
        """
        try:
            # 参数验证
            self._validate_execute_strategy_params(target_symbols, cash_per_trade)
            
            logger.info("="*40)
            logger.info("开始执行轮动交易...")
            logger.info(f"模式: {'回测' if self.is_backtest else '实盘'}")
            logger.info("="*40)
            
            target_codes = target_symbols['code'].tolist()
            
            # --- 步骤 1: 卖出不在榜单的持仓 ---
            current_holdings = list(self.portfolio.positions.keys())
            
            for symbol in current_holdings:
                if symbol not in target_codes:
                    # 不在推荐名单中，清仓卖出
                    try:
                        current_price = self._get_sell_price(symbol)
                        quantity = self.portfolio.positions[symbol]['quantity']
                        
                        logger.info(f"轮动卖出: {symbol} (掉出排名)")
                        success = self.portfolio.sell(symbol, current_price, quantity)
                        
                        if success:
                            # 记录订单（使用工厂方法）
                            order = Order.create_sell_order(
                                order_id=f"ORD_{len(self.orders)}",
                                symbol=symbol,
                                price=current_price,
                                quantity=quantity,
                                status=OrderStatus.FILLED
                            )
                            self.orders.append(order)
                    
                    except ValueError as e:
                        logger.error(f"卖出 {symbol} 失败: {e}")
                        continue
            
            # --- 步骤 2: 买入新上榜的标的 ---
            for _, row in target_symbols.iterrows():
                symbol = row['code']
                price = row['price']
                
                # 修正：捕获 update_market_price 异常，避免单个失败影响整体
                try:
                    # 更新行情
                    self.portfolio.update_market_price(symbol, price)
                except ValueError as e:
                    logger.error(f"更新 {symbol} 行情失败: {e}，跳过")
                    continue
                
                # 检查是否已持有
                if symbol in self.portfolio.positions:
                    # 已持有，跳过
                    continue
                
                # 修正：移除资金判断逻辑，直接尝试买入（推荐方案）
                # Portfolio.buy 会处理资金不足的情况，并返回详细的错误信息
                success, quantity, total_cost = self.portfolio.buy(symbol, price, cash_per_trade)
                
                if success:
                    # 记录订单（使用工厂方法）
                    order = Order.create_buy_order(
                        order_id=f"ORD_{len(self.orders)}",
                        symbol=symbol,
                        price=price,
                        amount=quantity * price,  # 实际成交金额
                        quantity=quantity,        # 实际成交数量
                        status=OrderStatus.FILLED
                    )
                    self.orders.append(order)
            
            logger.info("="*40)
            logger.info(f"交易执行完毕")
            logger.info(f"剩余现金: {self.portfolio.cash:.2f} 元")
            logger.info(f"总资产: {self.portfolio.get_total_asset():.2f} 元")
            logger.info("="*40)
        
        except Exception as e:
            logger.error(f"执行策略时发生错误: {e}")
            raise
    
    # 新增辅助方法
    def get_orders(self) -> List[Order]:
        """获取所有订单"""
        return self.orders
    
    def get_order_count(self) -> int:
        """获取订单数量"""
        return len(self.orders)
    
    def clear_orders(self) -> None:
        """清空订单记录"""
        self.orders = []

