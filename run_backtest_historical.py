"""
可转债双低策略历史回测脚本

修正内容：
1. ✅ 添加 numpy 导入
2. ✅ 修复使用错误的数据提供者
3. ✅ 添加随机种子设置
4. ✅ 添加参数验证
5. ✅ 添加异常处理
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# 导入交易模块
from trading import Portfolio, TradeExecutor, Order
from data.real_data_provider import RealDataProvider
from data.historical_data_provider import HistoricalDataProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest_historical.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 参数验证模块
# ============================================================================

def validate_backtest_params(
    initial_cash: float,
    top_n: int,
    cash_per_trade: float,
    max_price: float,
    max_premium: float,
    min_amount: float,
    max_amount: float,
    rebalance_days: int = 5
) -> None:
    """
    验证回测参数
    
    Args:
        initial_cash: 初始资金
        top_n: 选择前N只
        cash_per_trade: 每只标的投入金额
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_amount: 最小剩余规模（亿元）
        max_amount: 最大剩余规模（亿元）
        rebalance_days: 调仓周期（天）
        
    Raises:
        ValueError: 参数无效时抛出
    """
    if initial_cash <= 0:
        raise ValueError("初始资金必须大于0")
    if top_n <= 0:
        raise ValueError("top_n必须大于0")
    if cash_per_trade <= 0:
        raise ValueError("每只投入金额必须大于0")
    if cash_per_trade > initial_cash:
        raise ValueError("每只投入金额不能超过初始资金")
    if max_price <= 0:
        raise ValueError("最大价格必须大于0")
    if max_premium < 0:
        raise ValueError("最大溢价率不能为负")
    if min_amount <= 0:
        raise ValueError("最小规模必须大于0")
    if max_amount <= 0:
        raise ValueError("最大规模必须大于0")
    if min_amount >= max_amount:
        raise ValueError("最小规模必须小于最大规模")
    if rebalance_days <= 0:
        raise ValueError("调仓周期必须大于0")


# ============================================================================
# 策略模块（复用）
# ============================================================================

def calculate_dual_low_score(
    df: pd.DataFrame,
    price_weight: float = 0.5,
    premium_weight: float = 0.5
) -> pd.DataFrame:
    """
    计算双低得分（价格 + 溢价率）
    
    Args:
        df: 可转债数据
        price_weight: 价格权重
        premium_weight: 溢价率权重
        
    Returns:
        pd.DataFrame: 添加了 dual_low_score 列的数据
    """
    # 标准化价格（0-100）
    df['price_norm'] = (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min()) * 100
    
    # 标准化溢价率（0-100）
    df['premium_norm'] = (df['premium_rate'] - df['premium_rate'].min()) / (df['premium_rate'].max() - df['premium_rate'].min()) * 100
    
    # 计算双低得分（越低越好）
    df['dual_low_score'] = df['price_norm'] * price_weight + df['premium_norm'] * premium_weight
    
    return df


def select_top_bonds(
    df: pd.DataFrame,
    top_n: int = 10,
    max_price: float = 130.0,
    max_premium: float = 30.0,
    min_amount: float = 0.5,
    max_amount: float = 10.0
) -> pd.DataFrame:
    """
    筛选双低策略标的
    
    Args:
        df: 可转债数据
        top_n: 选择前N只
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_amount: 最小剩余规模（亿元）
        max_amount: 最大剩余规模（亿元）
        
    Returns:
        pd.DataFrame: 筛选后的标的
    """
    # 基本筛选
    condition = (
        (df['price'] <= max_price) &
        (df['premium_rate'] <= max_premium) &
        (df['remain_amount'] >= min_amount) &
        (df['remain_amount'] <= max_amount)
    )
    
    filtered = df[condition].copy()
    
    if len(filtered) == 0:
        return pd.DataFrame()
    
    # 计算双低得分
    filtered = calculate_dual_low_score(filtered)
    
    # 按双低得分排序，选择前N只
    selected = filtered.nsmallest(top_n, 'dual_low_score')
    
    return selected[['code', 'name', 'price', 'premium_rate', 'dual_low_score']]


# ============================================================================
# 性能指标计算模块
# ============================================================================

def calculate_performance_metrics(
    daily_returns: pd.Series,
    daily_assets: pd.Series,
    risk_free_rate: float = 0.03
) -> Dict[str, float]:
    """
    计算性能指标
    
    Args:
        daily_returns: 每日收益率Series
        daily_assets: 每日总资产Series
        risk_free_rate: 无风险利率（年化）
        
    Returns:
        Dict: 性能指标字典
    """
    if len(daily_returns) == 0:
        return {}
    
    # 年化收益率
    total_return = (daily_assets.iloc[-1] / daily_assets.iloc[0]) - 1
    days = len(daily_returns)
    annualized_return = (1 + total_return) ** (252 / days) - 1
    
    # 年化波动率
    annualized_volatility = daily_returns.std() * np.sqrt(252)
    
    # 夏普比率
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
    
    # 最大回撤
    cumulative_returns = (1 + daily_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 胜率
    win_rate = (daily_returns > 0).sum() / len(daily_returns) if len(daily_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate
    }


# ============================================================================
# 历史回测模块
# ============================================================================

def run_historical_backtest(
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    top_n: int = 10,
    cash_per_trade: float = 10000.0,
    max_price: float = 130.0,
    max_premium: float = 30.0,
    min_amount: float = 0.5,
    max_amount: float = 10.0,
    rebalance_days: int = 5,
    random_seed: int = 42,
    is_backtest: bool = True
) -> None:
    """
    运行历史回测
    
    修正：
    1. ✅ 使用正确的数据提供者（HistoricalDataProvider）
    2. ✅ 添加参数验证
    3. ✅ 添加异常处理
    4. ✅ 添加随机种子设置
    
    Args:
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        initial_cash: 初始资金
        top_n: 选择前N只
        cash_per_trade: 每只标的投入金额
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_amount: 最小剩余规模（亿元）
        max_amount: 最大剩余规模（亿元）
        rebalance_days: 调仓周期（天）
        random_seed: 随机种子
        is_backtest: 是否为回测模式
    """
    try:
        # 修正：添加参数验证
        validate_backtest_params(
            initial_cash, top_n, cash_per_trade,
            max_price, max_premium, min_amount, max_amount, rebalance_days
        )
        
        # 修正：设置随机种子
        np.random.seed(random_seed)
        
        logger.info("\n")
        logger.info("╔" + "═"*58 + "╗")
        logger.info("║" + " "*10 + "可转债双低策略历史回测系统" + " "*16 + "║")
        logger.info("╚" + "═"*58 + "╝")
        logger.info(f"回测期间: {start_date} ~ {end_date}")
        logger.info(f"初始资金: {initial_cash:,.2f} 元")
        logger.info(f"每只投入: {cash_per_trade:,.2f} 元")
        logger.info(f"选择数量: {top_n} 只")
        logger.info(f"调仓周期: {rebalance_days} 天")
        logger.info(f"随机种子: {random_seed}")
        logger.info(f"模式: {'回测' if is_backtest else '实盘'}")
        logger.info("\n")
        
        # 初始化投资组合和执行器
        portfolio = Portfolio(initial_cash=initial_cash)
        executor = TradeExecutor(portfolio=portfolio, is_backtest=is_backtest)
        
        # 修正：使用正确的数据提供者（HistoricalDataProvider）
        provider = HistoricalDataProvider(random_seed=random_seed)
        historical_data = provider.fetch_historical_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if historical_data.empty:
            logger.error("无法获取历史数据，回测终止")
            return
        
        # 模拟历史数据（多个交易日）
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
        
        daily_assets = []
        daily_returns = []
        
        logger.info(f"回测交易日数: {len(dates)}")
        logger.info("\n")
        
        # 逐日回测
        for i, date in enumerate(dates):
            logger.info(f"交易日 {i+1}/{len(dates)}: {date.strftime('%Y-%m-%d')}")
            
            # 修正：使用正确的随机种子
            np.random.seed(random_seed + i)
            
            # 模拟每日数据（在真实数据基础上添加随机波动）
            daily_data = historical_data.copy()
            
            # 修正：添加 numpy 导入后使用 np.random.randn()
            daily_data['price'] = daily_data['price'] * (1 + np.random.randn(len(daily_data)) * 0.01)
            
            # 步骤1: 策略筛选
            selected = select_top_bonds(
                daily_data,
                top_n=top_n,
                max_price=max_price,
                max_premium=max_premium,
                min_amount=min_amount,
                max_amount=max_amount
            )
            
            if selected.empty:
                logger.warning(f"  没有符合条件的标的，跳过")
                continue
            
            # 步骤2: 更新持仓市价
            for _, row in selected.iterrows():
                try:
                    portfolio.update_market_price(row['code'], row['price'])
                except Exception as e:
                    logger.debug(f"  更新 {row['code']} 市价失败: {e}")
            
            # 步骤3: 记录当日资产
            total_asset = portfolio.get_total_asset()
            daily_assets.append(total_asset)
            
            if i > 0:
                daily_return = (total_asset - daily_assets[-2]) / daily_assets[-2]
                daily_returns.append(daily_return)
            
            # 步骤4: 修正：使用可配置的调仓周期
            if i % rebalance_days == 0:
                logger.info(f"  执行调仓...")
                executor.execute_strategy(selected, cash_per_trade)
        
        # 计算性能指标
        if daily_returns:
            metrics = calculate_performance_metrics(
                pd.Series(daily_returns),
                pd.Series(daily_assets)
            )
            
            logger.info("\n")
            logger.info("📊 性能指标:")
            logger.info("-"*40)
            logger.info(f"总收益率:     {metrics['total_return']*100:.2f}%")
            logger.info(f"年化收益率:   {metrics['annualized_return']*100:.2f}%")
            logger.info(f"年化波动率:   {metrics['annualized_volatility']*100:.2f}%")
            logger.info(f"夏普比率:     {metrics['sharpe_ratio']:.2f}")
            logger.info(f"最大回撤:     {metrics['max_drawdown']*100:.2f}%")
            logger.info(f"胜率:         {metrics['win_rate']*100:.2f}%")
            logger.info("-"*40)
        
        # 显示最终持仓
        summary = portfolio.get_summary()
        if not summary.empty:
            logger.info("\n")
            logger.info("📈 最终持仓:")
            logger.info("-"*90)
            logger.info(f"{'代码':<8} {'数量':<8} {'手数':<8} {'成本价':<8} {'现价':<8} {'市值':<10} {'盈亏':<10} {'盈亏率':<8}")
            logger.info("-"*90)
            for _, row in summary.iterrows():
                profit_mark = "+" if row['profit'] >= 0 else ""
                logger.info(
                    f"{row['symbol']:<8} "
                    f"{row['quantity']:<8} "
                    f"{row['quantity_hands']:<8.0f} "
                    f"{row['avg_price']:<8.2f} "
                    f"{row['current_price']:<8.2f} "
                    f"{row['market_value']:<10.2f} "
                    f"{profit_mark}{row['profit']:<10.2f} "
                    f"{profit_mark}{row['profit_rate']:<8.2f}%"
                )
            logger.info("-"*90)
        
        # 显示最终资产
        logger.info("\n")
        logger.info("💵 最终资产:")
        logger.info("-"*40)
        logger.info(f"初始资金: {portfolio.initial_cash:,.2f} 元")
        logger.info(f"剩余现金: {portfolio.cash:,.2f} 元")
        logger.info(f"持仓市值: {portfolio.get_total_asset() - portfolio.cash:,.2f} 元")
        logger.info(f"总资产:   {portfolio.get_total_asset():,.2f} 元")
        logger.info("-"*40)
        
        logger.info("\n")
        logger.info("╔" + "═"*58 + "╗")
        logger.info("║" + " "*20 + "回测完成" + " "*27 + "║")
        logger.info("╚" + "═"*58 + "╝")
        logger.info("\n")
    
    except ValueError as e:
        logger.error(f"参数验证失败: {e}")
        return
    except Exception as e:
        logger.error(f"回测过程中发生错误: {e}", exc_info=True)
        return


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    # 回测过去30个交易日
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
    
    run_historical_backtest(
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000.0,    # 初始资金10万
        top_n=10,                 # 选择前10只
        cash_per_trade=10000.0,   # 每只投入1万
        max_price=130.0,          # 最大价格130元
        max_premium=30.0,         # 最大溢价率30%
        min_amount=0.5,           # 最小规模0.5亿
        max_amount=10.0,          # 最大规模10亿
        rebalance_days=5,         # 调仓周期5天
        random_seed=42,           # 随机种子42
        is_backtest=True          # 回测模式
    )


if __name__ == "__main__":
    main()

