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
        print("币安对冲网格策略配置向导")
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
        print("【步骤 2/2】配置对冲网格策略")
        print("-" * 30)

        # 交易对
        symbol = input("请输入交易对 (如 BTC/USDT): ").strip()
        if not symbol:
            print("交易对不能为空")
            return self._configure_strategy()

        # 基准价格
        base_price_input = input("请输入基准价格 (留空则使用当前价格): ").strip()
        base_price = float(base_price_input) if base_price_input else 0

        # 网格数量
        grid_count_input = input("请输入网格数量 (默认: 10): ").strip()
        grid_count = int(grid_count_input) if grid_count_input else 10

        # 网格间距
        grid_ratio_input = input("请输入网格间距百分比 (默认: 1，即1%): ").strip()
        grid_ratio = float(grid_ratio_input) / 100 if grid_ratio_input else 0.01

        # 投资金额
        investment_input = input("请输入投资金额 USDT (默认: 1000): ").strip()
        investment = float(investment_input) if investment_input else 1000

        # 最小止盈
        min_profit_input = input("请输入最小止盈百分比 (默认: 0.2，即0.2%): ").strip()
        min_profit = float(min_profit_input) / 100 if min_profit_input else 0.002

        # 更新配置
        self.config_manager.update_strategy_config({
            'symbol': symbol,
            'base_price': base_price,
            'grid_count': grid_count,
            'grid_ratio': grid_ratio,
            'investment': investment,
            'min_profit': min_profit
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
        print(f"  基准价格: {strategy.get('base_price', 0) or '自动'}")
        print(f"  网格数量: {strategy.get('grid_count', 0)}")
        print(f"  网格间距: {strategy.get('grid_ratio', 0) * 100}%")
        print(f"  投资金额: {strategy.get('investment', 0)} USDT")
        print(f"  最小止盈: {strategy.get('min_profit', 0) * 100}%")
        print()

        print("="*50 + "\n")
