"""
日志配置模块
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os


def setup_logging(
    log_file='logs/trading.log',
    log_level=logging.INFO,
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5
):
    """
    配置日志系统

    Args:
        log_file: 日志文件路径
        log_level: 日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 创建日志格式
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 文件处理器（支持日志轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 设置交易所库的日志级别（减少噪音）
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)
