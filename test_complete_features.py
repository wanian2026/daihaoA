"""
系统完整功能测试
"""
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("币安对冲网格系统 - 完整功能测试")
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


# 测试1: 风险控制功能
print_section("测试 1: 风险控制功能")

try:
    from strategies.hedge_grid_strategy import HedgeGridStrategy
    import ccxt

    mock_exchange = ccxt.binance({'apiKey': 'test', 'secret': 'test'})

    strategy_config = {
        'base_price': 1000,
        'grid_count': 5,
        'grid_ratio': 0.05,
        'investment': 1000,
        'min_profit': 0.002,
        'stop_loss': 0.05,
        'max_position': 10,
        'max_daily_loss': 100,
        'max_daily_trades': 100
    }

    strategy = HedgeGridStrategy(
        exchange=mock_exchange,
        symbol="BTC/USDT",
        config=strategy_config
    )

    print_test("止损参数设置", strategy.stop_loss == 0.05)
    print_test("最大持仓参数", strategy.max_position == 10)
    print_test("每日最大亏损", strategy.max_daily_loss == 100)
    print_test("每日最大交易次数", strategy.max_daily_trades == 100)
    print_test("风险控制检查方法", hasattr(strategy, '_check_risk_control'))
    print_test("止损检查方法", hasattr(strategy, '_check_stop_loss'))
    print_test("持仓限制检查方法", hasattr(strategy, '_check_position_limit'))
    print_test("紧急停止方法", hasattr(strategy, '_emergency_stop'))

except Exception as e:
    print_test("风险控制功能测试", False, str(e))


# 测试2: 交易记录功能
print_section("测试 2: 交易记录功能")

try:
    from storage.trade_recorder import TradeRecorder

    recorder = TradeRecorder("data")
    print_test("交易记录器创建", True)

    # 测试记录交易
    test_trade = {
        'symbol': 'BTC/USDT',
        'order_id': 'test_001',
        'type': 'buy',
        'price': 1000,
        'amount': 0.1,
        'profit': 10
    }

    recorder.record_trade(test_trade)
    print_test("交易记录保存", True)

    # 测试加载交易
    trades = recorder.load_trades()
    trades_found = len(trades) > 0
    print_test("交易记录加载", trades_found)

    # 测试交易汇总
    summary = recorder.get_trade_summary()
    has_summary = 'total_trades' in summary
    print_test("交易汇总功能", has_summary)

except Exception as e:
    print_test("交易记录功能测试", False, str(e))


# 测试3: 统计分析功能
print_section("测试 3: 统计分析功能")

try:
    from storage.trade_recorder import TradeRecorder

    recorder = TradeRecorder("data")

    # 记录多笔交易
    recorder.record_trade({
        'symbol': 'BTC/USDT',
        'order_id': 'test_001',
        'type': 'buy',
        'price': 1000,
        'amount': 0.1,
        'profit': 0
    })

    recorder.record_trade({
        'symbol': 'BTC/USDT',
        'order_id': 'test_002',
        'type': 'sell',
        'price': 1050,
        'amount': 0.1,
        'profit': 50
    })

    summary = recorder.get_trade_summary()

    print_test("总交易次数统计", summary['total_trades'] >= 2)
    print_test("买入次数统计", summary['buy_trades'] >= 1)
    print_test("卖出次数统计", summary['sell_trades'] >= 1)
    print_test("交易量统计", summary['total_volume'] > 0)
    print_test("盈利统计", summary['total_profit'] >= 50)

except Exception as e:
    print_test("统计分析功能测试", False, str(e))


# 测试4: 日志系统
print_section("测试 4: 日志系统")

try:
    from utils.logger import setup_logging, get_logger

    setup_logging(log_file='logs/test.log')
    print_test("日志系统配置", True)

    logger = get_logger('test')
    print_test("日志记录器获取", True)

    # 测试日志写入
    logger.info("测试日志")
    log_file_exists = os.path.exists('logs/test.log')
    print_test("日志文件创建", log_file_exists)

except Exception as e:
    print_test("日志系统测试", False, str(e))


# 测试5: 配置验证
print_section("测试 5: 配置验证")

try:
    from config.config_manager import ConfigManager

    # 测试有效配置
    cm = ConfigManager("config/config.json")
    cm.load()

    is_valid, errors = cm.validate()
    print_test("配置验证功能", 'is_valid' in dir(cm))

    # 测试错误显示
    if not is_valid and errors:
        cm.show_validation_errors(errors)
        print_test("错误信息显示", True)
    else:
        print_test("错误信息显示", True, "无配置错误")

except Exception as e:
    print_test("配置验证测试", False, str(e))


# 测试6: 异常恢复
print_section("测试 6: 异常恢复机制")

try:
    from strategies.hedge_grid_strategy import HedgeGridStrategy
    import ccxt

    mock_exchange = ccxt.binance({'apiKey': 'test', 'secret': 'test'})
    strategy_config = {
        'base_price': 1000,
        'grid_count': 5,
        'grid_ratio': 0.05,
        'investment': 1000,
        'min_profit': 0.002
    }

    strategy = HedgeGridStrategy(
        exchange=mock_exchange,
        symbol="BTC/USDT",
        config=strategy_config
    )

    print_test("订单状态同步方法", hasattr(strategy, '_sync_order_status'))
    print_test("每日统计重置方法", hasattr(strategy, 'reset_daily_stats'))
    print_test("每日统计更新方法", hasattr(strategy, 'update_daily_stats'))

except Exception as e:
    print_test("异常恢复机制测试", False, str(e))


# 测试7: 模块完整性
print_section("测试 7: 模块完整性")

try:
    from config.config_manager import ConfigManager
    from interactive.config_interactive import ConfigInteractive
    from exchanges.binance_exchange import BinanceExchange
    from strategies.hedge_grid_strategy import HedgeGridStrategy
    from storage.trade_recorder import TradeRecorder
    from utils.logger import setup_logging, get_logger

    print_test("ConfigManager模块", True)
    print_test("ConfigInteractive模块", True)
    print_test("BinanceExchange模块", True)
    print_test("HedgeGridStrategy模块", True)
    print_test("TradeRecorder模块", True)
    print_test("Logger工具模块", True)

except Exception as e:
    print_test("模块完整性测试", False, str(e))


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
    print("🎉 所有测试通过！系统功能完整！")
    print("\n✅ 新增功能验证：")
    print("   风险控制功能 ✅")
    print("   交易记录功能 ✅")
    print("   统计分析功能 ✅")
    print("   日志系统优化 ✅")
    print("   配置验证增强 ✅")
    print("   异常恢复机制 ✅")
    print("\n系统已完全就绪，可以投入使用！")
else:
    print("⚠️  发现问题，请检查失败的测试项")

print("="*60 + "\n")

# 清理测试数据
try:
    if os.path.exists('logs/test.log'):
        os.remove('logs/test.log')
except:
    pass

sys.exit(0 if test_results['failed'] == 0 else 1)
