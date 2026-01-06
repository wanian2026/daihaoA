"""
配置管理模块
"""
import json
import os
import logging
from typing import Dict, Any, Optional

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
