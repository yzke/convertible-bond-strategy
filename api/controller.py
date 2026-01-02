"""
业务控制器 (Final API Version)
连接API和Core层，处理业务逻辑，维持内存状态

修复内容：
1. ✅ [严重] BacktestController 切换为 HistoricalDataProvider
2. ✅ [策略] 统一使用经典双低公式 (Price + Premium)
3. ✅ [架构] PortfolioController 实现单例模式 (内存持久化)
4. ✅ [规范] 完善类型注解和异常处理
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

# Core Modules
from trading import Portfolio, TradeExecutor
from data.real_data_provider import RealDataProvider, COLUMN_MAPPING, get_column_name
from data.historical_data_provider import HistoricalDataProvider # 必须导入历史数据源

# API Schemas
from api.schemas import (
    StrategyConfig, BondCandidate, StrategyResult,
    PortfolioSummary, Position, TradeRecord,
    BacktestConfig, PerformanceMetrics, BacktestResult
)

# 配置日志
logger = logging.getLogger(__name__)

# ============================================================================
# 全局状态 (模拟数据库)
# ============================================================================
# 用于在API运行期间保存持仓状态
GLOBAL_PORTFOLIO = None 

# ============================================================================
# 工具函数
# ============================================================================

def validate_rating(rating: Optional[str], min_rating: str) -> bool:
    """验证单个评级是否符合要求"""
    if not rating or pd.isna(rating):
        return False
    
    rating_order = ['C', 'CC', 'CCC', 'B-', 'B', 'B+', 'BB-', 'BB', 'BB+',
                    'BBB-', 'BBB', 'BBB+', 'A-', 'A', 'A+', 'AA-', 'AA', 'AA+', 'AAA']
    try:
        # 获取索引，索引越大评级越高
        rating_index = rating_order.index(rating)
        min_index = rating_order.index(min_rating)
        return rating_index >= min_index
    except (ValueError, AttributeError):
        return False

def calculate_dual_low_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算双低得分 (经典版: 价格 + 溢价率)
    保持与实盘脚本逻辑一致
    """
    if df.empty:
        return df

    # 优先使用数据源自带列
    src_col = get_column_name(df, COLUMN_MAPPING['双低'])
    if src_col:
        df['dual_low_score'] = df[src_col]
    else:
        # 经典公式
        df['dual_low_score'] = df['price'] + df['premium_rate']
    
    return df

# ============================================================================
# 策略控制器
# ============================================================================

class StrategyController:
    """策略控制器"""
    
    def __init__(self):
        self.data_provider = RealDataProvider()
    
    def run_strategy(self, config: StrategyConfig) -> StrategyResult:
        logger.info(f"执行策略筛选: P<{config.max_price}, O<{config.max_premium}")
        
        try:
            # 1. 获取数据
            df = self.data_provider.fetch_convertible_bonds()
            if df.empty:
                logger.warning("未能获取到实时行情")
                return StrategyResult(candidates=[], total_count=0)
            
            # 2. 基础筛选
            condition = (
                (df['price'] <= config.max_price) &
                (df['premium_rate'] <= config.max_premium) &
                (df['remain_amount'] >= config.min_amount) &
                (df['remain_amount'] <= config.max_amount)
            )
            
            # 3. 评级筛选
            if 'rating' in df.columns:
                # 预先过滤掉空评级，避免 validate_rating 报错
                rating_mask = df['rating'].apply(lambda r: validate_rating(str(r), config.min_rating))
                condition &= rating_mask
            
            filtered = df[condition].copy()
            
            # 4. 计算得分 & 排序
            filtered = calculate_dual_low_score(filtered)
            
            if filtered.empty:
                return StrategyResult(candidates=[], total_count=0)

            # 取 Top N
            selected = filtered.nsmallest(config.top_n, 'dual_low_score')
            
            # 5. 格式化输出
            candidates = []
            for _, row in selected.iterrows():
                candidates.append(BondCandidate(
                    code=str(row['code']),
                    name=str(row['name']),
                    price=float(row['price']),
                    premium_rate=float(row['premium_rate']),
                    remain_amount=float(row['remain_amount']),
                    rating=str(row['rating']) if 'rating' in row and pd.notna(row['rating']) else None,
                    dual_low_score=float(row['dual_low_score'])
                ))
            
            return StrategyResult(
                candidates=candidates,
                total_count=len(candidates)
            )
        
        except Exception as e:
            logger.error(f"策略执行异常: {e}", exc_info=True)
            raise

# ============================================================================
# 投资组合控制器 (内存持久化版)
# ============================================================================

class PortfolioController:
    """投资组合控制器 (Singleton模式)"""
    
    def __init__(self):
        # 尝试连接全局状态
        global GLOBAL_PORTFOLIO
        if GLOBAL_PORTFOLIO is None:
            # 默认初始化一个空组合，等待 execute 初始化
            GLOBAL_PORTFOLIO = Portfolio(initial_cash=100000.0)
        
        self.portfolio = GLOBAL_PORTFOLIO
        # Executor 必须绑定到当前的 portfolio 实例
        self.executor = TradeExecutor(portfolio=self.portfolio, is_backtest=False) # 默认为实盘模式
    
    def execute_trade(self, candidates: List[BondCandidate], request_data: Dict[str, Any]) -> PortfolioSummary:
        """执行交易并更新全局状态"""
        global GLOBAL_PORTFOLIO
        
        # 如果是首次请求或强制重置，可以重新初始化资金
        # 这里为了演示，我们假设如果资金还是默认值且无持仓，就允许重置资金
        req_initial_cash = request_data.get('initial_cash', 100000.0)
        if self.portfolio.cash == self.portfolio.initial_cash and not self.portfolio.positions:
             self.portfolio.initial_cash = req_initial_cash
             self.portfolio.cash = req_initial_cash

        # 更新回测模式标志
        self.executor.is_backtest = request_data.get('is_backtest', True)
        
        # 转换为 DataFrame 供 executor 使用
        df_data = [{
            'code': c.code, 
            'price': c.price, 
            'premium_rate': c.premium_rate
        } for c in candidates]
        target_df = pd.DataFrame(df_data)
        
        # 执行交易
        cash_per_trade = request_data.get('cash_per_trade', 10000.0)
        self.executor.execute_strategy(target_df, cash_per_trade)
        
        # 返回汇总
        return self.get_summary()

    def get_summary(self) -> PortfolioSummary:
        """获取当前持仓汇总"""
        summary_df = self.portfolio.get_summary()
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
            
        total_asset = self.portfolio.get_total_asset()
        total_profit = total_asset - self.portfolio.initial_cash
        profit_rate = (total_profit / self.portfolio.initial_cash * 100) if self.portfolio.initial_cash > 0 else 0
        
        return PortfolioSummary(
            positions=positions,
            cash=float(self.portfolio.cash),
            market_value=float(total_asset - self.portfolio.cash),
            total_asset=float(total_asset),
            total_profit=float(total_profit),
            profit_rate=float(profit_rate),
            initial_cash=float(self.portfolio.initial_cash),
            position_count=len(positions)
        )

    def get_trade_history(self) -> List[TradeRecord]:
        history_df = self.portfolio.get_trade_history()
        records = []
        for _, row in history_df.iterrows():
            records.append(TradeRecord(
                symbol=row['symbol'],
                action=row['action'],
                quantity=int(row['quantity']),
                price=float(row['price']),
                amount=float(row['amount']),
                commission=float(row['commission']),
                # 如果 trade_history 里有 time 字段
                trade_time=datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S") if 'time' in row else None
            ))
        return records

# ============================================================================
# 回测控制器
# ============================================================================

class BacktestController:
    """回测控制器"""
    
    def __init__(self):
        # ⚠️ 关键修复：回测必须使用 HistoricalDataProvider
        # 使用随机种子确保结果可复现
        self.data_provider = HistoricalDataProvider(random_seed=42)
        self.rng = np.random.RandomState(42)
    
    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        logger.info(f"启动回测引擎: {config.start_date} -> {config.end_date}")
        
        # 1. 独立的回测环境 (不污染全局 GLOBAL_PORTFOLIO)
        portfolio = Portfolio(initial_cash=config.initial_cash)
        executor = TradeExecutor(portfolio=portfolio, is_backtest=True)
        
        # 2. 获取历史数据 (模拟)
        raw_data = self.data_provider.fetch_historical_data(
            start_date=config.start_date,
            end_date=config.end_date
        )
        
        if raw_data.empty:
            raise ValueError("无法获取历史数据")

        # 按日期分组处理
        daily_groups = raw_data.groupby('date')
        
        daily_assets = []
        daily_returns = []
        dates_processed = []
        
        # 3. 时间步进循环
        for i, (date_val, daily_df) in enumerate(daily_groups):
            current_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
            dates_processed.append(current_date)
            
            # --- 模拟行情波动 ---
            # 这里的逻辑与 run_backtest_historical.py 保持一致
            # 在 HistoricalDataProvider 基础数据上叠加当天的随机波动
            daily_df = daily_df.copy()
            noise = self.rng.randn(len(daily_df)) * 0.01 
            daily_df['price'] = daily_df['price'] * (1 + noise)
            
            # --- 策略筛选 ---
            # 1. 基础筛选
            condition = (
                (daily_df['price'] <= config.max_price) &
                (daily_df['premium_rate'] <= config.max_premium) &
                (daily_df['remain_amount'] >= config.min_amount) &
                (daily_df['remain_amount'] <= config.max_amount)
            )
            filtered = daily_df[condition].copy()
            
            if not filtered.empty:
                # 2. 计算得分 (经典公式)
                filtered['dual_low_score'] = filtered['price'] + filtered['premium_rate']
                # 3. 排序
                selected = filtered.nsmallest(config.top_n, 'dual_low_score')
                
                # --- 更新持仓市值 ---
                for _, row in selected.iterrows():
                    portfolio.update_market_price(row['code'], row['price'])
                
                # --- 调仓执行 ---
                if i % config.rebalance_days == 0:
                    executor.execute_strategy(selected, config.cash_per_trade)
            
            # --- 记录当日资产 ---
            total_asset = portfolio.get_total_asset()
            daily_assets.append(total_asset)
            
            if len(daily_assets) > 1:
                ret = (total_asset - daily_assets[-2]) / daily_assets[-2]
                daily_returns.append(ret)

        # 4. 计算业绩指标
        total_return = (daily_assets[-1] / daily_assets[0]) - 1 if daily_assets else 0
        
        ann_ret = 0.0
        ann_vol = 0.0
        sharpe = 0.0
        max_dd = 0.0
        win_rate = 0.0
        
        if len(daily_returns) > 0:
            ann_ret = (1 + total_return) ** (252 / len(daily_returns)) - 1
            ann_vol = np.std(daily_returns) * np.sqrt(252)
            sharpe = (ann_ret - 0.03) / ann_vol if ann_vol > 0 else 0
            win_rate = sum(r > 0 for r in daily_returns) / len(daily_returns)
            
            # 最大回撤
            cum_ret = np.cumprod(1 + np.array(daily_returns))
            peak = np.maximum.accumulate(cum_ret)
            dd = (cum_ret - peak) / peak
            max_dd = np.min(dd)

        # 5. 构建结果
        # 这里只转换最后一次持仓作为展示
        summary_df = portfolio.get_summary()
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

        return BacktestResult(
            performance=PerformanceMetrics(
                total_return=total_return,
                annualized_return=ann_ret,
                annualized_volatility=ann_vol,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                win_rate=win_rate
            ),
            portfolio=PortfolioSummary(
                positions=positions,
                cash=float(portfolio.cash),
                market_value=float(portfolio.get_total_asset() - portfolio.cash),
                total_asset=float(portfolio.get_total_asset()),
                total_profit=float(portfolio.get_total_asset() - config.initial_cash),
                profit_rate=float(total_return * 100),
                initial_cash=float(config.initial_cash),
                position_count=len(positions)
            ),
            trade_history=[], # 简化返回，避免数据量过大
            start_date=config.start_date,
            end_date=config.end_date,
            trading_days=len(dates_processed)
        )
