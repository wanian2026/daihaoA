"""
测试币安连接和余额获取
"""
import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager
from exchanges.binance_exchange import BinanceExchange


async def test_connection_and_balance():
    """测试连接和获取余额"""
    print("="*50)
    print("币安连接和余额测试")
    print("="*50 + "\n")

    # 加载配置
    config_manager = ConfigManager("config/config.json")

    if not config_manager.load():
        print("❌ 配置文件不存在，请先运行配置向导")
        print("   运行命令: python3 src/main.py")
        return

    exchange_config = config_manager.get_exchange_config()

    # 检查API配置
    if not exchange_config.get('api_key') or not exchange_config.get('secret'):
        print("❌ API Key 或 Secret 未配置")
        print("   请运行配置向导: python3 src/main.py")
        return

    try:
        # 创建交易所实例
        print("📡 正在连接币安交易所...")
        exchange = BinanceExchange(
            api_key=exchange_config['api_key'],
            secret=exchange_config['secret'],
            testnet=exchange_config.get('testnet', False)
        )

        # 测试连接
        print("🔍 测试连接...")
        connected = await exchange.test_connection()

        if not connected:
            print("❌ 连接失败！请检查:")
            print("   1. API Key 和 Secret 是否正确")
            print("   2. 网络是否正常")
            print("   3. API权限是否开启（需要现货交易权限）")
            return

        print("✅ 连接成功！\n")

        # 获取余额
        print("💰 获取账户余额...")
        balance = await exchange.get_balance()

        # 显示余额
        print("\n" + "-"*50)
        print("账户余额:")
        print("-"*50)

        total_usdt = 0

        for currency, info in balance.items():
            if currency in ['info', 'timestamp', 'datetime']:
                continue

            total = float(info.get('total', 0))
            free = float(info.get('free', 0))
            used = float(info.get('used', 0))

            if total > 0:
                print(f"  {currency}:")
                print(f"    总计: {total:.8f}")
                print(f"    可用: {free:.8f}")
                print(f"    冻结: {used:.8f}")

                # 估算USDT价值
                if currency == 'USDT':
                    total_usdt += total

        print("-"*50)
        print(f"USDT 价值估算: ~{total_usdt:.2f} USDT")
        print("-"*50 + "\n")

        # 获取当前市场价格（示例：BTC/USDT）
        print("📊 获取市场行情...")
        try:
            ticker = await exchange.get_ticker("BTC/USDT")
            print(f"  BTC/USDT:")
            print(f"    最新价格: {ticker['last']}")
            print(f"    24h最高: {ticker['high']}")
            print(f"    24h最低: {ticker['low']}")
            print(f"    24h涨跌: {ticker['change']:.2f}%")
        except Exception as e:
            print(f"  获取行情失败: {e}")

        print("\n✅ 测试完成！")
        print("\n提示: 如果余额正常，可以运行策略:")
        print("   python3 src/main.py")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭连接
        if 'exchange' in locals():
            await exchange.close()
            print("\n🔌 连接已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(test_connection_and_balance())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
