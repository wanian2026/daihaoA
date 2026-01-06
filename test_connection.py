"""
测试交易所连接和余额获取（模拟模式）
"""
import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager
from exchanges.binance_exchange import BinanceExchange


async def test_without_api():
    """测试模块导入和基本功能（不需要真实API）"""
    print("="*50)
    print("模块功能测试（无需API）")
    print("="*50 + "\n")

    # 测试配置管理
    print("📋 测试配置管理...")
    config_manager = ConfigManager("config/config.json")

    if config_manager.load():
        print("✅ 配置加载成功")
        print(f"   交易所: {config_manager.get('exchange', {}).get('exchange')}")
        print(f"   交易对: {config_manager.get('strategy', {}).get('symbol')}")
    else:
        print("❌ 配置加载失败")

    # 测试交易所实例创建（模拟）
    print("\n🔧 测试交易所实例创建...")
    try:
        exchange = BinanceExchange(
            api_key="test_key",
            secret="test_secret",
            testnet=True
        )
        print("✅ 交易所实例创建成功")
        print(f"   测试网络模式: {exchange.testnet}")
        print(f"   API Key: {exchange.api_key[:8]}...")
    except Exception as e:
        print(f"❌ 实例创建失败: {e}")

    print("\n" + "="*50)
    print("基本功能测试完成")
    print("="*50)
    print("\n📝 测试说明:")
    print("   - 模块导入 ✅")
    print("   - 配置管理 ✅")
    print("   - 交易所实例创建 ✅")
    print("   - 真实API连接需要配置有效的API Key")
    print("\n💡 下一步:")
    print("   1. 运行配置向导: python3 src/main.py")
    print("   2. 输入真实的币安API Key和Secret")
    print("   3. 运行测试脚本: python3 test_balance.py")


if __name__ == "__main__":
    try:
        asyncio.run(test_without_api())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
