# 这是一个实盘 Executor 的伪代码示例
import logging
import time
import requests

API_URL = "http://127.0.0.1:48000/api"
class RealTradeExecutor:
    def __init__(self, account_id: str, mini_qmt_path: str):
        self.account_id = account_id
        # 连接到 Windows 上运行的 MiniQMT 软件
        # session_id 是一个随机数
        self.xt_trader = xt_trader.XtQuantTrader(path=mini_qmt_path, session_id=123456)
        
        # 启动连接
        self.xt_trader.start()
        
        # 建立连接
        connect_result = self.xt_trader.connect()
        if connect_result == 0:
            print("✅ 实盘交易终端连接成功！")
        
        # 初始化账户对象
        self.acc = StockAccount(account_id)

    def buy(self, symbol: str, price: float, quantity: int):
        """发送真实买入指令"""
        print(f"🚀 发送实盘买单: {symbol} 价格:{price} 数量:{quantity}")
        
        # QMT 的代码格式通常是 '123456.SZ' 或 '113001.SH'
        stock_code = self._format_code(symbol)
        
        # 异步下单接口
        order_id = self.xt_trader.order_stock_async(
            self.acc,
            stock_code,
            xt_trader.order_type.STOCK_BUY, # 买入
            quantity,
            xt_trader.price_type.FIX_PRICE, # 限价单
            price,
            strategy_name='double_low_strategy',
            order_remark='API下单'
        )
        return order_id

    def sell(self, symbol: str, price: float, quantity: int):
        """发送真实卖出指令"""
        # ... 逻辑同上，只是类型改为 STOCK_SELL ...
        pass

    def _format_code(self, code):
        """将 123456 转为 123456.SZ"""
        if code.startswith('11'): return f"{code}.SH"
        return f"{code}.SZ"
