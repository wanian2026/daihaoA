"""
Web管理界面 - FastAPI应用
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="币安双向持仓策略管理系统", version="1.0.0")

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量：存储策略实例
strategy_instance = None
trade_recorder = None
config_manager = None

# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """连接WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接成功，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")


manager = ConnectionManager()


def init_strategy(strategy, recorder, config_mgr):
    """
    初始化策略实例

    Args:
        strategy: 策略实例
        recorder: 交易记录器
        config_mgr: 配置管理器
    """
    global strategy_instance, trade_recorder, config_manager
    strategy_instance = strategy
    trade_recorder = recorder
    config_manager = config_mgr
    logger.info("Web管理界面初始化完成")


@app.get("/")
async def root():
    """主页 - 返回Web管理界面"""
    try:
        with open("src/web/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Web管理界面加载失败</h1><p>请确保 src/web/index.html 文件存在</p>")


@app.get("/api/status")
async def get_status():
    """获取策略状态"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        status = await strategy_instance.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    """获取持仓详情"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        positions = strategy_instance.get_positions_info()
        return {"success": True, "data": positions}
    except Exception as e:
        logger.error(f"获取持仓详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades")
async def get_trades(limit: int = 100):
    """获取交易历史"""
    if not trade_recorder:
        raise HTTPException(status_code=503, detail="交易记录器未初始化")

    try:
        trades = trade_recorder.get_recent_trades(limit)
        return {"success": True, "data": trades}
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    if not config_manager:
        raise HTTPException(status_code=503, detail="配置管理器未初始化")

    try:
        config = config_manager.config
        # 隐藏敏感信息
        safe_config = config.copy()
        if 'exchange' in safe_config:
            safe_config['exchange']['api_key'] = '***'
            safe_config['exchange']['secret'] = '***'
        return {"success": True, "data": safe_config}
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manual/long")
async def open_long_position():
    """手动开多单"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        # 获取当前价格
        from decimal import Decimal
        ticker = await strategy_instance.exchange.fetch_ticker(strategy_instance.symbol)
        current_price = Decimal(str(ticker['last']))

        # 开多单
        await strategy_instance._open_long_position(current_price)

        return {"success": True, "message": "手动开多单成功"}
    except Exception as e:
        logger.error(f"手动开多单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manual/short")
async def open_short_position():
    """手动开空单"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        # 获取当前价格
        from decimal import Decimal
        ticker = await strategy_instance.exchange.fetch_ticker(strategy_instance.symbol)
        current_price = Decimal(str(ticker['last']))

        # 开空单
        await strategy_instance._open_short_position(current_price)

        return {"success": True, "message": "手动开空单成功"}
    except Exception as e:
        logger.error(f"手动开空单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/close/all")
async def close_all_positions():
    """平仓所有持仓"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        # 获取当前价格
        from decimal import Decimal
        ticker = await strategy_instance.exchange.fetch_ticker(strategy_instance.symbol)
        current_price = Decimal(str(ticker['last']))

        # 平所有持仓
        await strategy_instance.close_all_positions(current_price)

        return {"success": True, "message": "平仓所有持仓成功"}
    except Exception as e:
        logger.error(f"平仓所有持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pause")
async def pause_strategy():
    """暂停策略"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        strategy_instance.is_paused = True
        return {"success": True, "message": "策略已暂停"}
    except Exception as e:
        logger.error(f"暂停策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resume")
async def resume_strategy():
    """恢复策略"""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="策略未初始化")

    try:
        strategy_instance.is_paused = False
        return {"success": True, "message": "策略已恢复"}
    except Exception as e:
        logger.error(f"恢复策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点 - 实时推送数据"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，等待客户端消息
            data = await websocket.receive_text()
            logger.info(f"收到WebSocket消息: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket)


async def broadcast_status_update():
    """广播策略状态更新"""
    if strategy_instance and manager.active_connections:
        try:
            status = await strategy_instance.get_status()
            message = {
                "type": "status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(message)
        except Exception as e:
            logger.error(f"广播状态更新失败: {e}")


async def broadcast_trade_update(trade_data: dict):
    """广播交易更新"""
    if manager.active_connections:
        try:
            message = {
                "type": "trade_update",
                "data": trade_data,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(message)
        except Exception as e:
            logger.error(f"广播交易更新失败: {e}")


async def broadcast_log(log_data: dict):
    """广播日志更新"""
    if manager.active_connections:
        try:
            message = {
                "type": "log_update",
                "data": log_data,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(message)
        except Exception as e:
            logger.error(f"广播日志更新失败: {e}")
