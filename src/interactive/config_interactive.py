"""
交互式配置工具
"""
import logging
from typing import Dict, Any
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConfigInteractive:
    """交互式配置器"""

    def __init__(self, config_manager: ConfigManager):
        """
        初始化交互式配置器

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager

    def configure(self) -> Dict[str, Any]:
        """
        交互式配置

        Returns:
            完整配置
        """
        print("\n" + "="*50)
        print("币安双向持仓策略配置向导")
        print("="*50 + "\n")

        # 配置交易所
        self._configure_exchange()

        # 配置策略
        self._configure_strategy()

        # 保存配置
        self.config_manager.save()

        print("\n" + "="*50)
        print("配置完成！")
        print("="*50 + "\n")

        return self.config_manager.config

    def _configure_exchange(self):
        """配置交易所"""
        print("【步骤 1/2】配置币安交易所")
        print("-" * 30)

        # API Key
        api_key = input("请输入币安 API Key: ").strip()
        if not api_key:
            print("API Key 不能为空")
            return self._configure_exchange()

        # Secret
        secret = input("请输入币安 API Secret: ").strip()
        if not secret:
            print("API Secret 不能为空")
            return self._configure_exchange()

        # 是否使用测试网络
        testnet_input = input("是否使用测试网络 (y/n，默认: n): ").strip().lower()
        testnet = testnet_input == 'y'

        # 更新配置
        self.config_manager.update_exchange_config({
            'exchange': 'binance',
            'api_key': api_key,
            'secret': secret,
            'testnet': testnet
        })

        print("\n✓ 交易所配置完成\n")

    def _configure_strategy(self):
        """配置策略"""
        print("【步骤 2/2】配置双向持仓策略")
        print("-" * 30)

        # 交易对
        symbol = input("请输入交易对 (如 BTC/USDT): ").strip()
        if not symbol:
            print("交易对不能为空")
            return self._configure_strategy()

        # 投资金额
        investment_input = input("请输入投资金额 USDT (默认: 1000): ").strip()
        investment = float(investment_input) if investment_input else 1000

        # 持仓数量
        position_amount_input = input("请输入单笔持仓数量 (留空则自动计算): ").strip()
        position_amount = float(position_amount_input) if position_amount_input else 0

        print("\n【触发阈值配置】")
        print("-" * 30)

        # 上涨阈值
        up_threshold_input = input("请输入上涨触发阈值百分比 (默认: 2，即2%): ").strip()
        up_threshold = float(up_threshold_input) / 100 if up_threshold_input else 0.02

        # 下跌阈值
        down_threshold_input = input("请输入下跌触发阈值百分比 (默认: 2，即2%): ").strip()
        down_threshold = float(down_threshold_input) / 100 if down_threshold_input else 0.02

        print("\n【风险控制配置】")
        print("-" * 30)

        # 止损比例
        stop_loss_ratio_input = input("请输入止损比例百分比 (默认: 5，即5%): ").strip()
        stop_loss_ratio = float(stop_loss_ratio_input) / 100 if stop_loss_ratio_input else 0.05

        # 最大持仓对数
        max_positions_input = input("请输入最大持仓对数 (默认: 5): ").strip()
        max_positions = int(max_positions_input) if max_positions_input else 5

        # 每日最大亏损
        max_daily_loss_input = input("请输入每日最大亏损 USDT (默认: 100): ").strip()
        max_daily_loss = float(max_daily_loss_input) if max_daily_loss_input else 100

        # 每日最大交易次数
        max_daily_trades_input = input("请输入每日最大交易次数 (默认: 50): ").strip()
        max_daily_trades = int(max_daily_trades_input) if max_daily_trades_input else 50

        # 更新配置
        self.config_manager.update_strategy_config({
            'symbol': symbol,
            'investment': investment,
            'position_amount': position_amount,
            'up_threshold': up_threshold,
            'down_threshold': down_threshold,
            'stop_loss_ratio': stop_loss_ratio,
            'max_positions': max_positions,
            'max_daily_loss': max_daily_loss,
            'max_daily_trades': max_daily_trades
        })

        print("\n✓ 策略配置完成\n")

    def show_config(self):
        """显示当前配置"""
        config = self.config_manager.config

        print("\n" + "="*50)
        print("当前配置")
        print("="*50 + "\n")

        # 交易所配置
        exchange = config.get('exchange', {})
        print("【交易所配置】")
        print(f"  交易所: {exchange.get('exchange', 'N/A')}")
        print(f"  API Key: {exchange.get('api_key', '')[:8]}...")
        print(f"  Secret: {exchange.get('secret', '')[:8]}...")
        print(f"  测试网络: {'是' if exchange.get('testnet') else '否'}")
        print()

        # 策略配置
        strategy = config.get('strategy', {})
        print("【策略配置】")
        print(f"  交易对: {strategy.get('symbol', 'N/A')}")
        print(f"  投资金额: {strategy.get('investment', 0)} USDT")
        print(f"  单笔持仓数量: {strategy.get('position_amount', 0) or '自动'}")
        print()

        # 触发阈值配置
        print("【触发阈值配置】")
        print(f"  上涨触发阈值: {strategy.get('up_threshold', 0) * 100}%")
        print(f"  下跌触发阈值: {strategy.get('down_threshold', 0) * 100}%")
        print()

        # 风险控制配置
        print("【风险控制配置】")
        print(f"  止损比例: {strategy.get('stop_loss_ratio', 0) * 100}%")
        print(f"  最大持仓对数: {strategy.get('max_positions', 0)}")
        print(f"  每日最大亏损: {strategy.get('max_daily_loss', 0)} USDT")
        print(f"  每日最大交易次数: {strategy.get('max_daily_trades', 0)}")
        print()

        print("="*50 + "\n")
