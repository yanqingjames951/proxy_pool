# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     authHandler.py
   Description :   API Key 认证处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import json
import time
import secrets
from typing import Optional
from functools import wraps
from flask import request, jsonify
from redis import Redis
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler

log = LogHandler('auth')


class AuthHandler:
    """API Key 认证管理"""
    
    def __init__(self):
        self.conf = ConfigHandler()
        self.key_prefix = "api_key:"
        self.enabled = getattr(self.conf, 'authEnabled', True)
        
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
    
    def _get_key_name(self, api_key: str) -> str:
        return f"{self.key_prefix}{api_key}"
    
    def create_key(self, name: str, role: str = "user") -> str:
        """创建新的 API Key"""
        api_key = secrets.token_urlsafe(32)
        key_data = {
            "name": name,
            "role": role,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_used": "",
            "usage_count": 0
        }
        self._conn.set(self._get_key_name(api_key), json.dumps(key_data))
        log.info(f"Created API key for {name} with role {role}")
        return api_key
    
    def validate_key(self, api_key: str) -> Optional[dict]:
        """验证 API Key，返回用户信息或 None"""
        if not api_key:
            return None
        
        key_data = self._conn.get(self._get_key_name(api_key))
        if key_data:
            data = json.loads(key_data)
            # 更新最后使用时间和使用次数
            data["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
            data["usage_count"] = data.get("usage_count", 0) + 1
            self._conn.set(self._get_key_name(api_key), json.dumps(data))
            return data
        return None
    
    def get_user_info(self, api_key: str) -> Optional[dict]:
        """获取用户信息（不更新使用计数）"""
        if not api_key:
            return None
        key_data = self._conn.get(self._get_key_name(api_key))
        if key_data:
            return json.loads(key_data)
        return None
    
    def list_keys(self) -> list:
        """列出所有 API Keys"""
        keys = []
        try:
            cursor = 0
            while True:
                cursor, key_list = self._conn.scan(cursor, match=f"{self.key_prefix}*", count=100)
                for key in key_list:
                    value = self._conn.get(key)
                    if value:
                        api_key = key[len(self.key_prefix):]
                        data = json.loads(value)
                        keys.append({
                            "key": api_key[:8] + "..." + api_key[-4:],
                            "full_key": api_key,
                            **data
                        })
                if cursor == 0:
                    break
        except Exception as e:
            log.error(f"Failed to list keys: {e}")
        return keys
    
    def delete_key(self, api_key: str) -> bool:
        """删除 API Key"""
        key_name = self._get_key_name(api_key)
        if self._conn.exists(key_name):
            self._conn.delete(key_name)
            log.info(f"Deleted API key: {api_key[:8]}...")
            return True
        return False
    
    def update_key(self, api_key: str, name: str = None, role: str = None) -> bool:
        """更新 API Key 信息"""
        key_data = self.get_user_info(api_key)
        if not key_data:
            return False
        
        if name:
            key_data["name"] = name
        if role:
            key_data["role"] = role
        
        self._conn.set(self._get_key_name(api_key), json.dumps(key_data))
        return True
    
    def init_admin_key(self) -> str:
        """初始化管理员 Key（首次启动时调用）"""
        # 检查是否已有 admin key
        existing_keys = self.list_keys()
        for key_info in existing_keys:
            if key_info.get("role") == "admin":
                return key_info.get("full_key")
        
        # 创建新的 admin key
        admin_key = self.create_key("Admin", "admin")
        log.info(f"Initialized admin API key: {admin_key}")
        return admin_key


# 认证装饰器
def require_auth(f):
    """需要认证的接口装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_handler = AuthHandler()
        
        # 如果认证被禁用，直接放行
        if not auth_handler.enabled:
            request.user = {"name": "anonymous", "role": "admin"}
            return f(*args, **kwargs)
        
        # 从请求头获取 API Key
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({"code": 401, "message": "API Key required"}), 401
        
        user_info = auth_handler.validate_key(api_key)
        if not user_info:
            return jsonify({"code": 401, "message": "Invalid API Key"}), 401
        
        # 将用户信息附加到 request
        request.user = user_info
        request.api_key = api_key
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """需要管理员权限的接口装饰器"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if request.user.get("role") != "admin":
            return jsonify({"code": 403, "message": "Admin permission required"}), 403
        return f(*args, **kwargs)
    
    return decorated_function
