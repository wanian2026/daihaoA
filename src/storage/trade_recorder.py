"""
交易记录持久化模块
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class TradeRecorder:
    """交易记录器"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化交易记录器

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.trades_file = os.path.join(data_dir, "trades.jsonl")
        self.stats_file = os.path.join(data_dir, "stats.json")

        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)

        logger.info(f"交易记录器初始化: {self.data_dir}")

    def record_trade(self, trade_data: Dict[str, Any]):
        """
        记录交易

        Args:
            trade_data: 交易数据
        """
        try:
            # 添加时间戳
            trade_data['timestamp'] = datetime.now().isoformat()

            # 追加到交易记录文件
            with open(self.trades_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, ensure_ascii=False) + '\n')

            logger.info(f"交易已记录: {trade_data.get('order_id')}")

        except Exception as e:
            logger.error(f"记录交易失败: {e}")

    def load_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        加载交易记录

        Args:
            limit: 最大加载条数

        Returns:
            交易记录列表
        """
        trades = []

        if not os.path.exists(self.trades_file):
            return trades

        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 倒序读取最新的记录
            for line in reversed(lines[-limit:]):
                if line.strip():
                    trade = json.loads(line)
                    trades.append(trade)

        except Exception as e:
            logger.error(f"加载交易记录失败: {e}")

        return trades

    def save_stats(self, stats: Dict[str, Any]):
        """
        保存统计数据

        Args:
            stats: 统计数据
        """
        try:
            stats['last_updated'] = datetime.now().isoformat()

            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=4, ensure_ascii=False)

            logger.info("统计数据已保存")

        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")

    def load_stats(self) -> Dict[str, Any]:
        """
        加载统计数据

        Returns:
            统计数据字典
        """
        if not os.path.exists(self.stats_file):
            return {}

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info("统计数据已加载")
            return stats

        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
            return {}

    def clear_trades(self):
        """清空交易记录"""
        try:
            if os.path.exists(self.trades_file):
                os.remove(self.trades_file)
                logger.info("交易记录已清空")
        except Exception as e:
            logger.error(f"清空交易记录失败: {e}")

    def get_trade_summary(self) -> Dict[str, Any]:
        """
        获取交易汇总

        Returns:
            交易汇总数据
        """
        trades = self.load_trades(limit=10000)

        if not trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_volume': 0,
                'total_profit': 0,
                'total_loss': 0,
                'net_profit': 0
            }

        total_trades = len(trades)
        buy_trades = sum(1 for t in trades if t.get('type') == 'buy')
        sell_trades = total_trades - buy_trades
        total_volume = sum(t.get('amount', 0) for t in trades)
        total_profit = sum(t.get('profit', 0) for t in trades if t.get('profit', 0) > 0)
        total_loss = sum(abs(t.get('profit', 0)) for t in trades if t.get('profit', 0) < 0)
        net_profit = sum(t.get('profit', 0) for t in trades)

        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_volume': total_volume,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': net_profit
        }
