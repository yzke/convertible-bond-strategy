"""
API数据模型定义
使用Pydantic进行数据验证和序列化
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# 策略相关模型
# ============================================================================

class OrderType(str, Enum):
    """订单类型"""
    BUY = "buy"
    SELL = "sell"


class StrategyConfig(BaseModel):
    """策略配置"""
    max_price: float = Field(130.0, gt=0, description="最大价格限制")
    max_premium: float = Field(30.0, ge=0, description="最大溢价率限制（%）")
    min_amount: float = Field(0.5, gt=0, description="最小剩余规模（亿元）")
    max_amount: float = Field(10.0, gt=0, description="最大剩余规模（亿元）")
    min_rating: str = Field("A", description="最低评级")
    top_n: int = Field(10, gt=0, description="选择前N只")
    
    @validator('min_rating')
    def validate_rating(cls, v):
        """验证评级"""
        rating_order = ['C', 'CC', 'CCC', 'B-', 'B', 'B+', 'BB-', 'BB', 'BB+',
                        'BBB-', 'BBB', 'BBB+', 'A-', 'A', 'A+', 'AA-', 'AA', 'AA+', 'AAA']
        if v not in rating_order:
            raise ValueError(f"评级必须是以下之一: {', '.join(rating_order)}")
        return v


class BondCandidate(BaseModel):
    """候选转债"""
    code: str = Field(..., description="转债代码")
    name: str = Field(..., description="转债名称")
    price: float = Field(..., gt=0, description="转债价格")
    premium_rate: float = Field(..., description="溢价率（%）")
    remain_amount: float = Field(..., ge=0, description="剩余规模（亿元）")
    rating: Optional[str] = Field(None, description="评级")
    dual_low_score: float = Field(..., description="双低得分")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "123001",
                "name": "转债001",
                "price": 100.0,
                "premium_rate": 5.0,
                "remain_amount": 5.0,
                "rating": "AA",
                "dual_low_score": 50.0
            }
        }


class StrategyResult(BaseModel):
    """策略执行结果"""
    candidates: List[BondCandidate] = Field(..., description="候选转债列表")
    total_count: int = Field(..., description="总候选数")
    run_time: datetime = Field(default_factory=datetime.now, description="执行时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidates": [
                    {
                        "code": "123001",
                        "name": "转债001",
                        "price": 100.0,
                        "premium_rate": 5.0,
                        "remain_amount": 5.0,
                        "rating": "AA",
                        "dual_low_score": 50.0
                    }
                ],
                "total_count": 10
            }
        }


# ============================================================================
# 交易相关模型
# ============================================================================

class TradeRequest(BaseModel):
    """交易请求"""
    initial_cash: float = Field(100000.0, gt=0, description="初始资金")
    cash_per_trade: float = Field(10000.0, gt=0, description="每只投入金额")
    strategy_config: StrategyConfig = Field(default_factory=StrategyConfig, description="策略配置")
    is_backtest: bool = Field(True, description="是否为回测模式")
    
    @validator('cash_per_trade')
    def validate_cash_per_trade(cls, v, values):
        """验证每只投入金额不能超过初始资金"""
        if 'initial_cash' in values and v > values['initial_cash']:
            raise ValueError("每只投入金额不能超过初始资金")
        return v


class Position(BaseModel):
    """持仓信息"""
    symbol: str = Field(..., description="标的代码")
    quantity: int = Field(..., ge=0, description="持仓数量（张）")
    quantity_hands: float = Field(..., ge=0, description="持仓数量（手）")
    avg_price: float = Field(..., gt=0, description="平均成本价")
    current_price: float = Field(..., gt=0, description="当前价格")
    market_value: float = Field(..., ge=0, description="持仓市值")
    profit: float = Field(..., description="盈亏金额")
    profit_rate: float = Field(..., description="盈亏率（%）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "123001",
                "quantity": 100,
                "quantity_hands": 10,
                "avg_price": 100.0,
                "current_price": 105.0,
                "market_value": 10500.0,
                "profit": 500.0,
                "profit_rate": 5.0
            }
        }


class PortfolioSummary(BaseModel):
    """投资组合汇总"""
    positions: List[Position] = Field(..., description="持仓列表")
    cash: float = Field(..., ge=0, description="可用资金")
    market_value: float = Field(..., ge=0, description="持仓市值")
    total_asset: float = Field(..., ge=0, description="总资产")
    total_profit: float = Field(..., description="总盈亏")
    profit_rate: float = Field(..., description="总收益率（%）")
    initial_cash: float = Field(..., ge=0, description="初始资金")
    position_count: int = Field(..., ge=0, description="持仓数量")


class TradeRecord(BaseModel):
    """交易记录"""
    symbol: str = Field(..., description="标的代码")
    action: str = Field(..., description="交易方向（buy/sell）")
    quantity: int = Field(..., gt=0, description="交易数量（张）")
    price: float = Field(..., gt=0, description="交易价格")
    amount: float = Field(..., gt=0, description="交易金额")
    commission: float = Field(..., ge=0, description="手续费")
    trade_time: Optional[datetime] = Field(None, description="交易时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "123001",
                "action": "buy",
                "quantity": 100,
                "price": 100.0,
                "amount": 10000.0,
                "commission": 5.0
            }
        }


# ============================================================================
# 回测相关模型
# ============================================================================

class BacktestConfig(BaseModel):
    """回测配置"""
    start_date: str = Field(..., description="开始日期（YYYY-MM-DD）")
    end_date: str = Field(..., description="结束日期（YYYY-MM-DD）")
    initial_cash: float = Field(100000.0, gt=0, description="初始资金")
    top_n: int = Field(10, gt=0, description="选择前N只")
    cash_per_trade: float = Field(10000.0, gt=0, description="每只投入金额")
    max_price: float = Field(130.0, gt=0, description="最大价格限制")
    max_premium: float = Field(30.0, ge=0, description="最大溢价率限制（%）")
    min_amount: float = Field(0.5, gt=0, description="最小剩余规模（亿元）")
    max_amount: float = Field(10.0, gt=0, description="最大剩余规模（亿元）")
    rebalance_days: int = Field(5, gt=0, description="调仓周期（天）")
    random_seed: int = Field(42, description="随机种子")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v


class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    annualized_volatility: float = Field(..., description="年化波动率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    win_rate: float = Field(..., ge=0, le=1, description="胜率")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_return": 0.15,
                "annualized_return": 0.18,
                "annualized_volatility": 0.12,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.05,
                "win_rate": 0.6
            }
        }


class BacktestResult(BaseModel):
    """回测结果"""
    performance: PerformanceMetrics = Field(..., description="性能指标")
    portfolio: PortfolioSummary = Field(..., description="最终持仓")
    trade_history: List[TradeRecord] = Field(..., description="交易历史")
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    trading_days: int = Field(..., ge=0, description="交易日数")
    run_time: datetime = Field(default_factory=datetime.now, description="回测执行时间")


# ============================================================================
# 响应模型
# ============================================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")

