"""
配置管理模块
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

    def load(self) -> bool:
        """
        加载配置文件

        Returns:
            是否加载成功
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"配置文件加载成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False

    def save(self) -> bool:
        """
        保存配置文件

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            logger.info(f"配置文件保存成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value

    def get_exchange_config(self) -> Dict[str, Any]:
        """获取交易所配置"""
        return self.config.get('exchange', {})

    def get_strategy_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.config.get('strategy', {})

    def update_exchange_config(self, config: Dict[str, Any]):
        """更新交易所配置"""
        if 'exchange' not in self.config:
            self.config['exchange'] = {}
        self.config['exchange'].update(config)

    def update_strategy_config(self, config: Dict[str, Any]):
        """更新策略配置"""
        if 'strategy' not in self.config:
            self.config['strategy'] = {}
        self.config['strategy'].update(config)

    def is_configured(self) -> bool:
        """
        检查是否已配置

        Returns:
            是否已配置
        """
        exchange_config = self.get_exchange_config()
        if not exchange_config.get('api_key') or not exchange_config.get('secret'):
            return False

        strategy_config = self.get_strategy_config()
        if not strategy_config.get('symbol'):
            return False

        return True

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 验证交易所配置
        exchange_config = self.get_exchange_config()

        if not exchange_config.get('exchange'):
            errors.append("交易所类型未配置")

        if not exchange_config.get('api_key'):
            errors.append("API Key未配置")

        if not exchange_config.get('secret'):
            errors.append("API Secret未配置")

        # 验证策略配置
        strategy_config = self.get_strategy_config()

        if not strategy_config.get('symbol'):
            errors.append("交易对未配置")

        # 验证数值范围
        investment = strategy_config.get('investment', 0)
        if investment <= 0:
            errors.append(f"投资金额应大于0，当前: {investment}")

        position_ratio = strategy_config.get('position_ratio', 0)
        if position_ratio <= 0 or position_ratio > 1:
            errors.append(f"仓位比例应在0-100%之间，当前: {position_ratio*100}%")

        leverage = strategy_config.get('leverage', 1)
        if leverage < 1 or leverage > 125:
            errors.append(f"杠杆倍数应在1-125之间，当前: {leverage}")

        # 验证ATR参数
        atr_period = strategy_config.get('atr_period', 14)
        if atr_period < 1 or atr_period > 100:
            errors.append(f"ATR周期应在1-100之间，当前: {atr_period}")

        atr_timeframe = strategy_config.get('atr_timeframe', '1h')
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if atr_timeframe not in valid_timeframes:
            errors.append(f"ATR时间周期应为 {', '.join(valid_timeframes)} 之一，当前: {atr_timeframe}")

        # 验证上涨止盈参数
        up_threshold_type = strategy_config.get('up_threshold_type', 'percent')
        if up_threshold_type == 'percent':
            up_threshold = strategy_config.get('up_threshold', 0)
            if up_threshold <= 0 or up_threshold > 0.5:
                errors.append(f"上涨阈值应在0-50%之间，当前: {up_threshold*100}%")
        elif up_threshold_type == 'atr':
            up_atr_multiplier = strategy_config.get('up_atr_multiplier', 0.9)
            if up_atr_multiplier <= 0 or up_atr_multiplier > 5:
                errors.append(f"上涨ATR倍数应在0-5之间，当前: {up_atr_multiplier}")
        else:
            errors.append(f"上涨阈值类型应为 percent 或 atr，当前: {up_threshold_type}")

        # 验证下跌止盈参数
        down_threshold_type = strategy_config.get('down_threshold_type', 'percent')
        if down_threshold_type == 'percent':
            down_threshold = strategy_config.get('down_threshold', 0)
            if down_threshold <= 0 or down_threshold > 0.5:
                errors.append(f"下跌阈值应在0-50%之间，当前: {down_threshold*100}%")
        elif down_threshold_type == 'atr':
            down_atr_multiplier = strategy_config.get('down_atr_multiplier', 0.9)
            if down_atr_multiplier <= 0 or down_atr_multiplier > 5:
                errors.append(f"下跌ATR倍数应在0-5之间，当前: {down_atr_multiplier}")
        else:
            errors.append(f"下跌阈值类型应为 percent 或 atr，当前: {down_threshold_type}")

        # 验证止损参数
        stop_loss_type = strategy_config.get('stop_loss_type', 'percent')
        if stop_loss_type == 'percent':
            stop_loss_ratio = strategy_config.get('stop_loss_ratio', 0)
            if stop_loss_ratio <= 0 or stop_loss_ratio > 0.5:
                errors.append(f"止损比例应在0-50%之间，当前: {stop_loss_ratio*100}%")
        elif stop_loss_type == 'atr':
            stop_loss_atr_multiplier = strategy_config.get('stop_loss_atr_multiplier', 1.5)
            if stop_loss_atr_multiplier <= 0 or stop_loss_atr_multiplier > 10:
                errors.append(f"止损ATR倍数应在0-10之间，当前: {stop_loss_atr_multiplier}")
        else:
            errors.append(f"止损类型应为 percent 或 atr，当前: {stop_loss_type}")

        max_daily_loss = strategy_config.get('max_daily_loss', 0)
        if max_daily_loss < 0:
            errors.append(f"每日最大亏损不能为负数，当前: {max_daily_loss}")

        max_daily_trades = strategy_config.get('max_daily_trades', 0)
        if max_daily_trades < 0:
            errors.append(f"每日最大交易次数不能为负数，当前: {max_daily_trades}")

        max_positions = strategy_config.get('max_positions', 0)
        if max_positions <= 0 or max_positions > 20:
            errors.append(f"最大持仓对数应在1-20之间，当前: {max_positions}")

        return (len(errors) == 0, errors)

    def show_validation_errors(self, errors: list[str]):
        """
        显示验证错误

        Args:
            errors: 错误消息列表
        """
        if not errors:
            return

        print("\n" + "="*50)
        print("配置验证失败")
        print("="*50 + "\n")

        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

        print("\n请修正这些错误后重试\n")

