"""
交易所方法测试（模拟环境）
"""
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from exchanges.binance_exchange import BinanceExchange
import ccxt

print("="*60)
print("交易所方法完整性测试")
print("="*60 + "\n")

try:
    # 创建测试实例
    exchange = BinanceExchange(
        api_key="test_key",
        secret="test_secret",
        testnet=True
    )

    print("✅ 交易所实例创建成功\n")

    # 检查所有必需的方法是否存在
    required_methods = [
        'test_connection',
        'get_balance',
        'get_ticker',
        'get_orderbook',
        'create_order',
        'cancel_order',
        'get_open_orders',
        'get_position',
        'close'
    ]

    print("检查必需方法:")
    print("-"*60)

    all_methods_exist = True
    for method_name in required_methods:
        exists = hasattr(exchange, method_name) and callable(getattr(exchange, method_name))
        status = "✅" if exists else "❌"
        print(f"  {status} {method_name}")
        if not exists:
            all_methods_exist = False

    print("-"*60 + "\n")

    # 测试CCXT实例属性
    print("CCXT实例检查:")
    print("-"*60)
    ccxt_checks = [
        ('exchange实例存在', exchange.exchange is not None),
        ('API Key设置', exchange.api_key == "test_key"),
        ('Secret设置', exchange.secret == "test_secret"),
        ('测试网络模式', exchange.testnet == True),
        ('fetch_balance方法存在', hasattr(exchange.exchange, 'fetch_balance')),
        ('fetch_ticker方法存在', hasattr(exchange.exchange, 'fetch_ticker')),
        ('fetch_order_book方法存在', hasattr(exchange.exchange, 'fetch_order_book')),
        ('create_order方法存在', hasattr(exchange.exchange, 'create_order')),
        ('cancel_order方法存在', hasattr(exchange.exchange, 'cancel_order')),
        ('fetch_open_orders方法存在', hasattr(exchange.exchange, 'fetch_open_orders')),
    ]

    for check_name, result in ccxt_checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")

    print("-"*60 + "\n")

    # 测试方法签名
    print("方法签名检查:")
    print("-"*60)

    import inspect

    methods_to_check = [
        'test_connection',
        'get_balance',
        'get_ticker',
        'get_orderbook',
        'create_order',
        'cancel_order',
    ]

    for method_name in methods_to_check:
        method = getattr(exchange, method_name)
        try:
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            # 检查是否是异步方法
            is_async = inspect.iscoroutinefunction(method)

            print(f"  {'✅' if is_async else '⚠️ '} {method_name}")
            print(f"      异步: {is_async}, 参数: {params}")
        except Exception as e:
            print(f"  ❌ {method_name}: {e}")

    print("-"*60 + "\n")

    # 总体评估
    if all_methods_exist:
        print("✅ 所有必需方法都存在且可调用")
        print("\n交易所模块功能完整性: 100%")
    else:
        print("❌ 部分必需方法缺失")
        print("\n交易所模块功能完整性: < 100%")

    print("\n" + "="*60)
    print("交易所方法测试完成")
    print("="*60 + "\n")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
