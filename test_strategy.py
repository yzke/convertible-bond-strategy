"""
策略层测试脚本
验证双低策略是否正常工作
"""
import pandas as pd  # <--- ✅ 补充了这行缺失的导入
import logging
from data.akshare_provider import AkshareProvider
from strategy.double_low_strategy import DoubleLowStrategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_strategy():
    """测试双低策略"""
    print("=" * 60)
    print("测试双低策略")
    print("=" * 60)
    
    # 1. 获取数据
    print("\n步骤1：获取转债数据...")
    provider = AkshareProvider()
    df = provider.get_bond_list()
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    print(f"✅ 数据获取成功，共 {len(df)} 条")
    
    # 2. 显示当前评级分布
    print("\n📊 当前评级分布:")
    if 'rating' in df.columns:
        # 只显示前10个评级，避免刷屏
        rating_counts = df['rating'].value_counts().head(10).to_dict()
        for rating, count in sorted(rating_counts.items()):
            print(f"  {rating}: {count} 条")
    else:
        print("  数据源无 rating 字段")
    
    # 3. 创建策略（不允许未知评级）
    print("\n步骤2：创建双低策略...")
    strategy = DoubleLowStrategy(
        max_price=130,
        max_amount=10,
        min_rating='A',
        allow_unknown_rating=False, # 严格模式
        top_n=10,
        filter_negative_premium=False
    )
    
    print(f"✅ 策略创建成功")
    print(f"   策略参数: {strategy.get_params()}")
    
    # 4. 执行策略分析
    print("\n步骤3：执行策略分析...")
    result_df = strategy.analyze(df)
    
    if result_df.empty:
        print("⚠️  没有转债符合筛选条件")
        return False
    
    print(f"✅ 分析完成，推荐 {len(result_df)} 个转债")
    
    # 5. 显示结果
    print("\n" + "=" * 60)
    print("📊 双低策略推荐结果")
    print("=" * 60)
    
    display_columns = [
        'code', 'name', 'price', 'premium_rate', 
        'remain_amount', 'rating', 'double_low'
    ]
    
    # 确保列存在
    display_columns = [col for col in display_columns if col in result_df.columns]
    
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None) # 防止换行
    pd.set_option('display.float_format', '{:.2f}'.format)
    
    print(result_df[display_columns].to_string(index=False))
    
    return True

if __name__ == "__main__":
    try:
        success = test_strategy()
        if success:
            print("\n" + "=" * 60)
            print("✅ 策略测试通过！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 策略测试失败（无符合条件数据）")
            print("=" * 60)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

