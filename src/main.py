"""
币安双向持仓策略 - 主入口
"""
import asyncio
import sys
from config.config_manager import ConfigManager
from interactive.config_interactive import ConfigInteractive
from exchanges.binance_exchange import BinanceExchange
from strategies.hedge_grid_strategy import HedgeGridStrategy
from storage.trade_recorder import TradeRecorder
from utils.logger import setup_logging, get_logger


async def main():
    """主函数"""
    # 配置日志系统
    setup_logging(
        log_file='logs/trading.log',
        log_level=20  # INFO
    )

    logger = get_logger(__name__)

    print("\n" + "="*50)
    print("币安双向持仓自动化交易系统")
    print("="*50 + "\n")

    # 加载配置
    config_manager = ConfigManager("config/config.json")

    # 检查是否已配置
    if not config_manager.load():
        print("配置文件不存在，开始配置...\n")
        config_interactive = ConfigInteractive(config_manager)
        config_interactive.configure()

    # 验证配置
    is_valid, errors = config_manager.validate()
    if not is_valid:
        print("配置验证失败:\n")
        config_manager.show_validation_errors(errors)
        print("请重新配置以修正错误\n")

        config_interactive = ConfigInteractive(config_manager)
        config_interactive.configure()

        # 重新验证
        is_valid, errors = config_manager.validate()
        if not is_valid:
            print("配置验证仍然失败，请检查配置文件")
            return

    # 显示当前配置
    config_interactive = ConfigInteractive(config_manager)
    config_interactive.show_config()

    # 初始化交易记录器
    trade_recorder = TradeRecorder("data")
    logger.info("交易记录器已初始化")

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
        logger.info("正在初始化双向持仓策略...")
        strategy = HedgeGridStrategy(
            exchange=exchange.exchange,
            symbol=strategy_config['symbol'],
            config=strategy_config,
            trade_recorder=trade_recorder
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

            # 显示交易汇总
            summary = trade_recorder.get_trade_summary()
            print("\n" + "="*50)
            print("交易汇总")
            print("="*50)
            print(f"总交易次数: {summary['total_trades']}")
            print(f"买入次数: {summary['buy_trades']}")
            print(f"卖出次数: {summary['sell_trades']}")
            print(f"总交易量: {summary['total_volume']:.4f}")
            print(f"总盈利: {summary['total_profit']:.2f} USDT")
            print(f"总亏损: {summary['total_loss']:.2f} USDT")
            print(f"净盈利: {summary['net_profit']:.2f} USDT")
            print("="*50 + "\n")

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
