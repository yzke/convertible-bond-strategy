"""
回测相关接口（修正版）

修复内容：
1. ✅ 删除重复的路由定义
"""
from fastapi import APIRouter, HTTPException
import logging

from api.schemas import BacktestConfig, BacktestResult
from api.controller import BacktestController

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["回测"])
controller = BacktestController()


@router.post("/run", response_model=BacktestResult, summary="运行历史回测")
async def run_backtest(config: BacktestConfig) -> BacktestResult:
    """
    运行历史回测
    
    - **start_date**: 开始日期（YYYY-MM-DD）
    - **end_date**: 结束日期（YYYY-MM-DD）
    - **initial_cash**: 初始资金
    - **top_n**: 选择前N只
    - **cash_per_trade**: 每只投入金额
    - **max_price**: 最大价格限制
    - **max_premium**: 最大溢价率限制
    - **min_amount**: 最小剩余规模
    - **max_amount**: 最大剩余规模
    - **rebalance_days**: 调仓周期（天）
    - **random_seed**: 随机种子
    """
    try:
        logger.info(f"收到回测请求: {config}")
        result = controller.run_backtest(config)
        return result
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"回测执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

