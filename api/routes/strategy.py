"""
策略相关接口
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from api.schemas import StrategyConfig, StrategyResult, BondCandidate
from api.controller import StrategyController

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy", tags=["策略"])
controller = StrategyController()


@router.post("/run", response_model=StrategyResult, summary="运行双低策略")
async def run_strategy(config: StrategyConfig) -> StrategyResult:
    """
    运行双低策略，筛选优质转债
    
    - **max_price**: 最大价格限制（元）
    - **max_premium**: 最大溢价率限制（%）
    - **min_amount**: 最小剩余规模（亿元）
    - **max_amount**: 最大剩余规模（亿元）
    - **min_rating**: 最低评级
    - **top_n**: 选择前N只
    """
    try:
        logger.info(f"收到策略运行请求: {config}")
        result = controller.run_strategy(config)
        return result
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"策略执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates", response_model=List[BondCandidate], summary="获取候选转债")
async def get_candidates(
    max_price: float = 130.0,
    max_premium: float = 30.0,
    top_n: int = 10
) -> List[BondCandidate]:
    """
    获取候选转债列表（简化版）
    
    - **max_price**: 最大价格限制
    - **max_premium**: 最大溢价率限制
    - **top_n**: 返回数量
    """
    try:
        config = StrategyConfig(
            max_price=max_price,
            max_premium=max_premium,
            top_n=top_n
        )
        result = controller.run_strategy(config)
        return result.candidates
    except Exception as e:
        logger.error(f"获取候选转债失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

