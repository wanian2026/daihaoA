"""
策略逻辑测试
"""
import sys
import os
import asyncio

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategies.hedge_grid_strategy import HedgeGridStrategy
import ccxt
from decimal import Decimal

print("="*60)
print("对冲网格策略逻辑测试")
print("="*60 + "\n")

try:
    # 创建模拟交易所实例
    mock_exchange = ccxt.binance({
        'apiKey': 'test',
        'secret': 'test',
        'enableRateLimit': False
    })

    # 创建策略配置
    strategy_config = {
        'base_price': 1000,  # 设置基准价格
        'grid_count': 5,  # 减少网格数量便于测试
        'grid_ratio': 0.05,  # 5%间距
        'investment': 1000,
        'min_profit': 0.002
    }

    # 创建策略实例
    strategy = HedgeGridStrategy(
        exchange=mock_exchange,
        symbol="BTC/USDT",
        config=strategy_config
    )

    print("✅ 策略实例创建成功\n")

    # 测试1: 网格计算
    print("测试1: 网格级别计算")
    print("-"*60)

    levels = strategy._calculate_grid_levels()
    print(f"  网格总数: {len(levels)}")

    if len(levels) > 0:
        print(f"  最高价: {levels[-1]['price']}")
        print(f"  最低价: {levels[0]['price']}")
        print(f"  基准价: {strategy.base_price}")

        # 检查网格数量
        expected_count = strategy.grid_count * 2
        grid_count_ok = len(levels) == expected_count
        print(f"  网格数量正确: {'✅' if grid_count_ok else '❌'} (期望: {expected_count}, 实际: {len(levels)})")

        # 检查价格排序
        prices = [level['price'] for level in levels]
        is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
        print(f"  价格排序正确: {'✅' if is_sorted else '❌'}")

        # 检查买卖单分布
        buy_count = sum(1 for level in levels if level['type'] == 'buy')
        sell_count = sum(1 for level in levels if level['type'] == 'sell')
        distribution_ok = buy_count == sell_count == strategy.grid_count
        print(f"  买卖单分布: {'✅' if distribution_ok else '❌'} (买入: {buy_count}, 卖出: {sell_count})")

        # 显示前5个网格
        print("\n  前5个网格:")
        for i, level in enumerate(levels[:5]):
            type_symbol = "🔽 买入" if level['type'] == 'buy' else "🔼 卖出"
            print(f"    {i+1}. {level['grid_id']} | {type_symbol} | 价格: {level['price']}")

    print("-"*60 + "\n")

    # 测试2: 网格间距验证
    print("测试2: 网格间距验证")
    print("-"*60)

    # 分离买卖单
    buy_levels = [l for l in levels if l['type'] == 'buy']
    sell_levels = [l for l in levels if l['type'] == 'sell']

    # 检查买单间距（从低到高）
    buy_levels_sorted = sorted(buy_levels, key=lambda x: x['price'])
    buy_spacing_ok = True
    for i in range(len(buy_levels_sorted) - 1):
        price1 = buy_levels_sorted[i]['price']
        price2 = buy_levels_sorted[i+1]['price']
        expected_diff = strategy.base_price * strategy.grid_ratio * (i+1)
        actual_diff = strategy.base_price - price2
        # 允许一定误差
        if abs(expected_diff - actual_diff) > 0.01:
            buy_spacing_ok = False
            break

    print(f"  买单间距: {'✅' if buy_spacing_ok else '❌'}")

    # 检查卖单间距（从低到高）
    sell_levels_sorted = sorted(sell_levels, key=lambda x: x['price'])
    sell_spacing_ok = True
    for i, level in enumerate(sell_levels_sorted):
        expected_diff = strategy.base_price * strategy.grid_ratio * (i+1)
        actual_diff = level['price'] - strategy.base_price
        if abs(expected_diff - actual_diff) > 0.01:
            sell_spacing_ok = False
            break

    print(f"  卖单间距: {'✅' if sell_spacing_ok else '❌'}")

    print("-"*60 + "\n")

    # 测试3: 策略状态
    print("测试3: 策略状态检查")
    print("-"*60)

    print(f"  交易对: {'✅' if strategy.symbol == 'BTC/USDT' else '❌'} ({strategy.symbol})")
    print(f"  运行状态: {'✅' if strategy.is_running == False else '❌'} ({strategy.is_running})")
    print(f"  网格订单: {'✅' if len(strategy.grid_orders) == 0 else '❌'} ({len(strategy.grid_orders)})")
    print(f"  挂单列表: {'✅' if len(strategy.open_orders) == 0 else '❌'} ({len(strategy.open_orders)})")

    print("-"*60 + "\n")

    # 测试4: 统计数据
    print("测试4: 统计数据检查")
    print("-"*60)

    print(f"  总盈利: {'✅' if strategy.total_profit == Decimal('0') else '❌'} ({strategy.total_profit})")
    print(f"  交易次数: {'✅' if strategy.trade_count == 0 else '❌'} ({strategy.trade_count})")
    print(f"  买入次数: {'✅' if strategy.buy_count == 0 else '❌'} ({strategy.buy_count})")
    print(f"  卖出次数: {'✅' if strategy.sell_count == 0 else '❌'} ({strategy.sell_count})")

    print("-"*60 + "\n")

    # 测试5: 配置参数
    print("测试5: 配置参数验证")
    print("-"*60)

    print(f"  基准价格: {strategy.base_price}")
    print(f"  网格数量: {strategy.grid_count}")
    print(f"  网格间距: {strategy.grid_ratio * 100}%")
    print(f"  投资金额: {strategy.investment}")
    print(f"  最小止盈: {strategy.min_profit * 100}%")

    config_checks = [
        ('基准价格', strategy.base_price == Decimal('1000')),
        ('网格数量', strategy.grid_count == 5),
        ('网格间距', strategy.grid_ratio == Decimal('0.05')),
        ('投资金额', strategy.investment == Decimal('1000')),
        ('最小止盈', strategy.min_profit == Decimal('0.002')),
    ]

    all_config_ok = True
    for check_name, result in config_checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name} 正确性")
        if not result:
            all_config_ok = False

    print("-"*60 + "\n")

    # 总体评估
    print("="*60)
    print("策略逻辑测试总结")
    print("="*60)

    all_tests_pass = (
        len(levels) == expected_count and
        is_sorted and
        distribution_ok and
        buy_spacing_ok and
        sell_spacing_ok and
        strategy.symbol == 'BTC/USDT' and
        not strategy.is_running and
        len(strategy.grid_orders) == 0 and
        all_config_ok
    )

    if all_tests_pass:
        print("\n✅ 所有测试通过！")
        print("\n策略逻辑完整性: 100%")
        print("\n功能验证:")
        print("  ✅ 网格计算逻辑正确")
        print("  ✅ 价格分布合理")
        print("  ✅ 网格间距准确")
        print("  ✅ 买卖单平衡")
        print("  ✅ 配置参数正确")
        print("  ✅ 状态管理正常")
    else:
        print("\n❌ 部分测试失败")
        print("\n策略逻辑完整性: < 100%")

    print("\n" + "="*60 + "\n")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
