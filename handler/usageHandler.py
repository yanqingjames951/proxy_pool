# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     usageHandler.py
   Description :   使用日志与统计处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import json
import time
from datetime import datetime, timedelta
from redis import Redis
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler

log = LogHandler('usage')


class UsageHandler:
    """使用日志与统计管理"""
    
    def __init__(self):
        self.conf = ConfigHandler()
        self.log_key = "proxy_usage_logs"
        self.stats_prefix = "proxy_stats:"
        self.max_logs = 10000
        self.retention_days = 7
        
        # 直接连接 Redis
        from urllib.parse import urlparse
        db_conf = urlparse(self.conf.dbConn)
        self._conn = Redis(
            host=db_conf.hostname or 'localhost',
            port=db_conf.port or 6379,
            password=db_conf.password if db_conf.password else None,
            db=int(db_conf.path[1:]) if db_conf.path and len(db_conf.path) > 1 else 0,
            decode_responses=True
        )
    
    def log_usage(self, user: str, action: str, proxy: str = "", extra: dict = None):
        """记录使用日志"""
        log_entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user": user,
            "action": action,
            "proxy": proxy,
        }
        if extra:
            log_entry.update(extra)
        
        try:
            self._conn.lpush(self.log_key, json.dumps(log_entry))
            self._conn.ltrim(self.log_key, 0, self.max_logs - 1)
        except Exception as e:
            log.error(f"Failed to log usage: {e}")
        
        self._update_daily_stats(user, action)
    
    def _update_daily_stats(self, user: str, action: str):
        """更新每日统计"""
        today = time.strftime("%Y-%m-%d")
        stats_key = f"{self.stats_prefix}{today}"
        
        try:
            self._conn.hincrby(stats_key, f"user:{user}", 1)
            self._conn.hincrby(stats_key, f"action:{action}", 1)
            self._conn.hincrby(stats_key, "total", 1)
            self._conn.expire(stats_key, self.retention_days * 86400)
        except Exception as e:
            log.error(f"Failed to update stats: {e}")
    
    def get_recent_logs(self, limit: int = 100, user: str = None) -> list:
        """获取最近的日志"""
        try:
            logs = self._conn.lrange(self.log_key, 0, limit - 1)
            result = [json.loads(log_item) for log_item in logs]
            
            if user:
                result = [item for item in result if item.get("user") == user]
            
            return result
        except Exception as e:
            log.error(f"Failed to get logs: {e}")
            return []
    
    def get_daily_stats(self, date: str = None) -> dict:
        """获取指定日期的统计"""
        if not date:
            date = time.strftime("%Y-%m-%d")
        
        stats_key = f"{self.stats_prefix}{date}"
        
        try:
            raw_stats = self._conn.hgetall(stats_key)
            
            users = {}
            actions = {}
            total = 0
            
            for key, value in raw_stats.items():
                if key.startswith("user:"):
                    users[key[5:]] = int(value)
                elif key.startswith("action:"):
                    actions[key[7:]] = int(value)
                elif key == "total":
                    total = int(value)
            
            return {
                "date": date,
                "total": total,
                "users": users,
                "actions": actions
            }
        except Exception as e:
            log.error(f"Failed to get daily stats: {e}")
            return {"date": date, "total": 0, "users": {}, "actions": {}}
    
    def get_stats_range(self, days: int = 7) -> list:
        """获取最近 N 天的统计"""
        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.get_daily_stats(date)
            result.append(stats)
        return result
    
    def get_user_stats(self, user: str, days: int = 7) -> dict:
        """获取用户统计"""
        daily_counts = []
        total = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.get_daily_stats(date)
            count = stats.get("users", {}).get(user, 0)
            daily_counts.append({"date": date, "count": count})
            total += count
        
        return {
            "user": user,
            "total": total,
            "daily": daily_counts
        }
    
    def get_summary(self) -> dict:
        """获取使用摘要"""
        today_stats = self.get_daily_stats()
        week_stats = self.get_stats_range(7)
        
        week_total = sum(s.get("total", 0) for s in week_stats)
        active_users = set()
        for s in week_stats:
            active_users.update(s.get("users", {}).keys())
        
        return {
            "today": today_stats.get("total", 0),
            "week": week_total,
            "active_users": len(active_users),
            "top_users": sorted(
                today_stats.get("users", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
