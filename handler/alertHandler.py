# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     alertHandler.py
   Description :   告警通知处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import json
import time
import requests
from threading import Thread
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler
from handler.proxyHandler import ProxyHandler

log = LogHandler('alert')


class AlertHandler:
    """告警通知管理"""
    
    def __init__(self):
        self.conf = ConfigHandler()
        self.proxy_handler = ProxyHandler()
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5分钟冷却时间，避免频繁告警
        
    def check_and_alert(self):
        """检查代理池状态并发送告警"""
        try:
            count_info = self.proxy_handler.getCount()
            current_count = count_info.get('count', {}).get('total', 0)
            min_threshold = getattr(self.conf, 'poolSizeMin', 50)
            
            # 检查是否低于阈值
            if current_count < min_threshold:
                current_time = time.time()
                
                # 检查冷却时间
                if current_time - self.last_alert_time > self.alert_cooldown:
                    self.send_alert(
                        level="warning",
                        title="代理池数量不足",
                        message=f"当前代理数量 {current_count} 低于阈值 {min_threshold}",
                        details={
                            "current": current_count,
                            "threshold": min_threshold,
                            "time": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                    self.last_alert_time = current_time
                    return True
            return False
        except Exception as e:
            log.error(f"Alert check failed: {e}")
            return False
    
    def send_alert(self, level: str, title: str, message: str, details: dict = None):
        """
        发送告警通知
        支持多种通知方式: Webhook, 邮件等
        """
        log.warning(f"[ALERT] {level.upper()}: {title} - {message}")
        
        # 获取配置的 Webhook URL
        webhook_url = getattr(self.conf, 'alertWebhook', None)
        
        if webhook_url:
            Thread(target=self._send_webhook, args=(webhook_url, level, title, message, details)).start()
        
        # 记录告警历史
        self._log_alert(level, title, message, details)
    
    def _send_webhook(self, url: str, level: str, title: str, message: str, details: dict):
        """发送 Webhook 通知"""
        try:
            # 支持多种 Webhook 格式
            
            # 通用 JSON 格式
            payload = {
                "level": level,
                "title": title,
                "message": message,
                "details": details or {},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "proxy_pool"
            }
            
            # 检测是否是钉钉机器人
            if "dingtalk" in url or "oapi.dingtalk.com" in url:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": f"[{level.upper()}] {title}",
                        "text": f"## {title}\n\n**{message}**\n\n- 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n- 详情: {json.dumps(details, ensure_ascii=False) if details else '无'}"
                    }
                }
            
            # 检测是否是企业微信机器人
            elif "qyapi.weixin.qq.com" in url:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"## {title}\n**{message}**\n> 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
            
            # 检测是否是 Slack
            elif "hooks.slack.com" in url:
                payload = {
                    "text": f"*[{level.upper()}] {title}*\n{message}",
                    "attachments": [{
                        "color": "danger" if level == "critical" else "warning",
                        "fields": [
                            {"title": k, "value": str(v), "short": True}
                            for k, v in (details or {}).items()
                        ]
                    }]
                }
            
            # 检测是否是 Telegram Bot
            # 格式: https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>
            elif "api.telegram.org" in url:
                # 构建 Telegram 消息
                emoji = "🔴" if level == "critical" else "🟡" if level == "warning" else "🟢"
                text = f"{emoji} *[{level.upper()}] {title}*\n\n{message}\n\n"
                if details:
                    text += "📋 *详情:*\n"
                    for k, v in details.items():
                        text += f"  • {k}: `{v}`\n"
                text += f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                
                payload = {
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    log.info("Telegram alert sent successfully")
                else:
                    log.warning(f"Telegram returned status {response.status_code}: {response.text}")
                return
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                log.info(f"Webhook alert sent successfully")
            else:
                log.warning(f"Webhook returned status {response.status_code}")
                
        except Exception as e:
            log.error(f"Failed to send webhook: {e}")
    
    def _log_alert(self, level: str, title: str, message: str, details: dict):
        """记录告警历史到 Redis"""
        try:
            from redis import Redis
            from urllib.parse import urlparse
            
            db_conf = urlparse(self.conf.dbConn)
            conn = Redis(
                host=db_conf.hostname or 'localhost',
                port=db_conf.port or 6379,
                password=db_conf.password if db_conf.password else None,
                db=int(db_conf.path[1:]) if db_conf.path and len(db_conf.path) > 1 else 0,
                decode_responses=True
            )
            
            alert_data = {
                "level": level,
                "title": title,
                "message": message,
                "details": details,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            conn.lpush("proxy_alerts", json.dumps(alert_data))
            conn.ltrim("proxy_alerts", 0, 99)  # 保留最近100条
            
        except Exception as e:
            log.error(f"Failed to log alert: {e}")
    
    def get_alert_history(self, limit: int = 20) -> list:
        """获取告警历史"""
        try:
            from redis import Redis
            from urllib.parse import urlparse
            
            db_conf = urlparse(self.conf.dbConn)
            conn = Redis(
                host=db_conf.hostname or 'localhost',
                port=db_conf.port or 6379,
                password=db_conf.password if db_conf.password else None,
                db=int(db_conf.path[1:]) if db_conf.path and len(db_conf.path) > 1 else 0,
                decode_responses=True
            )
            
            alerts = conn.lrange("proxy_alerts", 0, limit - 1)
            return [json.loads(a) for a in alerts]
            
        except Exception as e:
            log.error(f"Failed to get alert history: {e}")
            return []
    
    def send_test_alert(self):
        """发送测试告警"""
        self.send_alert(
            level="info",
            title="测试告警",
            message="这是一条测试告警消息，用于验证告警配置是否正确",
            details={
                "type": "test",
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        return True


# 创建单例
alert_handler = AlertHandler()
