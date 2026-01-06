"""
综合功能测试脚本
"""
import sys
import os
import asyncio

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("币安对冲网格系统 - 全面功能测试")
print("="*60 + "\n")

test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0
}


def print_test(test_name, passed, message=""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if message:
        print(f"      {message}")
    if passed:
        test_results['passed'] += 1
    else:
        test_results['failed'] += 1


def print_section(title):
    """打印分节标题"""
    print("\n" + "-"*60)
    print(title)
    print("-"*60 + "\n")


# 测试1: 模块导入测试
print_section("测试 1: 模块导入测试")

try:
    from config.config_manager import ConfigManager
    print_test("ConfigManager 导入", True)
except Exception as e:
    print_test("ConfigManager 导入", False, str(e))

try:
    from exchanges.binance_exchange import BinanceExchange
    print_test("BinanceExchange 导入", True)
except Exception as e:
    print_test("BinanceExchange 导入", False, str(e))

try:
    from strategies.hedge_grid_strategy import HedgeGridStrategy
    print_test("HedgeGridStrategy 导入", True)
except Exception as e:
    print_test("HedgeGridStrategy 导入", False, str(e))

try:
    from interactive.config_interactive import ConfigInteractive
    print_test("ConfigInteractive 导入", True)
except Exception as e:
    print_test("ConfigInteractive 导入", False, str(e))


# 测试2: 配置管理测试
print_section("测试 2: 配置管理测试")

try:
    from config.config_manager import ConfigManager
    cm = ConfigManager("config/config.json")
    loaded = cm.load()

    if loaded:
        print_test("配置文件加载", True)
    else:
        print_test("配置文件加载", False, "配置文件不存在或为空")

    # 测试配置读取
    exchange_config = cm.get_exchange_config()
    has_exchange = 'exchange' in exchange_config and exchange_config['exchange'] == 'binance'
    print_test("交易所配置读取", has_exchange)

    strategy_config = cm.get_strategy_config()
    has_symbol = 'symbol' in strategy_config
    print_test("策略配置读取", has_symbol)

    # 测试配置验证
    is_configured = cm.is_configured()
    print_test("配置完整性检查", is_configured)

except Exception as e:
    print_test("配置管理测试", False, str(e))


# 测试3: 交易所实例创建测试
print_section("测试 3: 交易所实例创建测试")

try:
    from exchanges.binance_exchange import BinanceExchange

    # 创建测试实例
    exchange = BinanceExchange(
        api_key="test_key_12345678",
        secret="test_secret_12345678",
        testnet=True
    )

    print_test("交易所实例创建", True)
    print_test("测试网络模式", exchange.testnet)
    print_test("API Key设置", exchange.api_key == "test_key_12345678")

    # 测试CCXT实例
    print_test("CCXT实例创建", exchange.exchange is not None)
    print_test("CCXT实例类型", hasattr(exchange.exchange, 'fetch_balance'))

except Exception as e:
    print_test("交易所实例创建", False, str(e))


# 测试4: 策略实例创建测试
print_section("测试 4: 策略实例创建测试")

try:
    from strategies.hedge_grid_strategy import HedgeGridStrategy
    import ccxt

    # 创建模拟交易所实例
    mock_exchange = ccxt.binance({
        'apiKey': 'test',
        'secret': 'test',
        'enableRateLimit': False
    })

    # 创建策略配置
    strategy_config = {
        'base_price': 0,
        'grid_count': 10,
        'grid_ratio': 0.01,
        'investment': 1000,
        'min_profit': 0.002
    }

    strategy = HedgeGridStrategy(
        exchange=mock_exchange,
        symbol="BTC/USDT",
        config=strategy_config
    )

    print_test("策略实例创建", True)
    print_test("策略配置", strategy.config == strategy_config)
    print_test("交易对设置", strategy.symbol == "BTC/USDT")

    # 测试网格计算
    levels = strategy._calculate_grid_levels()
    print_test("网格级别计算", len(levels) > 0)

    expected_levels = strategy.grid_count * 2  # 上下各grid_count个
    print_test("网格数量正确", len(levels) == expected_levels)

except Exception as e:
    print_test("策略实例创建", False, str(e))
    import traceback
    traceback.print_exc()


# 测试5: 交互式配置测试
print_section("测试 5: 交互式配置测试")

try:
    from interactive.config_interactive import ConfigInteractive
    from config.config_manager import ConfigManager

    cm = ConfigManager("config/config.json")
    ci = ConfigInteractive(cm)

    print_test("交互式配置器创建", True)
    print_test("配置管理器关联", ci.config_manager == cm)

    # 测试show_config方法
    try:
        ci.show_config()
        print_test("配置显示功能", True)
    except:
        print_test("配置显示功能", False)

except Exception as e:
    print_test("交互式配置测试", False, str(e))


# 测试6: 文件完整性测试
print_section("测试 6: 文件完整性测试")

required_files = [
    'src/main.py',
    'src/exchanges/binance_exchange.py',
    'src/strategies/hedge_grid_strategy.py',
    'src/config/config_manager.py',
    'src/interactive/config_interactive.py',
    'config/config.json',
    'requirements.txt',
    'README.md',
    'TESTING.md',
    'test_connection.py',
    'test_balance.py'
]

for file_path in required_files:
    exists = os.path.exists(file_path)
    print_test(f"文件存在: {file_path}", exists)


# 测试7: 依赖包检查
print_section("测试 7: 依赖包检查")

required_packages = [
    'ccxt',
    'asyncio',
    'logging',
    'json',
    'typing',
    'decimal'
]

for package in required_packages:
    try:
        __import__(package)
        print_test(f"依赖包: {package}", True)
    except ImportError:
        print_test(f"依赖包: {package}", False, "未安装")


# 测试8: 配置文件格式测试
print_section("测试 8: 配置文件格式测试")

try:
    import json
    with open('config/config.json', 'r') as f:
        config = json.load(f)

    print_test("JSON格式正确", True)

    # 检查必需字段
    has_exchange = 'exchange' in config
    print_test("包含exchange配置", has_exchange)

    has_strategy = 'strategy' in config
    print_test("包含strategy配置", has_strategy)

    if has_exchange:
        has_api_key = 'api_key' in config['exchange']
        print_test("包含api_key字段", has_api_key)

    if has_strategy:
        has_symbol = 'symbol' in config['strategy']
        print_test("包含symbol字段", has_symbol)

except Exception as e:
    print_test("配置文件格式测试", False, str(e))


# 测试总结
print_section("测试总结")

total_tests = test_results['passed'] + test_results['failed']
pass_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0

print(f"总测试数: {total_tests}")
print(f"通过数量: {test_results['passed']}")
print(f"失败数量: {test_results['failed']}")
print(f"跳过数量: {test_results['skipped']}")
print(f"通过率: {pass_rate:.1f}%")

print("\n" + "="*60)

if test_results['failed'] == 0:
    print("🎉 所有测试通过！项目功能正常！")
    print("\n✅ 系统已准备就绪，可以开始使用：")
    print("   1. 运行配置向导: python3 src/main.py")
    print("   2. 测试连接: python3 test_balance.py")
    print("   3. 启动策略: python3 src/main.py")
else:
    print("⚠️  发现问题，请检查失败的测试项")
    print("\n建议：")
    print("   - 查看详细错误信息")
    print("   - 检查依赖包是否安装: pip install -r requirements.txt")
    print("   - 检查文件是否存在且完整")

print("="*60 + "\n")

# 返回退出码
sys.exit(0 if test_results['failed'] == 0 else 1)
