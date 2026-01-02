"""
FastAPI应用入口（修正版）

修复内容：
1. ✅ CORS配置支持环境变量
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from api.routes import strategy, portfolio, backtest
from api.schemas import HealthResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="可转债双低策略API",
    description="可转债双低策略量化交易系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 修复：CORS配置支持环境变量
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(strategy.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)


# ============================================================================
# 基础接口
# ============================================================================

@app.get("/", response_model=HealthResponse, summary="健康检查")
async def root() -> HealthResponse:
    """
    健康检查接口
    
    返回服务状态信息
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health() -> HealthResponse:
    """
    健康检查接口
    
    返回服务状态信息
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


# ============================================================================
# 启动事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("="*60)
    logger.info("可转债双低策略API启动")
    logger.info("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("="*60)
    logger.info("可转债双低策略API关闭")
    logger.info("="*60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

