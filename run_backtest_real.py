"""
可转债双低策略回测脚本（真实数据版本）

修正内容：
1. ✅ 修复 select_top_bonds() 中 rating 列不存在的问题
2. ✅ 修复显示时 KeyError 的问题
3. ✅ 动态处理可选列（rating, dual_low_score）
"""
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Optional

# 导入交易模块
from trading import Portfolio, TradeExecutor, Order
from data.real_data_provider import RealDataProvider, get_column_name, COLUMN_MAPPING

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest_real.log', encoding='utf-8')
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
    min_rating: str = 'A'
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
        min_rating: 最低评级
        
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
    
    # 评级验证
    rating_order = ['C', 'CC', 'CCC', 'B-', 'B', 'B+', 'BB-', 'BB', 'BB+',
                    'BBB-', 'BBB', 'BBB+', 'A-', 'A', 'A+', 'AA-', 'AA', 'AA+', 'AAA']
    if min_rating not in rating_order:
        raise ValueError(f"评级必须是以下之一: {', '.join(rating_order)}")


# ============================================================================
# 数据获取模块
# ============================================================================

def fetch_convertible_bonds_data() -> pd.DataFrame:
    """
    获取可转债实时数据（使用真实数据源）
    
    Returns:
        pd.DataFrame: 可转债数据
    """
    provider = RealDataProvider()
    return provider.fetch_convertible_bonds()


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
    # 使用列名映射获取双低值
    dual_low_col = get_column_name(df, COLUMN_MAPPING['双低'])
    
    if dual_low_col:
        df['dual_low_score'] = df[dual_low_col]
        logger.debug(f"使用数据源提供的双低值: {dual_low_col}")
        return df
    
    # 否则计算双低得分
    logger.debug("计算自定义双低得分")
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
    min_volume: int = 1000,
    min_amount: float = 0.5,
    max_amount: float = 10.0,
    min_rating: str = 'A'
) -> pd.DataFrame:
    """
    筛选双低策略标的（使用真实数据）
    
    修正：动态处理可选列（rating, dual_low_score）
    
    Args:
        df: 可转债数据
        top_n: 选择前N只
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_volume: 最小成交量限制
        min_amount: 最小剩余规模（亿元）
        max_amount: 最大剩余规模（亿元）
        min_rating: 最低评级
        
    Returns:
        pd.DataFrame: 筛选后的标的，包含列：
            - code: 转债代码
            - name: 转债名称
            - price: 转债价格
            - premium_rate: 溢价率（%）
            - remain_amount: 剩余规模（亿元）
            - rating: 评级（如果数据源提供）
            - dual_low_score: 双低得分
    """
    logger.info("="*60)
    logger.info("开始执行双低策略筛选...")
    logger.info(f"筛选条件:")
    logger.info(f"  - 价格 <= {max_price}")
    logger.info(f"  - 溢价率 <= {max_premium}%")
    logger.info(f"  - 剩余规模: {min_amount} ~ {max_amount} 亿元")
    logger.info(f"  - 评级 >= {min_rating}")
    logger.info(f"  - 成交量 >= {min_volume}")
    logger.info(f"选择数量: {top_n} 只")
    logger.info("="*60)
    
    # 基本筛选
    condition = (
        (df['price'] <= max_price) &
        (df['premium_rate'] <= max_premium) &
        (df['remain_amount'] >= min_amount) &
        (df['remain_amount'] <= max_amount)
    )
    
    # 使用列名映射获取成交额列
    amount_col = get_column_name(df, COLUMN_MAPPING['成交额'])
    if amount_col:
        condition &= (df[amount_col] >= min_volume)
        logger.debug(f"使用成交额列: {amount_col}")
    else:
        logger.warning("未找到成交额列，跳过成交量筛选")
    
    # 使用列名映射获取评级列
    rating_col = get_column_name(df, COLUMN_MAPPING['rating'])
    if rating_col:
        # 评级顺序（从低到高）
        rating_order = ['C', 'CC', 'CCC', 'B-', 'B', 'B+', 'BB-', 'BB', 'BB+',
                        'BBB-', 'BBB', 'BBB+', 'A-', 'A', 'A+', 'AA-', 'AA', 'AA+', 'AAA']
        
        def get_rating_index(rating):
            try:
                return rating_order.index(rating)
            except (ValueError, AttributeError):
                return -1
        
        min_index = get_rating_index(min_rating)
        rating_indices = df[rating_col].apply(get_rating_index)
        condition &= (rating_indices >= min_index)
        logger.debug(f"使用评级列: {rating_col}")
    else:
        logger.warning("未找到评级列，跳过评级筛选")
    
    filtered = df[condition].copy()
    
    logger.info(f"基本筛选后剩余: {len(filtered)} 只")
    
    if len(filtered) == 0:
        logger.warning("没有符合条件的标的！")
        return pd.DataFrame()
    
    # 计算双低得分
    filtered = calculate_dual_low_score(filtered)
    
    # 按双低得分排序，选择前N只
    selected = filtered.nsmallest(top_n, 'dual_low_score')
    
    # 修正：动态构建返回列，只包含实际存在的列
    base_columns = ['code', 'name', 'price', 'premium_rate', 'remain_amount', 'dual_low_score']
    
    # 添加可选列
    if rating_col and rating_col in selected.columns:
        # 重命名为 'rating' 以保持一致性
        selected = selected.rename(columns={rating_col: 'rating'})
        base_columns.append('rating')
    
    # 只返回存在的列
    available_columns = [col for col in base_columns if col in selected.columns]
    selected = selected[available_columns]
    
    logger.info(f"最终选择: {len(selected)} 只")
    logger.info(f"返回列: {list(selected.columns)}")
    logger.info("="*60)
    
    return selected


# ============================================================================
# 显示辅助函数
# ============================================================================

def display_selected_bonds(selected: pd.DataFrame) -> None:
    """
    显示筛选结果
    
    修正：动态处理可选列
    
    Args:
        selected: 筛选后的DataFrame
    """
    logger.info("\n")
    logger.info("📊 双低策略筛选结果:")
    
    # 动态构建表头
    has_rating = 'rating' in selected.columns
    
    if has_rating:
        logger.info("-"*100)
        logger.info(f"{'排名':<4} {'代码':<8} {'名称':<10} {'价格':<8} {'溢价率':<10} {'规模':<8} {'评级':<6} {'双低得分':<8}")
        logger.info("-"*100)
        for idx, row in selected.iterrows():
            rank = idx + 1
            logger.info(
                f"{rank:<4} {row['code']:<8} {row['name']:<10} "
                f"{row['price']:<8.2f} {row['premium_rate']:>7.2f}% "
                f"{row['remain_amount']:<8.2f} {row['rating']:<6} {row['dual_low_score']:<8.2f}"
            )
    else:
        logger.info("-"*90)
        logger.info(f"{'排名':<4} {'代码':<8} {'名称':<10} {'价格':<8} {'溢价率':<10} {'规模':<8} {'双低得分':<8}")
        logger.info("-"*90)
        for idx, row in selected.iterrows():
            rank = idx + 1
            logger.info(
                f"{rank:<4} {row['code']:<8} {row['name']:<10} "
                f"{row['price']:<8.2f} {row['premium_rate']:>7.2f}% "
                f"{row['remain_amount']:<8.2f} {row['dual_low_score']:<8.2f}"
            )
    
    logger.info("-"*100 if has_rating else "-"*90)
    logger.info("\n")


def get_bond_name(selected: pd.DataFrame, code: str) -> str:
    """
    获取转债名称
    
    Args:
        selected: 筛选后的DataFrame
        code: 转债代码
        
    Returns:
        str: 转债名称，如果找不到则返回空字符串
    """
    if code in selected['code'].values:
        return selected[selected['code'] == code]['name'].values[0]
    return ''


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
    min_amount: float = 0.5,
    max_amount: float = 10.0,
    min_rating: str = 'A',
    is_backtest: bool = True
) -> None:
    """
    运行回测（使用真实数据）
    
    修正：添加参数验证和异常处理
    
    Args:
        initial_cash: 初始资金
        top_n: 选择前N只
        cash_per_trade: 每只标的投入金额
        max_price: 最大价格限制
        max_premium: 最大溢价率限制（%）
        min_volume: 最小成交量限制
        min_amount: 最小剩余规模（亿元）
        max_amount: 最大剩余规模（亿元）
        min_rating: 最低评级
        is_backtest: 是否为回测模式
    """
    try:
        # 添加参数验证
        validate_backtest_params(
            initial_cash, top_n, cash_per_trade,
            max_price, max_premium, min_amount, max_amount, min_rating
        )
        
        logger.info("\n")
        logger.info("╔" + "═"*58 + "╗")
        logger.info("║" + " "*8 + "可转债双低策略回测系统（真实数据）" + " "*11 + "║")
        logger.info("╚" + "═"*58 + "╝")
        logger.info(f"回测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"初始资金: {initial_cash:,.2f} 元")
        logger.info(f"每只投入: {cash_per_trade:,.2f} 元")
        logger.info(f"选择数量: {top_n} 只")
        logger.info(f"模式: {'回测' if is_backtest else '实盘'}")
        logger.info("\n")
        
        # 步骤1: 获取真实数据
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
            min_volume=min_volume,
            min_amount=min_amount,
            max_amount=max_amount,
            min_rating=min_rating
        )
        if selected.empty:
            logger.error("没有符合条件的标的，回测终止")
            return
        
        # 修正：使用新的显示函数
        display_selected_bonds(selected)
        
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
            logger.info("-"*100)
            logger.info(f"{'代码':<8} {'名称':<10} {'数量':<8} {'手数':<8} {'成本价':<8} {'现价':<8} {'市值':<10} {'盈亏':<10} {'盈亏率':<8}")
            logger.info("-"*100)
            for _, row in summary.iterrows():
                # 修正：使用辅助函数获取名称
                name = get_bond_name(selected, row['symbol'])
                profit_mark = "+" if row['profit'] >= 0 else ""
                logger.info(
                    f"{row['symbol']:<8} {name:<10} "
                    f"{row['quantity']:<8} "
                    f"{row['quantity_hands']:<8.0f} "
                    f"{row['avg_price']:<8.2f} "
                    f"{row['current_price']:<8.2f} "
                    f"{row['market_value']:<10.2f} "
                    f"{profit_mark}{row['profit']:<10.2f} "
                    f"{profit_mark}{row['profit_rate']:<8.2f}%"
                )
            logger.info("-"*100)
        
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
            logger.info("-"*70)
            logger.info(f"{'代码':<8} {'名称':<10} {'方向':<6} {'数量':<8} {'价格':<8} {'金额':<10} {'手续费':<8}")
            logger.info("-"*70)
            for _, row in trade_history.iterrows():
                # 修正：使用辅助函数获取名称
                name = get_bond_name(selected, row['symbol'])
                logger.info(
                    f"{row['symbol']:<8} {name:<10} "
                    f"{row['action']:<6} "
                    f"{row['quantity']:<8} "
                    f"{row['price']:<8.2f} "
                    f"{row['amount']:<10.2f} "
                    f"{row['commission']:<8.2f}"
                )
            logger.info("-"*70)
        
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
    run_backtest(
        initial_cash=100000.0,    # 初始资金10万
        top_n=10,                 # 选择前10只
        cash_per_trade=10000.0,   # 每只投入1万
        max_price=130.0,          # 最大价格130元
        max_premium=30.0,         # 最大溢价率30%
        min_volume=1000,          # 最小成交量1000
        min_amount=0.5,           # 最小规模0.5亿
        max_amount=10.0,          # 最大规模10亿
        min_rating='A',           # 最低评级A
        is_backtest=True          # 回测模式
    )


if __name__ == "__main__":
    main()
