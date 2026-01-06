"""
币安交易所连接模块 - 使用真实API
"""
import ccxt.async_support as ccxt
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class BinanceExchange:
    """币安合约交易封装类"""

    def __init__(self, api_key: str, secret: str, testnet: bool = False):
        """
        初始化币安交易所连接（只支持合约交易）

        Args:
            api_key: API Key
            secret: API Secret
            testnet: 是否使用测试网络
        """
        self.api_key = api_key
        self.secret = secret
        self.testnet = testnet

        # 初始化CCXT异步实例（强制使用合约交易）
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,  # 启用速率限制
            'options': {
                'defaultType': 'future',  # 合约交易
                'dualPositionMode': True,  # 双向持仓模式
            }
        })

        if testnet:
            # 使用测试网络
            self.exchange.set_sandbox_mode(True)
            logger.info("使用币安测试网络")

        logger.info("币安合约交易连接初始化成功（双向持仓模式）")

    async def close(self):
        """关闭交易所连接"""
        try:
            await self.exchange.close()
            logger.info("交易所连接已关闭")
        except Exception as e:
            logger.error(f"关闭交易所连接失败: {e}")

    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 获取账户信息测试连接
            await self.exchange.fetch_balance()
            logger.info("币安连接测试成功")
            return True
        except Exception as e:
            logger.error(f"币安连接测试失败: {e}")
            return False

    async def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额

        Returns:
            余额信息字典
        """
        try:
            balance = await self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            raise

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取交易对行情

        Args:
            symbol: 交易对符号，如 BTC/USDT

        Returns:
            行情信息
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            raise

    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取订单簿

        Args:
            symbol: 交易对符号
            limit: 深度限制

        Returns:
            订单簿数据
        """
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            logger.error(f"获取订单簿失败 {symbol}: {e}")
            raise

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建订单

        Args:
            symbol: 交易对符号
            order_type: 订单类型 (market, limit)
            side: 方向 (buy, sell)
            amount: 数量
            price: 价格 (限价单必填)
            params: 额外参数

        Returns:
            订单信息
        """
        try:
            if order_type == 'market':
                order = await self.exchange.create_market_order(symbol, side, amount)
            elif order_type == 'limit':
                if price is None:
                    raise ValueError("限价单必须指定价格")
                order = await self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                raise ValueError(f"不支持的订单类型: {order_type}")

            logger.info(f"订单创建成功: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        撤销订单

        Args:
            order_id: 订单ID
            symbol: 交易对符号

        Returns:
            是否成功
        """
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"订单撤销成功: {order_id}")
            return True
        except Exception as e:
            logger.error(f"撤销订单失败: {e}")
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取挂单

        Args:
            symbol: 交易对符号，不指定则获取全部

        Returns:
            挂单列表
        """
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"获取挂单失败: {e}")
            raise

    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓信息（现货使用余额代替）

        Args:
            symbol: 交易对符号

        Returns:
            持仓信息
        """
        try:
            # 现货交易没有持仓概念，返回对应币种余额
            base_currency = symbol.split('/')[0]
            balance = await self.exchange.fetch_balance()
            position = {
                'symbol': symbol,
                'amount': balance.get(base_currency, {}).get('total', 0),
                'free': balance.get(base_currency, {}).get('free', 0),
                'used': balance.get(base_currency, {}).get('used', 0)
            }
            return position
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        try:
            await self.exchange.close()
            logger.info("币安交易所连接已关闭")
        except Exception as e:
            logger.error(f"关闭连接失败: {e}")
