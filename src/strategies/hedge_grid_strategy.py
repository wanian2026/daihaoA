"""
双向持仓策略引擎
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import ccxt

logger = logging.getLogger(__name__)


class HedgeGridStrategy:
    """双向持仓策略（同时持有多单和空单）"""

    def __init__(
        self,
        exchange: ccxt.Exchange,
        symbol: str,
        config: Dict[str, Any],
        trade_recorder=None
    ):
        """
        初始化双向持仓策略

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
        self.investment = Decimal(str(config.get('investment', 1000)))  # 投资金额（每个单方向）
        self.position_ratio = Decimal(str(config.get('position_ratio', 0.1)))  # 仓位比例（0-1，如0.1表示10%）
        self.leverage = config.get('leverage', 5)  # 杠杆倍数

        # 触发阈值（支持ATR或百分比）
        self.up_threshold_type = config.get('up_threshold_type', 'percent')  # 'percent' 或 'atr'
        self.up_threshold = Decimal(str(config.get('up_threshold', 0.02)))  # 上涨触发阈值
        self.up_atr_multiplier = Decimal(str(config.get('up_atr_multiplier', 0.9)))  # 上涨ATR倍数

        self.down_threshold_type = config.get('down_threshold_type', 'percent')  # 'percent' 或 'atr'
        self.down_threshold = Decimal(str(config.get('down_threshold', 0.02)))  # 下跌触发阈值
        self.down_atr_multiplier = Decimal(str(config.get('down_atr_multiplier', 0.9)))  # 下跌ATR倍数

        # 止损参数（支持ATR或百分比）
        self.stop_loss_type = config.get('stop_loss_type', 'percent')  # 'percent' 或 'atr'
        self.stop_loss_ratio = Decimal(str(config.get('stop_loss_ratio', 0.05)))  # 止损比例
        self.stop_loss_atr_multiplier = Decimal(str(config.get('stop_loss_atr_multiplier', 1.5)))  # 止损ATR倍数

        # ATR参数
        self.atr_period = config.get('atr_period', 14)  # ATR周期（默认14）
        self.atr_timeframe = config.get('atr_timeframe', '1h')  # ATR时间周期（默认1小时）

        # 风险控制参数
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 100)))  # 每日最大亏损USDT
        self.max_daily_trades = config.get('max_daily_trades', 50)  # 每日最大交易次数
        self.max_positions = config.get('max_positions', 5)  # 最大持仓对数

        # 持仓管理
        self.long_positions: List[Dict] = []  # 多单列表
        self.short_positions: List[Dict] = []  # 空单列表

        # 风险控制状态
        self.daily_loss = Decimal('0')  # 每日亏损
        self.daily_trades = 0  # 每日交易次数
        self.is_paused = False  # 是否暂停交易

        # 运行状态
        self.is_running = False
        self.current_atr = Decimal('0')  # 当前ATR值
        self.account_balance = Decimal('0')  # 账户余额

        # 统计数据
        self.total_profit = Decimal('0')
        self.total_loss = Decimal('0')
        self.trade_count = 0
        self.long_profit_count = 0
        self.long_loss_count = 0
        self.short_profit_count = 0
        self.short_loss_count = 0

        logger.info(f"双向持仓策略初始化: {symbol}")

    async def initialize(self):
        """初始化策略"""
        logger.info("开始初始化双向持仓策略...")

        # 检查仓位比例和杠杆倍数
        if self.position_ratio <= 0 or self.position_ratio > 1:
            raise ValueError(f"仓位比例必须在0-100%之间，当前: {self.position_ratio*100}%")

        if self.leverage < 1 or self.leverage > 125:
            raise ValueError(f"杠杆倍数必须在1-125之间，当前: {self.leverage}")

        # 获取账户余额
        await self._fetch_account_balance()

        # 计算ATR
        await self._update_atr()
        logger.info(f"当前ATR({self.atr_timeframe}, {self.atr_period}周期): {self.current_atr}")

        # 显示止盈止损配置
        logger.info(f"上涨触发: {self._get_threshold_desc('up')}")
        logger.info(f"下跌触发: {self._get_threshold_desc('down')}")
        logger.info(f"止损配置: {self._get_threshold_desc('stop_loss')}")

        logger.info(f"账户余额: {self.account_balance} USDT")
        logger.info(f"仓位比例: {self.position_ratio*100}%")
        logger.info(f"杠杆倍数: {self.leverage}x")

        logger.info("双向持仓策略初始化完成")

    def _get_threshold_desc(self, threshold_type: str) -> str:
        """
        获取阈值描述

        Args:
            threshold_type: 'up', 'down', 'stop_loss'

        Returns:
            阈值描述字符串
        """
        if threshold_type == 'up':
            if self.up_threshold_type == 'atr':
                return f"ATR × {self.up_atr_multiplier} (约 {self.current_atr * self.up_atr_multiplier:.2f})"
            else:
                return f"{self.up_threshold * 100}%"
        elif threshold_type == 'down':
            if self.down_threshold_type == 'atr':
                return f"ATR × {self.down_atr_multiplier} (约 {self.current_atr * self.down_atr_multiplier:.2f})"
            else:
                return f"{self.down_threshold * 100}%"
        elif threshold_type == 'stop_loss':
            if self.stop_loss_type == 'atr':
                return f"ATR × {self.stop_loss_atr_multiplier} (约 {self.current_atr * self.stop_loss_atr_multiplier:.2f})"
            else:
                return f"{self.stop_loss_ratio * 100}%"
        return "未知"

    async def _fetch_account_balance(self) -> Decimal:
        """
        获取账户USDT余额

        Returns:
            账户余额
        """
        try:
            balance = await self.exchange.fetch_balance()

            # 尝试获取USDT余额
            # 合约账户可能有不同的余额结构
            usdt_balance = Decimal('0')

            # 尝试直接获取
            if 'USDT' in balance:
                usdt_balance = Decimal(str(balance['USDT'].get('free', 0)))

            # 如果是合约账户，尝试获取总权益
            elif 'USDT' not in balance and 'info' in balance:
                # 合约账户通常在 info 字段中
                total_balance = balance.get('USDT', {}).get('total', 0)
                usdt_balance = Decimal(str(total_balance))

            # 如果余额为0，尝试从账户总余额获取
            if usdt_balance == 0 and 'USDT' in balance:
                usdt_balance = Decimal(str(balance['USDT'].get('total', 0)))

            self.account_balance = usdt_balance
            logger.info(f"账户余额查询成功: {usdt_balance} USDT")
            return usdt_balance
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            raise

    def _calculate_position_amount(self, current_price: Decimal) -> Decimal:
        """
        根据账户余额、仓位比例和杠杆倍数计算开仓数量

        公式: 开仓数量 = (账户余额 × 仓位比例 × 杠杆倍数) / 当前价格

        Args:
            current_price: 当前价格

        Returns:
            开仓数量
        """
        # 可用金额 = 账户余额 × 仓位比例
        available_amount = self.account_balance * self.position_ratio

        # 开仓金额 = 可用金额 × 杠杆倍数
        position_amount_usdt = available_amount * self.leverage

        # 开仓数量 = 开仓金额 / 当前价格
        position_amount = position_amount_usdt / current_price

        logger.info(f"开仓数量计算: 账户余额={self.account_balance}, 仓位比例={self.position_ratio*100}%, 杠杆={self.leverage}x, 当前价格={current_price}")
        logger.info(f"计算结果: 可用金额={available_amount:.2f}, 开仓金额={position_amount_usdt:.2f}, 开仓数量={position_amount:.6f}")

        return position_amount

    async def _update_atr(self):
        """计算并更新ATR值"""
        try:
            # 获取K线数据
            ohlcv = await self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.atr_timeframe,
                limit=self.atr_period + 1
            )

            # 计算True Range
            tr_list = []
            prev_close = None

            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                high = Decimal(str(high))
                low = Decimal(str(low))
                close = Decimal(str(close))

                if prev_close is not None:
                    # TR = max(H-L, |H-PC|, |L-PC|)
                    tr1 = high - low
                    tr2 = abs(high - prev_close)
                    tr3 = abs(low - prev_close)
                    tr = max(tr1, tr2, tr3)
                    tr_list.append(tr)

                prev_close = close

            # 计算ATR（简单移动平均）
            if tr_list:
                self.current_atr = sum(tr_list) / len(tr_list)
                logger.info(f"ATR更新成功: {self.current_atr:.8f}")
            else:
                logger.warning("ATR计算失败，使用默认值")
                self.current_atr = Decimal('0')

        except Exception as e:
            logger.error(f"计算ATR失败: {e}")
            self.current_atr = Decimal('0')

    async def open_initial_positions(self):
        """开启初始多空单"""
        logger.info("开始开启初始多空单...")

        # 取消所有现有挂单（清理环境）
        await self.cancel_all_orders()

        # 获取当前价格
        ticker = await self.exchange.fetch_ticker(self.symbol)
        current_price = Decimal(str(ticker['last']))
        logger.info(f"当前价格: {current_price}")

        # 开一个多单
        await self._open_long_position(current_price)

        # 开一个空单
        await self._open_short_position(current_price)

        logger.info(f"初始多空单开启完成: 多单 {len(self.long_positions)} 个, 空单 {len(self.short_positions)} 个")

    async def _open_long_position(self, price: Decimal):
        """
        开多单（U本位合约）

        Args:
            price: 当前价格（用于市价单）
        """
        try:
            # 计算开仓数量（基于账户余额、仓位比例和杠杆倍数）
            position_amount = self._calculate_position_amount(price)

            # U本位合约，使用 positionSide: 'LONG' 指定多单
            amount = float(position_amount)
            order = await self.exchange.create_market_buy_order(
                self.symbol,
                amount,
                params={'positionSide': 'LONG'}
            )

            # 记录多单信息
            long_position = {
                'order_id': order['id'],
                'entry_price': Decimal(str(order.get('average', order.get('price', price)))),
                'amount': position_amount,
                'entry_time': order['timestamp'],
                'is_open': True,
                'entry_atr': self.current_atr  # 记录开仓时的ATR
            }
            self.long_positions.append(long_position)

            logger.info(f"开多单成功: 价格 {long_position['entry_price']}, 数量 {long_position['amount']:.6f}")

        except Exception as e:
            logger.error(f"开多单失败: {e}")

    async def _open_short_position(self, price: Decimal):
        """
        开空单（U本位合约）

        Args:
            price: 当前价格（用于市价单）
        """
        try:
            # 计算开仓数量（基于账户余额、仓位比例和杠杆倍数）
            position_amount = self._calculate_position_amount(price)

            # U本位合约，做空不需要持有币种，使用 positionSide: 'SHORT' 指定空单
            amount = float(position_amount)
            order = await self.exchange.create_market_sell_order(
                self.symbol,
                amount,
                params={'positionSide': 'SHORT'}
            )

            # 记录空单信息
            short_position = {
                'order_id': order['id'],
                'entry_price': Decimal(str(order.get('average', order.get('price', price)))),
                'amount': position_amount,
                'entry_time': order['timestamp'],
                'is_open': True,
                'entry_atr': self.current_atr  # 记录开仓时的ATR
            }
            self.short_positions.append(short_position)

            logger.info(f"开空单成功: 价格 {short_position['entry_price']}, 数量 {short_position['amount']:.6f}")

        except Exception as e:
            logger.error(f"开空单失败: {e}")

    def _calculate_long_stop_loss(self, position: Dict) -> Decimal:
        """
        计算多单止损价格

        Args:
            position: 持仓信息

        Returns:
            止损价格
        """
        entry_price = position['entry_price']
        entry_atr = position.get('entry_atr', self.current_atr)

        if self.stop_loss_type == 'atr':
            # 基于ATR计算止损: 入场价 - ATR × 倍数
            stop_price = entry_price - (entry_atr * self.stop_loss_atr_multiplier)
        else:
            # 基于百分比计算止损
            stop_price = entry_price * (1 - self.stop_loss_ratio)

        return stop_price

    def _calculate_long_take_profit(self, position: Dict) -> Decimal:
        """
        计算多单止盈价格

        Args:
            position: 持仓信息

        Returns:
            止盈价格
        """
        entry_price = position['entry_price']
        entry_atr = position.get('entry_atr', self.current_atr)

        if self.up_threshold_type == 'atr':
            # 基于ATR计算止盈: 入场价 + ATR × 倍数
            tp_price = entry_price + (entry_atr * self.up_atr_multiplier)
        else:
            # 基于百分比计算止盈
            tp_price = entry_price * (1 + self.up_threshold)

        return tp_price

    def _calculate_short_stop_loss(self, position: Dict) -> Decimal:
        """
        计算空单止损价格

        Args:
            position: 持仓信息

        Returns:
            止损价格
        """
        entry_price = position['entry_price']
        entry_atr = position.get('entry_atr', self.current_atr)

        if self.stop_loss_type == 'atr':
            # 基于ATR计算止损: 入场价 + ATR × 倍数
            stop_price = entry_price + (entry_atr * self.stop_loss_atr_multiplier)
        else:
            # 基于百分比计算止损
            stop_price = entry_price * (1 + self.stop_loss_ratio)

        return stop_price

    def _calculate_short_take_profit(self, position: Dict) -> Decimal:
        """
        计算空单止盈价格

        Args:
            position: 持仓信息

        Returns:
            止盈价格
        """
        entry_price = position['entry_price']
        entry_atr = position.get('entry_atr', self.current_atr)

        if self.down_threshold_type == 'atr':
            # 基于ATR计算止盈: 入场价 - ATR × 倍数
            tp_price = entry_price - (entry_atr * self.down_atr_multiplier)
        else:
            # 基于百分比计算止盈
            tp_price = entry_price * (1 - self.down_threshold)

        return tp_price

    async def check_long_triggers(self, current_price: Decimal):
        """
        检查多单触发条件

        Args:
            current_price: 当前价格
        """
        for position in list(self.long_positions):
            if not position['is_open']:
                continue

            entry_price = position['entry_price']

            # 计算止盈价格
            tp_price = self._calculate_long_take_profit(position)

            # 计算止损价格
            sl_price = self._calculate_long_stop_loss(position)

            # 检查止盈
            if current_price >= tp_price:
                logger.info(f"多单止盈触发: 当前价格 {current_price} >= 止盈价格 {tp_price}")
                await self._close_long_position(position, current_price, reason="止盈")

                # 风险控制检查后重新开多单
                if self._check_risk_control_full():
                    await self._open_long_position(current_price)
                else:
                    logger.warning("风险控制触发，跳过重新开多单")
                continue

            # 检查止损
            if current_price <= sl_price:
                logger.info(f"多单止损触发: 当前价格 {current_price} <= 止损价格 {sl_price}")
                await self._close_long_position(position, current_price, reason="止损")

                # 风险控制检查后重新开多单
                if self._check_risk_control_full():
                    await self._open_long_position(current_price)
                else:
                    logger.warning("风险控制触发，跳过重新开多单")
                continue

    async def check_short_triggers(self, current_price: Decimal):
        """
        检查空单触发条件

        Args:
            current_price: 当前价格
        """
        for position in list(self.short_positions):
            if not position['is_open']:
                continue

            entry_price = position['entry_price']

            # 计算止盈价格（空单是价格下跌止盈）
            tp_price = self._calculate_short_take_profit(position)

            # 计算止损价格（空单是价格上涨止损）
            sl_price = self._calculate_short_stop_loss(position)

            # 检查止盈（价格下跌）
            if current_price <= tp_price:
                logger.info(f"空单止盈触发: 当前价格 {current_price} <= 止盈价格 {tp_price}")
                await self._close_short_position(position, current_price, reason="止盈")

                # 风险控制检查后重新开空单
                if self._check_risk_control_full():
                    await self._open_short_position(current_price)
                else:
                    logger.warning("风险控制触发，跳过重新开空单")
                continue

            # 检查止损（价格上涨）
            if current_price >= sl_price:
                logger.info(f"空单止损触发: 当前价格 {current_price} >= 止损价格 {sl_price}")
                await self._close_short_position(position, current_price, reason="止损")

                # 风险控制检查后重新开空单
                if self._check_risk_control_full():
                    await self._open_short_position(current_price)
                else:
                    logger.warning("风险控制触发，跳过重新开空单")
                continue

    async def _close_long_position(self, position: Dict, current_price: Decimal, reason: str = ""):
        """
        平多单（U本位合约）

        Args:
            position: 多单信息
            current_price: 当前价格
            reason: 平仓原因
        """
        try:
            position['is_open'] = False
            amount = float(position['amount'])

            # U本位合约，平多单使用 positionSide: 'LONG'
            order = await self.exchange.create_market_sell_order(
                self.symbol,
                amount,
                params={'positionSide': 'LONG', 'reduceOnly': True}
            )

            # 计算盈亏
            entry_price = position['entry_price']
            profit_amount = (current_price - entry_price) * position['amount']
            profit_ratio = (current_price - entry_price) / entry_price

            # 计算交易手续费（开仓+平仓，使用Taker费率0.04%作为保守估计）
            fee_rate = Decimal('0.0004')  # 0.04%
            position_value_usdt = position['amount'] * current_price
            total_fee_usdt = position_value_usdt * fee_rate * 2  # 开仓和平仓各一次

            # 计算净盈亏（扣除手续费）
            profit_amount_net = profit_amount - total_fee_usdt
            profit_ratio_net = (current_price - entry_price) / entry_price - (total_fee_usdt / position_value_usdt)

            # 更新统计
            self.trade_count += 1
            self.daily_trades += 1

            if profit_amount >= 0:
                self.total_profit += profit_amount_net
                self.long_profit_count += 1
                logger.info(
                    f"多单止盈: 入场 {entry_price}, 平仓 {current_price} | "
                    f"毛利润 {profit_amount:.4f} USDT ({profit_ratio*100:.2f}%) | "
                    f"手续费 {total_fee_usdt:.4f} USDT | "
                    f"净利润 {profit_amount_net:.4f} USDT ({profit_ratio_net*100:.2f}%)"
                )
            else:
                self.total_loss += abs(profit_amount_net)
                self.long_loss_count += 1
                self.update_daily_stats(abs(profit_amount_net))
                logger.warning(
                    f"多单止损: 入场 {entry_price}, 平仓 {current_price} | "
                    f"毛亏损 {abs(profit_amount):.4f} USDT ({profit_ratio*100:.2f}%) | "
                    f"手续费 {total_fee_usdt:.4f} USDT | "
                    f"净亏损 {abs(profit_amount_net):.4f} USDT ({profit_ratio_net*100:.2f}%)"
                )

            # 记录交易
            if self.trade_recorder:
                trade_data = {
                    'symbol': self.symbol,
                    'order_id': position['order_id'],
                    'close_order_id': order.get('id'),
                    'type': 'long',
                    'entry_price': float(entry_price),
                    'exit_price': float(current_price),
                    'amount': float(position['amount']),
                    'profit': float(profit_amount_net),  # 使用净利润
                    'profit_ratio': float(profit_ratio_net),  # 使用净利率
                    'reason': reason,
                    'timestamp': order.get('timestamp')
                }
                self.trade_recorder.record_trade(trade_data)

                # 广播交易更新到Web界面
                try:
                    from web.app import broadcast_trade_update
                    await broadcast_trade_update(trade_data)
                except Exception as e:
                    # Web模块可能未初始化，忽略错误
                    pass

            # 从持仓中移除
            if position in self.long_positions:
                self.long_positions.remove(position)

        except Exception as e:
            logger.error(f"平多单失败: {e}")

    async def _close_short_position(self, position: Dict, current_price: Decimal, reason: str = ""):
        """
        平空单（U本位合约）

        Args:
            position: 空单信息
            current_price: 当前价格
            reason: 平仓原因
        """
        try:
            position['is_open'] = False
            amount = float(position['amount'])

            # U本位合约，平空单使用 positionSide: 'SHORT'
            order = await self.exchange.create_market_buy_order(
                self.symbol,
                amount,
                params={'positionSide': 'SHORT', 'reduceOnly': True}
            )

            # 计算盈亏（空单是反的：高卖低买盈利）
            entry_price = position['entry_price']
            profit_amount = (entry_price - current_price) * position['amount']
            profit_ratio = (entry_price - current_price) / entry_price

            # 计算交易手续费（开仓+平仓，使用Taker费率0.04%作为保守估计）
            fee_rate = Decimal('0.0004')  # 0.04%
            position_value_usdt = position['amount'] * entry_price
            total_fee_usdt = position_value_usdt * fee_rate * 2  # 开仓和平仓各一次

            # 计算净盈亏（扣除手续费）
            profit_amount_net = profit_amount - total_fee_usdt
            profit_ratio_net = (entry_price - current_price) / entry_price - (total_fee_usdt / position_value_usdt)

            # 更新统计
            self.trade_count += 1
            self.daily_trades += 1

            if profit_amount >= 0:
                self.total_profit += profit_amount_net
                self.short_profit_count += 1
                logger.info(
                    f"空单止盈: 入场 {entry_price}, 平仓 {current_price} | "
                    f"毛利润 {profit_amount:.4f} USDT ({profit_ratio*100:.2f}%) | "
                    f"手续费 {total_fee_usdt:.4f} USDT | "
                    f"净利润 {profit_amount_net:.4f} USDT ({profit_ratio_net*100:.2f}%)"
                )
            else:
                self.total_loss += abs(profit_amount_net)
                self.short_loss_count += 1
                self.update_daily_stats(abs(profit_amount_net))
                logger.warning(
                    f"空单止损: 入场 {entry_price}, 平仓 {current_price} | "
                    f"毛亏损 {abs(profit_amount):.4f} USDT ({profit_ratio*100:.2f}%) | "
                    f"手续费 {total_fee_usdt:.4f} USDT | "
                    f"净亏损 {abs(profit_amount_net):.4f} USDT ({profit_ratio_net*100:.2f}%)"
                )

            # 记录交易
            if self.trade_recorder:
                trade_data = {
                    'symbol': self.symbol,
                    'order_id': position['order_id'],
                    'close_order_id': order.get('id'),
                    'type': 'short',
                    'entry_price': float(entry_price),
                    'exit_price': float(current_price),
                    'amount': float(position['amount']),
                    'profit': float(profit_amount_net),  # 使用净利润
                    'profit_ratio': float(profit_ratio_net),  # 使用净利率
                    'reason': reason,
                    'timestamp': order.get('timestamp')
                }
                self.trade_recorder.record_trade(trade_data)

                # 广播交易更新到Web界面
                try:
                    from web.app import broadcast_trade_update
                    await broadcast_trade_update(trade_data)
                except Exception as e:
                    # Web模块可能未初始化，忽略错误
                    pass

            # 从持仓中移除
            if position in self.short_positions:
                self.short_positions.remove(position)

        except Exception as e:
            logger.error(f"平空单失败: {e}")

    async def check_positions(self):
        """检查所有持仓触发条件"""
        # 更新ATR（每小时更新一次）
        await self._update_atr()

        # 风险控制检查（检查每日限制，但不检查持仓数量）
        if not self._check_risk_control_basic():
            logger.warning("风险控制触发，跳过交易")
            return

        # 获取当前价格
        ticker = await self.exchange.fetch_ticker(self.symbol)
        current_price = Decimal(str(ticker['last']))

        # 检查多单触发条件
        await self.check_long_triggers(current_price)

        # 检查空单触发条件
        await self.check_short_triggers(current_price)

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
        except Exception as e:
            logger.error(f"取消挂单失败: {e}")

    async def close_all_positions(self, current_price: Decimal):
        """
        平仓所有持仓

        Args:
            current_price: 当前价格
        """
        logger.info("平仓所有持仓...")

        # 平所有多单
        for position in list(self.long_positions):
            if position['is_open']:
                await self._close_long_position(position, current_price, reason="策略停止")

        # 平所有空单
        for position in list(self.short_positions):
            if position['is_open']:
                await self._close_short_position(position, current_price, reason="策略停止")

        logger.info("所有持仓已平仓")

    def _check_risk_control_basic(self) -> bool:
        """
        基础风险控制检查（只检查每日限制，不检查持仓数量）

        Returns:
            是否允许交易
        """
        # 检查是否暂停
        if self.is_paused:
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

    def _check_risk_control_full(self) -> bool:
        """
        完整风险控制检查（包括持仓数量）

        Returns:
            是否允许交易
        """
        # 先进行基础检查
        if not self._check_risk_control_basic():
            return False

        # 检查最大持仓数量
        total_positions = len(self.long_positions) + len(self.short_positions)
        if total_positions >= self.max_positions * 2:  # 乘2因为多空各算
            logger.warning(f"已达到最大持仓数量: {total_positions}/{self.max_positions * 2}")
            return False

        return True

    def update_daily_stats(self, loss: Decimal):
        """
        更新每日统计

        Args:
            loss: 亏损金额
        """
        if loss > 0:
            self.daily_loss += loss

    def reset_daily_stats(self):
        """重置每日统计"""
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
        current_price = Decimal(str(ticker['last']))

        # 计算当前持仓盈亏
        long_pnl = Decimal('0')
        for position in self.long_positions:
            if position['is_open']:
                long_pnl += (current_price - position['entry_price']) * position['amount']

        short_pnl = Decimal('0')
        for position in self.short_positions:
            if position['is_open']:
                short_pnl += (position['entry_price'] - current_price) * position['amount']

        total_pnl = long_pnl + short_pnl

        return {
            'symbol': self.symbol,
            'is_running': self.is_running,
            'current_price': float(current_price),
            'current_atr': float(self.current_atr),
            'positions': {
                'long_count': len([p for p in self.long_positions if p['is_open']]),
                'short_count': len([p for p in self.short_positions if p['is_open']]),
                'long_pnl': float(long_pnl),
                'short_pnl': float(short_pnl),
                'total_pnl': float(total_pnl)
            },
            'thresholds': {
                'up_threshold': self._get_threshold_desc('up'),
                'down_threshold': self._get_threshold_desc('down'),
                'stop_loss': self._get_threshold_desc('stop_loss')
            },
            'stats': {
                'total_trades': self.trade_count,
                'long_profit_count': self.long_profit_count,
                'long_loss_count': self.long_loss_count,
                'short_profit_count': self.short_profit_count,
                'short_loss_count': self.short_loss_count,
                'total_profit': float(self.total_profit),
                'total_loss': float(self.total_loss),
                'net_profit': float(self.total_profit - self.total_loss)
            },
            'daily': {
                'daily_loss': float(self.daily_loss),
                'daily_trades': self.daily_trades,
                'is_paused': self.is_paused
            },
            'risk_control': {
                'max_positions': self.max_positions,
                'max_daily_loss': float(self.max_daily_loss),
                'max_daily_trades': self.max_daily_trades
            }
        }

    async def start(self):
        """启动策略"""
        if self.is_running:
            logger.warning("策略已经在运行中")
            return

        logger.info("启动双向持仓策略...")
        self.is_running = True

        # 初始化
        await self.initialize()

        # 开启初始多空单
        await self.open_initial_positions()

        logger.info("双向持仓策略启动完成")

    async def stop(self):
        """停止策略"""
        if not self.is_running:
            return

        logger.info("停止双向持仓策略...")

        # 获取当前价格并平仓
        ticker = await self.exchange.fetch_ticker(self.symbol)
        current_price = Decimal(str(ticker['last']))
        await self.close_all_positions(current_price)

        self.is_running = False
        logger.info("双向持仓策略已停止")

    def get_positions_info(self) -> List[Dict]:
        """
        获取持仓详情

        Returns:
            持仓列表
        """
        positions = []

        # 多单信息
        for p in self.long_positions:
            if p['is_open']:
                positions.append({
                    'type': 'long',
                    'entry_price': float(p['entry_price']),
                    'amount': float(p['amount']),
                    'entry_time': p['entry_time']
                })

        # 空单信息
        for p in self.short_positions:
            if p['is_open']:
                positions.append({
                    'type': 'short',
                    'entry_price': float(p['entry_price']),
                    'amount': float(p['amount']),
                    'entry_time': p['entry_time']
                })

        return positions

    async def run_loop(self, check_interval: int = 5):
        """
        策略主循环

        Args:
            check_interval: 检查间隔（秒）
        """
        logger.info(f"策略主循环已启动，检查间隔: {check_interval}秒")

        try:
            while self.is_running:
                try:
                    # 显示策略状态
                    status = await self.get_status()
                    logger.info(
                        f"价格: {status['current_price']} | "
                        f"ATR: {status['current_atr']:.4f} | "
                        f"多单: {status['positions']['long_count']} | "
                        f"空单: {status['positions']['short_count']} | "
                        f"浮盈: {status['positions']['total_pnl']:.2f} | "
                        f"总交易: {status['stats']['total_trades']}"
                    )

                    # 显示详细的持仓信息（包括止盈止损价格）
                    self._log_position_details(status['current_price'])

                    # 检查持仓触发条件
                    await self.check_positions()

                    # 广播状态更新到Web界面
                    try:
                        from web.app import broadcast_status_update
                        await broadcast_status_update()
                    except Exception as e:
                        # Web模块可能未初始化，忽略错误
                        pass

                except Exception as e:
                    logger.error(f"主循环异常: {e}", exc_info=True)

                # 等待下一次检查
                await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("主循环已取消")

        logger.info("策略主循环已结束")

    def _log_position_details(self, current_price: Decimal):
        """
        记录详细的持仓信息（包括止盈止损价格）

        Args:
            current_price: 当前价格
        """
        # 多单详情
        for idx, position in enumerate(self.long_positions):
            if position['is_open']:
                tp_price = self._calculate_long_take_profit(position)
                sl_price = self._calculate_long_stop_loss(position)

                distance_to_tp = ((tp_price - current_price) / current_price) * 100
                distance_to_sl = ((current_price - sl_price) / current_price) * 100

                logger.info(
                    f"  多单{idx+1}: 入场={position['entry_price']} | "
                    f"止盈={tp_price} (+{distance_to_tp:.2f}%) | "
                    f"止损={sl_price} (-{distance_to_sl:.2f}%)"
                )

        # 空单详情
        for idx, position in enumerate(self.short_positions):
            if position['is_open']:
                tp_price = self._calculate_short_take_profit(position)
                sl_price = self._calculate_short_stop_loss(position)

                distance_to_tp = ((current_price - tp_price) / current_price) * 100
                distance_to_sl = ((sl_price - current_price) / current_price) * 100

                logger.info(
                    f"  空单{idx+1}: 入场={position['entry_price']} | "
                    f"止盈={tp_price} (-{distance_to_tp:.2f}%) | "
                    f"止损={sl_price} (+{distance_to_sl:.2f}%)"
                )
