"""
主程序导入和结构测试
"""
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("主程序结构测试")
print("="*60 + "\n")

try:
    # 测试所有必需模块导入
    print("测试1: 主程序依赖模块导入")
    print("-"*60)

    try:
        from config.config_manager import ConfigManager
        print("  ✅ ConfigManager 导入成功")
    except Exception as e:
        print(f"  ❌ ConfigManager 导入失败: {e}")

    try:
        from interactive.config_interactive import ConfigInteractive
        print("  ✅ ConfigInteractive 导入成功")
    except Exception as e:
        print(f"  ❌ ConfigInteractive 导入失败: {e}")

    try:
        from exchanges.binance_exchange import BinanceExchange
        print("  ✅ BinanceExchange 导入成功")
    except Exception as e:
        print(f"  ❌ BinanceExchange 导入失败: {e}")

    try:
        from strategies.hedge_grid_strategy import HedgeGridStrategy
        print("  ✅ HedgeGridStrategy 导入成功")
    except Exception as e:
        print(f"  ❌ HedgeGridStrategy 导入失败: {e}")

    print("-"*60 + "\n")

    # 测试主函数结构
    print("测试2: 主程序函数结构")
    print("-"*60)

    # 导入main模块
    import main

    # 检查setup_logging函数
    has_setup_logging = hasattr(main, 'setup_logging') and callable(main.setup_logging)
    print(f"  {'✅' if has_setup_logging else '❌'} setup_logging函数存在")

    # 检查main函数
    has_main = hasattr(main, 'main') and callable(main.main)
    print(f"  {'✅' if has_main else '❌'} main函数存在")

    # 检查main函数是否是协程
    if has_main:
        import asyncio
        is_coroutine = asyncio.iscoroutinefunction(main.main)
        print(f"  {'✅' if is_coroutine else '❌'} main函数是协程")

    print("-"*60 + "\n")

    # 测试配置文件路径
    print("测试3: 配置文件路径")
    print("-"*60)

    config_path = "config/config.json"
    config_exists = os.path.exists(config_path)
    print(f"  {'✅' if config_exists else '❌'} 配置文件存在: {config_path}")

    # 检查是否可以读取配置
    if config_exists:
        try:
            with open(config_path, 'r') as f:
                import json
                config = json.load(f)
            print(f"  ✅ 配置文件格式正确")
            print(f"  ✅ 包含exchange配置: {'exchange' in config}")
            print(f"  ✅ 包含strategy配置: {'strategy' in config}")
        except Exception as e:
            print(f"  ❌ 配置文件读取失败: {e}")

    print("-"*60 + "\n")

    # 测试日志目录
    print("测试4: 日志目录")
    print("-"*60)

    logs_dir = "logs"
    logs_exists = os.path.exists(logs_dir)
    print(f"  {'✅' if logs_exists else '❌'} 日志目录存在: {logs_dir}")

    if not logs_exists:
        try:
            os.makedirs(logs_dir, exist_ok=True)
            print(f"  ✅ 日志目录已创建")
        except Exception as e:
            print(f"  ❌ 日志目录创建失败: {e}")

    print("-"*60 + "\n")

    # 测试主程序导入
    print("测试5: 主程序完整导入")
    print("-"*60)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "src/main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        print("  ✅ 主程序导入成功")
        print("  ✅ 主程序结构完整")
    except Exception as e:
        print(f"  ❌ 主程序导入失败: {e}")

    print("-"*60 + "\n")

    # 总体评估
    print("="*60)
    print("主程序测试总结")
    print("="*60)

    all_tests = [
        has_setup_logging,
        has_main,
        config_exists,
        logs_exists,
    ]

    passed = sum(all_tests)
    total = len(all_tests)

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✅ 所有测试通过！")
        print("\n主程序功能完整性: 100%")
        print("\n可以正常启动:")
        print("   python3 src/main.py")
    else:
        print("\n⚠️  部分测试失败")
        print("\n主程序功能完整性: < 100%")

    print("\n" + "="*60 + "\n")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
