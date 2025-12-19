# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     websocketHandler.py
   Description :   WebSocket 实时推送处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import json
import time
import threading
from flask import Flask
from flask_sock import Sock
from handler.logHandler import LogHandler
from handler.proxyHandler import ProxyHandler

log = LogHandler('websocket')


class WebSocketHandler:
    """WebSocket 实时推送管理"""
    
    def __init__(self, app: Flask = None):
        self.sock = None
        self.clients = set()
        self.proxy_handler = ProxyHandler()
        self.broadcast_interval = 5  # 广播间隔（秒）
        self.is_running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化 Flask 应用"""
        self.sock = Sock(app)
        self._register_routes()
        log.info("WebSocket handler initialized")
    
    def _register_routes(self):
        """注册 WebSocket 路由"""
        
        @self.sock.route('/ws/stats')
        def stats_handler(ws):
            """代理池状态实时推送"""
            self.clients.add(ws)
            log.info(f"WebSocket client connected. Total clients: {len(self.clients)}")
            
            try:
                # 发送初始状态
                self._send_stats(ws)
                
                # 保持连接并接收消息
                while True:
                    try:
                        message = ws.receive(timeout=1)
                        if message:
                            data = json.loads(message)
                            self._handle_message(ws, data)
                    except TimeoutError:
                        # 定期发送心跳
                        ws.send(json.dumps({"type": "ping", "time": time.time()}))
                    except Exception as e:
                        if "Connection closed" in str(e) or "WebSocket" in str(e):
                            break
                        log.error(f"WebSocket receive error: {e}")
                        break
            finally:
                self.clients.discard(ws)
                log.info(f"WebSocket client disconnected. Total clients: {len(self.clients)}")
    
    def _send_stats(self, ws):
        """发送当前统计数据"""
        try:
            stats = self.proxy_handler.getCount()
            message = {
                "type": "stats",
                "data": stats,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            ws.send(json.dumps(message))
        except Exception as e:
            log.error(f"Failed to send stats: {e}")
    
    def _handle_message(self, ws, data: dict):
        """处理客户端消息"""
        msg_type = data.get("type", "")
        
        if msg_type == "subscribe":
            # 订阅特定事件
            events = data.get("events", [])
            log.info(f"Client subscribed to events: {events}")
            ws.send(json.dumps({"type": "subscribed", "events": events}))
            
        elif msg_type == "get_stats":
            # 请求当前统计
            self._send_stats(ws)
            
        elif msg_type == "pong":
            # 心跳响应
            pass
    
    def broadcast(self, message: dict):
        """向所有客户端广播消息"""
        if not self.clients:
            return
            
        data = json.dumps(message)
        dead_clients = set()
        
        for client in self.clients:
            try:
                client.send(data)
            except Exception as e:
                log.debug(f"Failed to send to client: {e}")
                dead_clients.add(client)
        
        # 移除断开的客户端
        self.clients -= dead_clients
    
    def broadcast_stats(self):
        """广播当前统计数据"""
        try:
            stats = self.proxy_handler.getCount()
            self.broadcast({
                "type": "stats",
                "data": stats,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            log.error(f"Failed to broadcast stats: {e}")
    
    def broadcast_event(self, event_type: str, data: dict):
        """广播事件"""
        self.broadcast({
            "type": "event",
            "event": event_type,
            "data": data,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def start_broadcaster(self, interval: int = 5):
        """启动定时广播器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.broadcast_interval = interval
        
        def broadcaster_loop():
            while self.is_running:
                self.broadcast_stats()
                time.sleep(self.broadcast_interval)
        
        thread = threading.Thread(target=broadcaster_loop, daemon=True)
        thread.start()
        log.info(f"WebSocket broadcaster started, interval: {interval}s")
    
    def stop_broadcaster(self):
        """停止广播器"""
        self.is_running = False
        log.info("WebSocket broadcaster stopped")
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.clients)


# 创建单例
ws_handler = WebSocketHandler()
