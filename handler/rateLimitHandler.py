# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     rateLimitHandler.py
   Description :   请求限流处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import time
from functools import wraps
from flask import request, jsonify
from redis import Redis
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler

log = LogHandler('ratelimit')


class RateLimitHandler:
    """请求限流管理"""
    
    def __init__(self):
        self.conf = ConfigHandler()
        self.minute_limit = getattr(self.conf, 'rateLimitPerMinute', 60)
        self.daily_limit = getattr(self.conf, 'rateLimitPerDay', 1000)
        self.enabled = getattr(self.conf, 'rateLimitEnabled', True)
        
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
    
    def _get_minute_key(self, user: str) -> str:
        minute = time.strftime("%Y%m%d%H%M")
        return f"rate_limit:minute:{user}:{minute}"
    
    def _get_daily_key(self, user: str) -> str:
        day = time.strftime("%Y%m%d")
        return f"rate_limit:daily:{user}:{day}"
    
    def check_limit(self, user: str) -> tuple:
        """
        检查是否超过限流
        返回: (是否允许, 限流信息)
        """
        if not self.enabled:
            return True, {"allowed": True}
        
        try:
            # 检查每分钟限流
            minute_key = self._get_minute_key(user)
            minute_count = self._conn.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0
            
            if self.minute_limit > 0 and minute_count >= self.minute_limit:
                return False, {
                    "allowed": False,
                    "reason": "minute_limit",
                    "limit": self.minute_limit,
                    "current": minute_count,
                    "retry_after": 60 - int(time.time()) % 60
                }
            
            # 检查每日限流
            daily_key = self._get_daily_key(user)
            daily_count = self._conn.get(daily_key)
            daily_count = int(daily_count) if daily_count else 0
            
            if self.daily_limit > 0 and daily_count >= self.daily_limit:
                now = time.localtime()
                seconds_until_midnight = (24 - now.tm_hour - 1) * 3600 + (60 - now.tm_min) * 60
                return False, {
                    "allowed": False,
                    "reason": "daily_limit",
                    "limit": self.daily_limit,
                    "current": daily_count,
                    "retry_after": seconds_until_midnight
                }
            
            return True, {
                "allowed": True,
                "minute_remaining": self.minute_limit - minute_count if self.minute_limit > 0 else -1,
                "daily_remaining": self.daily_limit - daily_count if self.daily_limit > 0 else -1
            }
        
        except Exception as e:
            log.error(f"Rate limit check failed: {e}")
            return True, {"allowed": True}
    
    def increment(self, user: str):
        """增加计数"""
        if not self.enabled:
            return
        
        try:
            minute_key = self._get_minute_key(user)
            self._conn.incr(minute_key)
            self._conn.expire(minute_key, 60)
            
            daily_key = self._get_daily_key(user)
            self._conn.incr(daily_key)
            self._conn.expire(daily_key, 86400)
        
        except Exception as e:
            log.error(f"Rate limit increment failed: {e}")
    
    def get_user_quota(self, user: str) -> dict:
        """获取用户配额信息"""
        try:
            minute_key = self._get_minute_key(user)
            minute_count = self._conn.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0
            
            daily_key = self._get_daily_key(user)
            daily_count = self._conn.get(daily_key)
            daily_count = int(daily_count) if daily_count else 0
            
            return {
                "minute": {
                    "limit": self.minute_limit,
                    "used": minute_count,
                    "remaining": max(0, self.minute_limit - minute_count) if self.minute_limit > 0 else -1
                },
                "daily": {
                    "limit": self.daily_limit,
                    "used": daily_count,
                    "remaining": max(0, self.daily_limit - daily_count) if self.daily_limit > 0 else -1
                }
            }
        except Exception as e:
            log.error(f"Get quota failed: {e}")
            return {"error": str(e)}


def rate_limit(f):
    """限流装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        rate_limiter = RateLimitHandler()
        
        user = "anonymous"
        if hasattr(request, 'user') and request.user:
            user = request.user.get("name", "anonymous")
        elif request.remote_addr:
            user = request.remote_addr
        
        allowed, info = rate_limiter.check_limit(user)
        
        if not allowed:
            response = jsonify({
                "code": 429,
                "message": "Too many requests",
                "detail": info
            })
            response.status_code = 429
            response.headers["Retry-After"] = str(info.get("retry_after", 60))
            return response
        
        result = f(*args, **kwargs)
        rate_limiter.increment(user)
        
        return result
    
    return decorated_function
