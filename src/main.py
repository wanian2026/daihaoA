"""
币安对冲网格策略 - 主入口
"""
import asyncio
import logging
import sys
from config.config_manager import ConfigManager
from interactive.config_interactive import ConfigInteractive
from exchanges.binance_exchange import BinanceExchange
from strategies.hedge_grid_strategy import HedgeGridStrategy


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)

    print("\n" + "="*50)
    print("币安对冲网格自动化交易系统")
    print("="*50 + "\n")

    # 加载配置
    config_manager = ConfigManager("config/config.json")

    # 检查是否已配置
    if not config_manager.load() or not config_manager.is_configured():
        print("未检测到有效配置，开始配置...\n")
        config_interactive = ConfigInteractive(config_manager)
        config_interactive.configure()

    # 显示当前配置
    config_interactive = ConfigInteractive(config_manager)
    config_interactive.show_config()

    # 确认启动
    confirm = input("确认启动策略? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消启动")
        return

    # 获取配置
    exchange_config = config_manager.get_exchange_config()
    strategy_config = config_manager.get_strategy_config()

    try:
        # 初始化交易所
        logger.info("正在连接币安交易所...")
        exchange = BinanceExchange(
            api_key=exchange_config['api_key'],
            secret=exchange_config['secret'],
            testnet=exchange_config.get('testnet', False)
        )

        # 测试连接
        if not await exchange.test_connection():
            logger.error("币安连接测试失败，请检查API配置")
            return

        logger.info("币安连接成功")

        # 初始化策略
        logger.info("正在初始化对冲网格策略...")
        strategy = HedgeGridStrategy(
            exchange=exchange.exchange,
            symbol=strategy_config['symbol'],
            config=strategy_config
        )

        # 启动策略
        await strategy.start()
        logger.info("策略已启动，按 Ctrl+C 停止\n")

        # 运行策略主循环
        try:
            await strategy.run_loop()
        except KeyboardInterrupt:
            print("\n\n正在停止策略...")
            await strategy.stop()
            print("策略已停止")

    except Exception as e:
        logger.error(f"运行异常: {e}", exc_info=True)
    finally:
        if 'exchange' in locals():
            await exchange.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
