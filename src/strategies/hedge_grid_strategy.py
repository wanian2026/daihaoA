"""
对冲网格策略引擎
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import ccxt

logger = logging.getLogger(__name__)


class HedgeGridStrategy:
    """对冲网格策略"""

    def __init__(
        self,
        exchange: ccxt.Exchange,
        symbol: str,
        config: Dict[str, Any]
    ):
        """
        初始化对冲网格策略

        Args:
            exchange: 交易所实例
            symbol: 交易对符号
            config: 策略配置
        """
        self.exchange = exchange
        self.symbol = symbol
        self.config = config

        # 策略参数
        self.base_price = Decimal(str(config.get('base_price', 0)))  # 基准价格
        self.grid_count = config.get('grid_count', 10)  # 网格数量
        self.grid_ratio = Decimal(str(config.get('grid_ratio', 0.01)))  # 网格间距(1%)
        self.investment = Decimal(str(config.get('investment', 1000)))  # 投资金额
        self.min_profit = Decimal(str(config.get('min_profit', 0.002)))  # 最小止盈(0.2%)

        # 运行状态
        self.is_running = False
        self.grid_orders: Dict[str, Dict] = {}  # grid_id -> order_info
        self.open_orders: List[str] = []  # 挂单ID列表

        # 统计数据
        self.total_profit = Decimal('0')
        self.trade_count = 0
        self.buy_count = 0
        self.sell_count = 0

        logger.info(f"对冲网格策略初始化: {symbol}")

    async def initialize(self):
        """初始化策略"""
        logger.info("开始初始化对冲网格策略...")

        # 获取当前价格作为基准价（如果未设置）
        if self.base_price <= 0:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            self.base_price = Decimal(str(ticker['last']))
            logger.info(f"使用当前价格作为基准价: {self.base_price}")

        # 计算网格价位
        self.grid_levels = self._calculate_grid_levels()
        logger.info(f"计算网格级别完成，共 {len(self.grid_levels)} 个价位")

        logger.info("对冲网格策略初始化完成")

    def _calculate_grid_levels(self) -> List[Decimal]:
        """
        计算网格价位

        Returns:
            网格价位列表
        """
        levels = []

        # 上方网格（卖出网格）
        for i in range(1, self.grid_count + 1):
            price = self.base_price * (1 + self.grid_ratio * i)
            levels.append({
                'price': price,
                'type': 'sell',
                'grid_id': f"sell_{i}"
            })

        # 下方网格（买入网格）
        for i in range(1, self.grid_count + 1):
            price = self.base_price * (1 - self.grid_ratio * i)
            levels.append({
                'price': price,
                'type': 'buy',
                'grid_id': f"buy_{i}"
            })

        # 按价格排序
        levels.sort(key=lambda x: x['price'])
        return levels

    async def place_grid_orders(self):
        """放置网格订单"""
        logger.info("开始放置网格订单...")

        # 取消所有现有挂单
        await self.cancel_all_orders()

        # 计算每笔订单数量
        ticker = await self.exchange.fetch_ticker(self.symbol)
        current_price = Decimal(str(ticker['last']))

        # 估算订单数量
        base_currency = self.symbol.split('/')[0]
        balance = await self.exchange.fetch_balance()
        available_usdt = Decimal(str(balance.get('USDT', {}).get('free', 0)))
        available_base = Decimal(str(balance.get(base_currency, {}).get('free', 0)))

        # 放置网格订单
        for level in self.grid_levels:
            try:
                grid_id = level['grid_id']
                order_type = level['type']
                price = level['price']

                # 计算订单数量
                if order_type == 'buy':
                    # 买单：根据可用USDT计算
                    amount = (self.investment / (2 * self.grid_count)) / price
                else:
                    # 卖单：根据持有币种计算
                    amount = (self.investment / (2 * self.grid_count)) / current_price

                amount = float(amount)

                # 创建订单
                if order_type == 'buy':
                    order = await self.exchange.create_limit_buy_order(
                        self.symbol,
                        amount,
                        float(price)
                    )
                else:
                    order = await self.exchange.create_limit_sell_order(
                        self.symbol,
                        amount,
                        float(price)
                    )

                # 记录订单信息
                self.grid_orders[grid_id] = {
                    'order_id': order['id'],
                    'type': order_type,
                    'price': price,
                    'amount': amount,
                    'grid_id': grid_id
                }
                self.open_orders.append(order['id'])

                logger.info(f"放置网格订单成功: {grid_id} {order_type} @ {price}")

            except Exception as e:
                logger.error(f"放置网格订单失败 {level['grid_id']}: {e}")

        logger.info(f"网格订单放置完成，共 {len(self.grid_orders)} 个订单")

    async def cancel_all_orders(self):
        """取消所有挂单"""
        logger.info("取消所有挂单...")
        try:
            orders = await self.exchange.fetch_open_orders(self.symbol)
            for order in orders:
                try:
                    await self.exchange.cancel_order(order['id'], self.symbol)
                    logger.info(f"取消订单: {order['id']}")
                except Exception as e:
                    logger.error(f"取消订单失败 {order['id']}: {e}")

            self.grid_orders.clear()
            self.open_orders.clear()
        except Exception as e:
            logger.error(f"取消挂单失败: {e}")

    async def check_filled_orders(self):
        """检查已成交订单"""
        filled_orders = []

        # 检查所有网格订单状态
        for grid_id, order_info in list(self.grid_orders.items()):
            try:
                order = await self.exchange.fetch_order(
                    order_info['order_id'],
                    self.symbol
                )

                if order['status'] == 'closed':
                    filled_orders.append({
                        'grid_id': grid_id,
                        'order': order,
                        'info': order_info
                    })
                    # 从活跃订单中移除
                    del self.grid_orders[grid_id]
                    if order_info['order_id'] in self.open_orders:
                        self.open_orders.remove(order_info['order_id'])

            except Exception as e:
                logger.error(f"检查订单状态失败 {grid_id}: {e}")

        # 处理已成交订单
        for filled in filled_orders:
            await self._handle_filled_order(filled)

    async def _handle_filled_order(self, filled: Dict):
        """
        处理已成交订单

        Args:
            filled: 已成交订单信息
        """
        order_info = filled['info']
        order_type = order_info['type']
        grid_id = filled['grid_id']

        logger.info(f"订单成交: {grid_id} {order_type}")

        # 更新统计
        self.trade_count += 1
        if order_type == 'buy':
            self.buy_count += 1
        else:
            self.sell_count += 1

        # 重新放置对冲订单
        # 如果是买单成交，在上方放置卖单
        # 如果是卖单成交，在下方放置买单
        if order_type == 'buy':
            # 买单成交，在上方放置卖单
            sell_price = order_info['price'] * (1 + self.grid_ratio)
            await self._place_counter_order('sell', sell_price, order_info['amount'])
        else:
            # 卖单成交，在下方放置买单
            buy_price = order_info['price'] * (1 - self.grid_ratio)
            await self._place_counter_order('buy', buy_price, order_info['amount'])

    async def _place_counter_order(self, order_type: str, price: Decimal, amount: float):
        """
        放置对冲订单

        Args:
            order_type: 订单类型
            price: 价格
            amount: 数量
        """
        try:
            if order_type == 'buy':
                order = await self.exchange.create_limit_buy_order(
                    self.symbol,
                    amount,
                    float(price)
                )
                new_grid_id = f"counter_buy_{order['id'][:8]}"
            else:
                order = await self.exchange.create_limit_sell_order(
                    self.symbol,
                    amount,
                    float(price)
                )
                new_grid_id = f"counter_sell_{order['id'][:8]}"

            # 记录订单
            self.grid_orders[new_grid_id] = {
                'order_id': order['id'],
                'type': order_type,
                'price': price,
                'amount': amount,
                'grid_id': new_grid_id,
                'is_counter': True
            }
            self.open_orders.append(order['id'])

            logger.info(f"放置对冲订单: {new_grid_id} {order_type} @ {price}")

        except Exception as e:
            logger.error(f"放置对冲订单失败: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """
        获取策略状态

        Returns:
            策略状态字典
        """
        ticker = await self.exchange.fetch_ticker(self.symbol)

        return {
            'symbol': self.symbol,
            'is_running': self.is_running,
            'current_price': ticker['last'],
            'grid_count': len(self.grid_orders),
            'total_trades': self.trade_count,
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'grid_levels': len(self.grid_levels),
            'open_orders': len(self.open_orders)
        }

    async def start(self):
        """启动策略"""
        if self.is_running:
            logger.warning("策略已经在运行中")
            return

        logger.info("启动对冲网格策略...")
        self.is_running = True

        # 初始化并放置订单
        await self.initialize()
        await self.place_grid_orders()

        logger.info("对冲网格策略启动完成")

    async def stop(self):
        """停止策略"""
        if not self.is_running:
            return

        logger.info("停止对冲网格策略...")
        self.is_running = False

        # 取消所有挂单
        await self.cancel_all_orders()

        logger.info("对冲网格策略已停止")

    async def run_loop(self):
        """策略主循环"""
        while self.is_running:
            try:
                # 检查已成交订单
                await self.check_filled_orders()

                # 输出状态
                status = await self.get_status()
                logger.info(
                    f"策略状态 | 价格: {status['current_price']} | "
                    f"挂单: {status['grid_count']} | "
                    f"交易: {status['total_trades']} | "
                    f"买入: {status['buy_count']} | "
                    f"卖出: {status['sell_count']}"
                )

                # 等待一段时间
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"策略运行异常: {e}")
                await asyncio.sleep(10)
