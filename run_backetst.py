"""
可转债双低策略回测脚本

功能：
1. 📊 获取可转债实时数据
2. 🎯 执行双低策略筛选（价格 + 溢价率）
3. 💰 模拟交易（买入+轮动）
4. 📈 显示持仓和收益

使用方法：
    python run_backtest.py

修正内容：
1. ✅ 修正排名显示（重置索引为1-10）
2. ✅ 修正溢价率显示格式
3. ✅ 生成6位代码（符合可转债代码规范）
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict

# 导入交易模块
from trading import Portfolio, TradeExecutor, Order

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 数据获取模块
# ============================================================================

def fetch_convertible_bonds_data() -> pd.DataFrame:
    """
    获取可转债实时数据
    
    修正：生成6位代码（符合可转债代码规范，如123001）
    
    Returns:
        pd.DataFrame: 可转债数据，包含列：
            - code: 转债代码
            - name: 转债名称
            - price: 转债价格
            - premium_rate: 溢价率（%）
            - volume: 成交量
            - maturity: 剩余年限
    """
    logger.info("="*60)
    logger.info("开始获取可转债数据...")
    logger.info("="*60)
    
    # 模拟数据（实际使用时替换为真实数据源）
    # 这里模拟100只可转债数据
    np.random.seed(42)
    n = 100
    
    # 修正：生成6位代码（符合可转债代码规范，如123001）
    data = {
        'code': [f"12{i:04d}" for i in range(1, n+1)],  # 123001, 123002, ...
        'name': [f"转债{i:03d}" for i in range(1, n+1)],
        'price': np.random.uniform(90, 150, n),
        'premium_rate': np.random.uniform(-5, 50, n),
        'volume': np.random.uniform(1000, 100000, n),
        'maturity': np.random.uniform(0.5, 5.0, n)
    }
    
    df = pd.DataFrame(data)
    df['premium_rate'] = df['premium_rate'].round(2)
    df['price'] = df['price'].round(2)
    df['volume'] = df['volume'].astype(int)
    df['maturity'] = df['maturity'].round(2)
    
    logger.info(f"成功获取 {len(df)} 只可转债数据")
    logger.info("="*60)
    
    return df


# ============================================================================
# 策略模块
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
    min_volume: int = 1000
) -> pd.DataFrame:
    """
    筛选双低策略标的
    
    修正：返回的DataFrame重置索引为1-top_n
    
    Args:
        df: 可转债数据
        top_n: 选择前N只
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_volume: 最小成交量限制
        
    Returns:
        pd.DataFrame: 筛选后的标的
    """
    logger.info("="*60)
    logger.info("开始执行双低策略筛选...")
    logger.info(f"筛选条件: 价格 <= {max_price}, 溢价率 <= {max_premium}%, 成交量 >= {min_volume}")
    logger.info(f"选择数量: {top_n} 只")
    logger.info("="*60)
    
    # 基本筛选
    filtered = df[
        (df['price'] <= max_price) &
        (df['premium_rate'] <= max_premium) &
        (df['volume'] >= min_volume)
    ].copy()
    
    logger.info(f"基本筛选后剩余: {len(filtered)} 只")
    
    if len(filtered) == 0:
        logger.warning("没有符合条件的标的！")
        return pd.DataFrame()
    
    # 计算双低得分
    filtered = calculate_dual_low_score(filtered)
    
    # 按双低得分排序，选择前N只
    selected = filtered.nsmallest(top_n, 'dual_low_score')
    
    # 修正：重置索引为1-top_n
    selected = selected.reset_index(drop=True)
    selected.index += 1  # 索引从1开始
    
    logger.info(f"最终选择: {len(selected)} 只")
    logger.info("="*60)
    
    return selected[['code', 'name', 'price', 'premium_rate', 'dual_low_score']]


# ============================================================================
# 回测模块
# ============================================================================

def run_backtest(
    initial_cash: float = 100000.0,
    top_n: int = 10,
    cash_per_trade: float = 10000.0,
    max_price: float = 130.0,
    max_premium: float = 30.0,
    min_volume: int = 1000,
    is_backtest: bool = True
) -> None:
    """
    运行回测
    
    Args:
        initial_cash: 初始资金
        top_n: 选择前N只
        cash_per_trade: 每只标的投入金额
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_volume: 最小成交量限制
        is_backtest: 是否为回测模式
    """
    logger.info("\n")
    logger.info("╔" + "═"*58 + "╗")
    logger.info("║" + " "*10 + "可转债双低策略回测系统" + " "*19 + "║")
    logger.info("╚" + "═"*58 + "╝")
    logger.info(f"回测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"初始资金: {initial_cash:,.2f} 元")
    logger.info(f"每只投入: {cash_per_trade:,.2f} 元")
    logger.info(f"选择数量: {top_n} 只")
    logger.info(f"模式: {'回测' if is_backtest else '实盘'}")
    logger.info("\n")
    
    # 步骤1: 获取数据
    df = fetch_convertible_bonds_data()
    if df.empty:
        logger.error("无法获取数据，回测终止")
        return
    
    # 步骤2: 策略筛选
    selected = select_top_bonds(
        df,
        top_n=top_n,
        max_price=max_price,
        max_premium=max_premium,
        min_volume=min_volume
    )
    if selected.empty:
        logger.error("没有符合条件的标的，回测终止")
        return
    
    # 修正：显示筛选结果（使用重置后的索引）
    logger.info("\n")
    logger.info("📊 双低策略筛选结果:")
    logger.info("-"*60)
    logger.info(f"{'排名':<4} {'代码':<8} {'名称':<8} {'价格':<8} {'溢价率':<10} {'双低得分':<8}")
    logger.info("-"*60)
    for idx, row in selected.iterrows():
        # 修正：使用重置后的索引作为排名
        rank = idx
        logger.info(f"{rank:<4} {row['code']:<8} {row['name']:<8} {row['price']:<8.2f} {row['premium_rate']:>7.2f}% {row['dual_low_score']:<8.2f}")
    logger.info("-"*60)
    logger.info("\n")
    
    # 步骤3: 初始化投资组合和执行器
    portfolio = Portfolio(initial_cash=initial_cash)
    executor = TradeExecutor(portfolio=portfolio, is_backtest=is_backtest)
    
    # 步骤4: 执行买入
    logger.info("\n")
    logger.info("💰 开始执行买入交易...")
    logger.info("-"*60)
    executor.execute_strategy(selected, cash_per_trade)
    logger.info("-"*60)
    
    # 步骤5: 显示持仓
    summary = portfolio.get_summary()
    if not summary.empty:
        logger.info("\n")
        logger.info("📈 当前持仓:")
        logger.info("-"*80)
        logger.info(f"{'代码':<8} {'数量':<8} {'手数':<8} {'成本价':<8} {'现价':<8} {'市值':<10} {'盈亏':<10} {'盈亏率':<8}")
        logger.info("-"*80)
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
        logger.info("-"*80)
    
    # 步骤6: 显示资金和总资产
    logger.info("\n")
    logger.info("💵 资金概览:")
    logger.info("-"*40)
    logger.info(f"初始资金: {portfolio.initial_cash:,.2f} 元")
    logger.info(f"剩余现金: {portfolio.cash:,.2f} 元")
    logger.info(f"持仓市值: {portfolio.get_total_asset() - portfolio.cash:,.2f} 元")
    logger.info(f"总资产:   {portfolio.get_total_asset():,.2f} 元")
    logger.info("-"*40)
    
    # 步骤7: 计算收益率
    total_profit = portfolio.get_total_asset() - portfolio.initial_cash
    profit_rate = (total_profit / portfolio.initial_cash) * 100
    profit_mark = "+" if total_profit >= 0 else ""
    
    logger.info("\n")
    logger.info("📊 收益汇总:")
    logger.info("-"*40)
    logger.info(f"总盈亏:   {profit_mark}{total_profit:,.2f} 元")
    logger.info(f"总收益率: {profit_mark}{profit_rate:.2f}%")
    logger.info("-"*40)
    
    # 步骤8: 显示交易历史
    trade_history = portfolio.get_trade_history()
    if not trade_history.empty:
        logger.info("\n")
        logger.info("📝 交易历史:")
        logger.info("-"*60)
        logger.info(f"{'代码':<8} {'方向':<6} {'数量':<8} {'价格':<8} {'金额':<10} {'手续费':<8}")
        logger.info("-"*60)
        for _, row in trade_history.iterrows():
            logger.info(
                f"{row['symbol']:<8} "
                f"{row['action']:<6} "
                f"{row['quantity']:<8} "
                f"{row['price']:<8.2f} "
                f"{row['amount']:<10.2f} "
                f"{row['commission']:<8.2f}"
            )
        logger.info("-"*60)
    
    # 步骤9: 显示订单记录
    orders = executor.get_orders()
    if orders:
        logger.info("\n")
        logger.info("📋 订单记录:")
        logger.info("-"*60)
        for order in orders:
            logger.info(f"{order}")
        logger.info("-"*60)
    
    logger.info("\n")
    logger.info("╔" + "═"*58 + "╗")
    logger.info("║" + " "*20 + "回测完成" + " "*27 + "║")
    logger.info("╚" + "═"*58 + "╝")
    logger.info("\n")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    try:
        run_backtest(
            initial_cash=100000.0,    # 初始资金10万
            top_n=10,                 # 选择前10只
            cash_per_trade=10000.0,   # 每只投入1万
            max_price=130.0,          # 最大价格130元
            max_premium=30.0,         # 最大溢价率30%
            min_volume=1000,          # 最小成交量1000
            is_backtest=True          # 回测模式
        )
    except Exception as e:
        logger.error(f"回测过程中发生错误: {e}", exc_info=True)


if __name__ == "__main__":
    main()
