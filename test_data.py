"""
数据层测试脚本
验证Akshare数据提供者是否正常工作
"""
import logging
from data.akshare_provider import AkshareProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_data_provider():
    """测试数据提供者"""
    print("=" * 60)
    print("测试Akshare数据提供者")
    print("=" * 60)
    
    # 创建数据提供者
    provider = AkshareProvider()
    
    # 获取转债列表
    df = provider.get_bond_list()
    
    # 验证数据
    if df.empty:
        print("\n❌ 测试失败：没有获取到数据")
        print("请检查网络连接或Akshare API是否正常")
        return False
    
    print("\n✅ 数据获取成功！")
    
    # 检查关键字段是否存在
    required_fields = ['code', 'name', 'price', 'premium_rate', 'remain_amount']
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        print(f"\n⚠️  警告：缺少关键字段 {missing_fields}")
        print(f"当前列名: {list(df.columns)}")
        print("可能是Akshare字段变动，需要更新COLUMN_MAPPING")
        return False
    
    print(f"\n📊 数据列名: {list(df.columns)}")
    print(f"\n📝 前3条数据:")
    print(df.head(3).to_string())
    
    # 数据类型验证
    print(f"\n🔍 数据类型检查:")
    print(f"- premium_rate 类型: {df['premium_rate'].dtype}")
    print(f"- premium_rate 示例值: {df['premium_rate'].head().tolist()}")
    
    # 检查是否有异常值
    print(f"\n⚠️  异常值检查:")
    print(f"- premium_rate 中0值的数量: {(df['premium_rate'] == 0).sum()}")
    
    # 数据统计
    print(f"\n📈 数据统计:")
    print(f"- 总数量: {len(df)}")
    if len(df) > 0:
        print(f"- 价格范围: {df['price'].min():.2f} ~ {df['price'].max():.2f}")
        valid_premium = df[df['premium_rate'] > 0]['premium_rate']
        if len(valid_premium) > 0:
            print(f"- 溢价率范围: {valid_premium.min():.2%} ~ {valid_premium.max():.2%}")
        print(f"- 剩余规模范围: {df['remain_amount'].min():.2f} ~ {df['remain_amount'].max():.2f} 亿元")
    
    return True

if __name__ == "__main__":
    success = test_data_provider()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！数据层工作正常")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败，请检查错误日志")
        print("=" * 60)

