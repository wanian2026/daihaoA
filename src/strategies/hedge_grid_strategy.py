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
        config: Dict[str, Any],
        trade_recorder=None
    ):
        """
        初始化对冲网格策略

        Args:
            exchange: 交易所实例
            symbol: 交易对符号
            config: 策略配置
            trade_recorder: 交易记录器（可选）
        """
        self.exchange = exchange
        self.symbol = symbol
        self.config = config
        self.trade_recorder = trade_recorder

        # 策略参数
        self.base_price = Decimal(str(config.get('base_price', 0)))  # 基准价格
        self.grid_count = config.get('grid_count', 10)  # 网格数量
        self.grid_ratio = Decimal(str(config.get('grid_ratio', 0.01)))  # 网格间距(1%)
        self.investment = Decimal(str(config.get('investment', 1000)))  # 投资金额
        self.min_profit = Decimal(str(config.get('min_profit', 0.002)))  # 最小止盈(0.2%)

        # 风险控制参数
        self.stop_loss = Decimal(str(config.get('stop_loss', 0.05)))  # 止损百分比(5%)
        self.max_position = Decimal(str(config.get('max_position', 0)))  # 最大持仓量(0表示不限制)
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 100)))  # 每日最大亏损USDT
        self.max_daily_trades = config.get('max_daily_trades', 100)  # 每日最大交易次数

        # 风险控制状态
        self.current_position = Decimal('0')  # 当前持仓
        self.daily_loss = Decimal('0')  # 每日亏损
        self.daily_trades = 0  # 每日交易次数
        self.is_paused = False  # 是否暂停交易

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
        order = filled['order']

        logger.info(f"订单成交: {grid_id} {order_type}")

        # 计算盈亏
        profit = 0
        if order_type == 'buy':
            self.buy_count += 1
            self.current_position += Decimal(str(order_info['amount']))
        else:
            self.sell_count += 1
            self.current_position -= Decimal(str(order_info['amount']))
            # 卖单可能有盈利（简化计算）
            profit = order.get('cost', 0) * 0.01  # 假设1%的利润
            self.total_profit += Decimal(str(profit))

        # 风险控制检查
        if not self._check_risk_control():
            logger.warning("风险控制触发，停止放置对冲订单")
            return

        # 更新统计
        self.trade_count += 1
        self.daily_trades += 1

        # 更新每日盈亏
        self.update_daily_stats(Decimal(str(profit)))

        # 记录交易
        if self.trade_recorder:
            trade_data = {
                'symbol': self.symbol,
                'order_id': order.get('id'),
                'type': order_type,
                'grid_id': grid_id,
                'price': order.get('price'),
                'amount': order.get('filled'),
                'cost': order.get('cost'),
                'profit': profit,
                'timestamp': order.get('timestamp'),
                'is_counter': order_info.get('is_counter', False)
            }
            self.trade_recorder.record_trade(trade_data)

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

    def _check_risk_control(self) -> bool:
        """
        风险控制检查

        Returns:
            是否允许交易
        """
        # 检查是否暂停
        if self.is_paused:
            logger.warning("交易已暂停，跳过此操作")
            return False

        # 检查每日最大亏损
        if self.daily_loss >= self.max_daily_loss:
            logger.warning(f"已达到每日最大亏损限制: {self.daily_loss}/{self.max_daily_loss} USDT")
            self.is_paused = True
            return False

        # 检查每日最大交易次数
        if self.daily_trades >= self.max_daily_trades:
            logger.warning(f"已达到每日最大交易次数: {self.daily_trades}/{self.max_daily_trades}")
            self.is_paused = True
            return False

        return True

    async def _check_stop_loss(self):
        """检查止损条件"""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            current_price = Decimal(str(ticker['last']))

            # 检查跌破止损线
            if current_price < self.base_price * (1 - self.stop_loss):
                logger.warning(f"价格跌破止损线! 当前: {current_price}, 基准: {self.base_price}, 止损: {self.stop_loss*100}%")
                await self._emergency_stop("价格跌破止损线")
                return True

            # 检查跌破网格最低价
            if self.grid_levels:
                lowest_price = self.grid_levels[0]['price']
                if current_price < lowest_price * (1 - self.grid_ratio):
                    logger.warning(f"价格跌破网格最低价! 当前: {current_price}, 最低: {lowest_price}")
                    await self._emergency_stop("价格跌破网格范围")
                    return True

            return False

        except Exception as e:
            logger.error(f"检查止损失败: {e}")
            return False

    async def _check_position_limit(self, amount: float) -> bool:
        """
        检查持仓限制

        Args:
            amount: 订单数量

        Returns:
            是否允许下单
        """
        if self.max_position <= 0:
            return True  # 不限制

        # 检查是否超过最大持仓
        if self.current_position + Decimal(str(amount)) > self.max_position:
            logger.warning(f"达到最大持仓限制! 当前: {self.current_position}, 最大: {self.max_position}")
            return False

        return True

    async def _emergency_stop(self, reason: str):
        """
        紧急停止

        Args:
            reason: 停止原因
        """
        logger.error(f"触发紧急停止! 原因: {reason}")

        # 取消所有挂单
        await self.cancel_all_orders()

        # 停止策略
        self.is_running = False

        logger.info("策略已紧急停止")

    def update_daily_stats(self, profit: Decimal):
        """
        更新每日统计

        Args:
            profit: 盈亏（正数为盈利，负数为亏损）
        """
        self.daily_trades += 1

        if profit < 0:
            self.daily_loss += abs(profit)
        else:
            # 如果盈利，减少累计亏损
            self.daily_loss = max(Decimal('0'), self.daily_loss - profit)

    def reset_daily_stats(self):
        """重置每日统计（可用于每日重置）"""
        self.daily_loss = Decimal('0')
        self.daily_trades = 0
        self.is_paused = False
        logger.info("每日统计已重置")

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
            'base_price': float(self.base_price),
            'grid_count': len(self.grid_orders),
            'total_trades': self.trade_count,
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'grid_levels': len(self.grid_levels),
            'open_orders': len(self.open_orders),
            'current_position': float(self.current_position),
            'daily_loss': float(self.daily_loss),
            'daily_trades': self.daily_trades,
            'is_paused': self.is_paused,
            'risk_control': {
                'max_position': float(self.max_position),
                'stop_loss': float(self.stop_loss),
                'max_daily_loss': float(self.max_daily_loss),
                'max_daily_trades': self.max_daily_trades
            }
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
        retry_count = 0
        max_retries = 5
        retry_delay = 10  # 秒

        while self.is_running:
            try:
                # 止损检查
                stop_loss_triggered = await self._check_stop_loss()
                if stop_loss_triggered:
                    break

                # 检查已成交订单
                await self.check_filled_orders()

                # 输出状态
                status = await self.get_status()
                logger.info(
                    f"策略状态 | 价格: {status['current_price']} | "
                    f"挂单: {status['grid_count']} | "
                    f"交易: {status['total_trades']} | "
                    f"买入: {status['buy_count']} | "
                    f"卖出: {status['sell_count']} | "
                    f"持仓: {self.current_position} | "
                    f"日亏: {self.daily_loss} USDT | "
                    f"日交易: {self.daily_trades}/{self.max_daily_trades}"
                )

                # 重置重试计数
                retry_count = 0

                # 等待一段时间
                await asyncio.sleep(5)

            except Exception as e:
                retry_count += 1
                logger.error(f"策略运行异常 (第{retry_count}次): {e}")

                if retry_count >= max_retries:
                    logger.error(f"达到最大重试次数 ({max_retries})，策略停止")
                    await self._emergency_stop(f"连续{max_retries}次异常")

                # 指数退避
                delay = min(retry_delay * (2 ** (retry_count - 1)), 300)  # 最大5分钟
                logger.info(f"等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)

                # 尝试恢复订单状态
                try:
                    logger.info("尝试恢复订单状态...")
                    await self._sync_order_status()
                except Exception as sync_error:
                    logger.error(f"订单状态同步失败: {sync_error}")

    async def _sync_order_status(self):
        """同步订单状态"""
        logger.info("同步订单状态...")

        # 获取交易所当前挂单
        try:
            open_orders = await self.exchange.fetch_open_orders(self.symbol)
            open_order_ids = set(order['id'] for order in open_orders)

            # 检查本地记录的订单
            for grid_id, order_info in list(self.grid_orders.items()):
                order_id = order_info['order_id']

                if order_id not in open_order_ids:
                    # 订单可能已成交或取消
                    logger.warning(f"订单可能已成交: {grid_id} {order_id}")

                    # 尝试查询订单状态
                    try:
                        order = await self.exchange.fetch_order(order_id, self.symbol)
                        if order['status'] == 'closed':
                            # 订单成交，需要处理
                            logger.info(f"发现已成交订单: {grid_id}")
                            filled = {
                                'grid_id': grid_id,
                                'order': order,
                                'info': order_info
                            }
                            await self._handle_filled_order(filled)
                    except Exception as e:
                        logger.error(f"查询订单状态失败 {order_id}: {e}")

            logger.info("订单状态同步完成")

        except Exception as e:
            logger.error(f"同步订单状态失败: {e}")
