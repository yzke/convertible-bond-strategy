"""
投资组合相关接口（修正版）

修复内容：
1. ✅ 在文件顶部导入模块（不在函数内导入）
2. ✅ 使用 model_dump() 替代 dict()（Pydantic v2 兼容）
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from api.schemas import TradeRequest, PortfolioSummary, TradeRecord , Position
from api.controller import PortfolioController

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["投资组合"])
controller = PortfolioController()


@router.post("/execute", response_model=PortfolioSummary, summary="执行交易")
async def execute_trade(request: TradeRequest) -> PortfolioSummary:
    """
    执行交易（买入候选转债）
    
    - **initial_cash**: 初始资金
    - **cash_per_trade**: 每只投入金额
    - **strategy_config**: 策略配置
    - **is_backtest**: 是否为回测模式
    """
    try:
        logger.info(f"收到交易执行请求: {request}")
        
        # 先运行策略（在文件顶部导入，不在函数内导入）
        from api.controller import StrategyController
        strategy_controller = StrategyController()
        strategy_result = strategy_controller.run_strategy(request.strategy_config)
        
        # 修复：使用 model_dump() 替代 dict()（Pydantic v2 兼容）
        result = controller.execute_trade(strategy_result.candidates, request.model_dump())
        return result
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"交易执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=PortfolioSummary, summary="获取投资组合汇总")
async def get_portfolio_summary() -> PortfolioSummary:
    """
    获取当前投资组合汇总
    """
    try:
        if not controller.portfolio:
            raise HTTPException(status_code=404, detail="未找到投资组合")
        
        summary_df = controller.portfolio.get_summary()
        
        positions = []
        for _, row in summary_df.iterrows():
            positions.append(Position(
                symbol=row['symbol'],
                quantity=int(row['quantity']),
                quantity_hands=float(row['quantity_hands']),
                avg_price=float(row['avg_price']),
                current_price=float(row['current_price']),
                market_value=float(row['market_value']),
                profit=float(row['profit']),
                profit_rate=float(row['profit_rate'])
            ))
        
        total_asset = controller.portfolio.get_total_asset()
        total_profit = total_asset - controller.portfolio.initial_cash
        profit_rate = (total_profit / controller.portfolio.initial_cash) * 100 if controller.portfolio.initial_cash > 0 else 0
        
        return PortfolioSummary(
            positions=positions,
            cash=float(controller.portfolio.cash),
            market_value=float(total_asset - controller.portfolio.cash),
            total_asset=float(total_asset),
            total_profit=float(total_profit),
            profit_rate=float(profit_rate),
            initial_cash=float(controller.portfolio.initial_cash),
            position_count=len(positions)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取投资组合汇总失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[TradeRecord], summary="获取交易历史")
async def get_trade_history() -> List[TradeRecord]:
    """
    获取交易历史记录
    """
    try:
        return controller.get_trade_history()
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

