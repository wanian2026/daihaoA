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

        print("\n【仓位和杠杆配置】")
        print("-" * 30)

        # 仓位比例
        while True:
            position_ratio_input = input("请输入仓位比例 (0.01-1，如0.1表示10%，默认: 0.1): ").strip()
            try:
                position_ratio = float(position_ratio_input) if position_ratio_input else 0.1
                if position_ratio <= 0 or position_ratio > 1:
                    print("仓位比例应在0-100%之间")
                    continue
                break
            except ValueError:
                print("请输入有效的数字")
                continue

        # 杠杆倍数
        while True:
            leverage_input = input("请输入杠杆倍数 (1-125，默认: 5): ").strip()
            try:
                leverage = int(leverage_input) if leverage_input else 5
                if leverage < 1 or leverage > 125:
                    print("杠杆倍数应在1-125之间")
                    continue
                break
            except ValueError:
                print("请输入有效的整数")
                continue

        print("\n【ATR指标配置】")
        print("-" * 30)

        # ATR周期
        atr_period_input = input("请输入ATR周期 (默认: 14): ").strip()
        atr_period = int(atr_period_input) if atr_period_input else 14

        # ATR时间周期
        atr_timeframe_input = input("请输入ATR时间周期 (1m/5m/15m/1h/4h/1d，默认: 1h): ").strip()
        atr_timeframe = atr_timeframe_input if atr_timeframe_input else '1h'

        print("\n【上涨止盈配置】")
        print("-" * 30)

        # 上涨止盈类型
        while True:
            up_type_input = input("上涨止盈类型 (percent=百分比, atr=ATR倍数，默认: atr): ").strip().lower()
            up_threshold_type = up_type_input if up_type_input else 'atr'
            if up_threshold_type not in ['percent', 'atr']:
                print("请输入 percent 或 atr")
                continue
            break

        up_threshold = 0.02
        up_atr_multiplier = 0.9

        if up_threshold_type == 'percent':
            # 上涨百分比
            up_threshold_input = input("请输入上涨止盈百分比 (默认: 2，即2%): ").strip()
            up_threshold = float(up_threshold_input) / 100 if up_threshold_input else 0.02
        else:
            # 上涨ATR倍数
            up_atr_input = input("请输入上涨ATR倍数 (默认: 0.9): ").strip()
            up_atr_multiplier = float(up_atr_input) if up_atr_input else 0.9

        print("\n【下跌止盈配置】")
        print("-" * 30)

        # 下跌止盈类型
        while True:
            down_type_input = input("下跌止盈类型 (percent=百分比, atr=ATR倍数，默认: atr): ").strip().lower()
            down_threshold_type = down_type_input if down_type_input else 'atr'
            if down_threshold_type not in ['percent', 'atr']:
                print("请输入 percent 或 atr")
                continue
            break

        down_threshold = 0.02
        down_atr_multiplier = 0.9

        if down_threshold_type == 'percent':
            # 下跌百分比
            down_threshold_input = input("请输入下跌止盈百分比 (默认: 2，即2%): ").strip()
            down_threshold = float(down_threshold_input) / 100 if down_threshold_input else 0.02
        else:
            # 下跌ATR倍数
            down_atr_input = input("请输入下跌ATR倍数 (默认: 0.9): ").strip()
            down_atr_multiplier = float(down_atr_input) if down_atr_input else 0.9

        print("\n【止损配置】")
        print("-" * 30)

        # 止损类型
        while True:
            stop_type_input = input("止损类型 (percent=百分比, atr=ATR倍数，默认: atr): ").strip().lower()
            stop_loss_type = stop_type_input if stop_type_input else 'atr'
            if stop_loss_type not in ['percent', 'atr']:
                print("请输入 percent 或 atr")
                continue
            break

        stop_loss_ratio = 0.05
        stop_loss_atr_multiplier = 1.5

        if stop_loss_type == 'percent':
            # 止损百分比
            stop_loss_input = input("请输入止损百分比 (默认: 5，即5%): ").strip()
            stop_loss_ratio = float(stop_loss_input) / 100 if stop_loss_input else 0.05
        else:
            # 止损ATR倍数
            stop_atr_input = input("请输入止损ATR倍数 (默认: 1.5): ").strip()
            stop_loss_atr_multiplier = float(stop_atr_input) if stop_atr_input else 1.5

        print("\n【风险控制配置】")
        print("-" * 30)

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
            'position_ratio': position_ratio,
            'leverage': leverage,
            'up_threshold_type': up_threshold_type,
            'up_threshold': up_threshold,
            'up_atr_multiplier': up_atr_multiplier,
            'down_threshold_type': down_threshold_type,
            'down_threshold': down_threshold,
            'down_atr_multiplier': down_atr_multiplier,
            'stop_loss_type': stop_loss_type,
            'stop_loss_ratio': stop_loss_ratio,
            'stop_loss_atr_multiplier': stop_loss_atr_multiplier,
            'atr_period': atr_period,
            'atr_timeframe': atr_timeframe,
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
        print(f"  交易模式: 合约交易（双向持仓）")
        print()

        # 策略配置
        strategy = config.get('strategy', {})
        print("【策略配置】")
        print(f"  交易对: {strategy.get('symbol', 'N/A')}")
        print(f"  投资金额: {strategy.get('investment', 0)} USDT")
        print(f"  仓位比例: {strategy.get('position_ratio', 0.1) * 100}%")
        print(f"  杠杆倍数: {strategy.get('leverage', 5)}x")
        print()

        # ATR配置
        print("【ATR指标配置】")
        print(f"  ATR周期: {strategy.get('atr_period', 14)}")
        print(f"  ATR时间周期: {strategy.get('atr_timeframe', '1h')}")
        print()

        # 上涨止盈配置
        print("【上涨止盈配置】")
        up_type = strategy.get('up_threshold_type', 'percent')
        if up_type == 'atr':
            print(f"  止盈方式: ATR倍数")
            print(f"  ATR倍数: {strategy.get('up_atr_multiplier', 0.9)}")
        else:
            print(f"  止盈方式: 百分比")
            print(f"  止盈百分比: {strategy.get('up_threshold', 0.02) * 100}%")
        print()

        # 下跌止盈配置
        print("【下跌止盈配置】")
        down_type = strategy.get('down_threshold_type', 'percent')
        if down_type == 'atr':
            print(f"  止盈方式: ATR倍数")
            print(f"  ATR倍数: {strategy.get('down_atr_multiplier', 0.9)}")
        else:
            print(f"  止盈方式: 百分比")
            print(f"  止盈百分比: {strategy.get('down_threshold', 0.02) * 100}%")
        print()

        # 止损配置
        print("【止损配置】")
        stop_type = strategy.get('stop_loss_type', 'percent')
        if stop_type == 'atr':
            print(f"  止损方式: ATR倍数")
            print(f"  ATR倍数: {strategy.get('stop_loss_atr_multiplier', 1.5)}")
        else:
            print(f"  止损方式: 百分比")
            print(f"  止损百分比: {strategy.get('stop_loss_ratio', 0.05) * 100}%")
        print()

        # 风险控制配置
        print("【风险控制配置】")
        print(f"  最大持仓对数: {strategy.get('max_positions', 0)}")
        print(f"  每日最大亏损: {strategy.get('max_daily_loss', 0)} USDT")
        print(f"  每日最大交易次数: {strategy.get('max_daily_trades', 0)}")
        print()

        print("="*50 + "\n")
