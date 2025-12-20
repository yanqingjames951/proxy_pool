# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyApi.py
   Description :   WebApi
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/04: WebApi
                   2019/08/14: 集成Gunicorn启动方式
                   2020/06/23: 新增pop接口
                   2022/07/21: 更新count接口
                   2024/12/20: 新增仪表盘API接口
                   2024/12/20: 新增认证、限流、统计功能
-------------------------------------------------
"""
__author__ = 'JHao'

import time
import platform
from werkzeug.wrappers import Response
from flask import Flask, jsonify, request
from flask_cors import CORS

from util.six import iteritems
from helper.proxy import Proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler
from handler.authHandler import AuthHandler, require_auth, require_admin
from handler.usageHandler import UsageHandler
from handler.rateLimitHandler import RateLimitHandler, rate_limit

import setting

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend
conf = ConfigHandler()
proxy_handler = ProxyHandler()
auth_handler = AuthHandler()
usage_handler = UsageHandler()
rate_limit_handler = RateLimitHandler()


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

# 详细 API 文档
API_DOCS = {
    "info": {
        "title": "Proxy Pool API",
        "version": "2.4.0",
        "description": "代理池 API 服务，提供代理获取、管理、监控等功能"
    },
    "endpoints": [
        {
            "path": "/get/",
            "method": "GET",
            "summary": "获取单个代理",
            "params": [
                {"name": "type", "type": "string", "required": False, "desc": "协议类型: 'https' 或留空"}
            ],
            "response": {"proxy": "ip:port", "https": True, "score": 85, "latency": 450}
        },
        {
            "path": "/get_batch/",
            "method": "GET",
            "summary": "批量获取代理",
            "params": [
                {"name": "count", "type": "int", "required": False, "default": 10, "desc": "获取数量(最大100)"},
                {"name": "type", "type": "string", "required": False, "desc": "协议类型"},
                {"name": "region", "type": "string", "required": False, "desc": "地区过滤"}
            ],
            "response": {"code": 0, "count": 10, "proxies": []}
        },
        {
            "path": "/pop/",
            "method": "GET",
            "summary": "获取并删除一个代理",
            "params": [{"name": "type", "type": "string", "required": False, "desc": "协议类型"}],
            "response": {"proxy": "ip:port", "https": True}
        },
        {
            "path": "/export/",
            "method": "GET",
            "summary": "导出代理列表",
            "params": [
                {"name": "format", "type": "string", "required": False, "default": "txt", "desc": "格式: txt/json/csv"},
                {"name": "count", "type": "int", "required": False, "default": 100, "desc": "导出数量"},
                {"name": "type", "type": "string", "required": False, "desc": "协议类型"},
                {"name": "region", "type": "string", "required": False, "desc": "地区过滤"}
            ],
            "response": "file download"
        },
        {
            "path": "/all/",
            "method": "GET",
            "summary": "获取所有代理",
            "params": [{"name": "type", "type": "string", "required": False, "desc": "协议类型"}],
            "response": []
        },
        {
            "path": "/count/",
            "method": "GET",
            "summary": "获取代理统计",
            "params": [],
            "response": {"count": 1000, "http_type": {}, "source": {}, "region": {}}
        },
        {
            "path": "/delete/",
            "method": "GET",
            "summary": "删除指定代理",
            "params": [{"name": "proxy", "type": "string", "required": True, "desc": "代理地址 ip:port"}],
            "response": {"code": 0, "src": "success"}
        },
        {
            "path": "/health/",
            "method": "GET",
            "summary": "健康检查",
            "params": [],
            "response": {"status": "ok", "redis": "connected", "proxy_count": 1000}
        },
        {
            "path": "/metrics/",
            "method": "GET",
            "summary": "Prometheus 指标",
            "params": [],
            "response": "prometheus text format"
        },
        {
            "path": "/api/proxies/",
            "method": "GET",
            "summary": "分页查询代理",
            "auth": True,
            "params": [
                {"name": "page", "type": "int", "required": False, "default": 1, "desc": "页码"},
                {"name": "size", "type": "int", "required": False, "default": 20, "desc": "每页数量"},
                {"name": "https", "type": "string", "required": False, "desc": "过滤 HTTPS"},
                {"name": "region", "type": "string", "required": False, "desc": "地区过滤"},
                {"name": "source", "type": "string", "required": False, "desc": "来源过滤"},
                {"name": "sort", "type": "string", "required": False, "default": "latency", "desc": "排序字段"},
                {"name": "order", "type": "string", "required": False, "default": "asc", "desc": "排序方向"}
            ],
            "response": {"data": [], "total": 1000, "page": 1, "size": 20, "pages": 50}
        },
        {
            "path": "/api/auth/login/",
            "method": "POST",
            "summary": "验证 API Key",
            "params": [{"name": "api_key", "type": "string", "required": True, "desc": "API Key", "in": "body"}],
            "response": {"code": 0, "user": {"name": "admin", "role": "admin"}}
        },
        {
            "path": "/api/auth/keys/",
            "method": "GET",
            "summary": "获取所有 API Keys (管理员)",
            "auth": "admin",
            "params": [],
            "response": {"code": 0, "keys": []}
        },
        {
            "path": "/api/auth/keys/",
            "method": "POST",
            "summary": "创建 API Key (管理员)",
            "auth": "admin",
            "params": [
                {"name": "name", "type": "string", "required": True, "desc": "用户名", "in": "body"},
                {"name": "role", "type": "string", "required": False, "default": "user", "desc": "角色", "in": "body"}
            ],
            "response": {"code": 0, "api_key": "xxx"}
        },
        {
            "path": "/api/usage/logs/",
            "method": "GET",
            "summary": "获取使用日志",
            "auth": True,
            "params": [{"name": "limit", "type": "int", "required": False, "default": 100, "desc": "记录数量"}],
            "response": {"code": 0, "logs": []}
        },
        {
            "path": "/api/usage/stats/",
            "method": "GET",
            "summary": "获取使用统计",
            "auth": True,
            "params": [],
            "response": {"code": 0, "stats": {}}
        },
        {
            "path": "/api/alerts/",
            "method": "GET",
            "summary": "获取告警历史",
            "auth": "admin",
            "params": [{"name": "limit", "type": "int", "required": False, "default": 20, "desc": "记录数量"}],
            "response": {"code": 0, "alerts": []}
        }
    ]
}

# 简化列表用于首页
api_list = [{"url": e["path"], "method": e["method"], "desc": e["summary"]} for e in API_DOCS["endpoints"]]


@app.route('/')
def index():
    return {'url': api_list}


@app.route('/docs/')
def docs():
    """完整 API 文档"""
    return API_DOCS


@app.route('/get/')
@rate_limit
def get():
    https = request.args.get("type", "").lower() == 'https'
    proxy = proxy_handler.get(https)
    # 记录使用日志
    user = getattr(request, 'user', {}).get('name', 'anonymous')
    if proxy:
        usage_handler.log_usage(user, 'get', proxy.proxy)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/get_batch/')
@rate_limit
def getBatch():
    """批量获取代理"""
    count = int(request.args.get("count", 10))
    https = request.args.get("type", "").lower() == 'https'
    region = request.args.get("region", "")
    
    proxies = proxy_handler.getBatch(count, https, region if region else None)
    
    # 记录使用日志
    user = getattr(request, 'user', {}).get('name', 'anonymous')
    usage_handler.log_usage(user, 'get_batch', f"count={len(proxies)}")
    
    return {
        "code": 0,
        "count": len(proxies),
        "proxies": [p.to_dict for p in proxies]
    }


@app.route('/export/')
def export():
    """导出代理列表"""
    fmt = request.args.get("format", "txt").lower()
    https = request.args.get("type", "").lower() == 'https'
    region = request.args.get("region", "")
    count = int(request.args.get("count", 100))
    
    proxies = proxy_handler.getBatch(count, https, region if region else None)
    
    # 记录使用日志
    user = getattr(request, 'user', {}).get('name', 'anonymous')
    usage_handler.log_usage(user, 'export', f"format={fmt},count={len(proxies)}")
    
    if fmt == "json":
        return jsonify([p.to_dict for p in proxies])
    
    elif fmt == "csv":
        lines = ["proxy,https,region,latency,source"]
        for p in proxies:
            lines.append(f"{p.proxy},{p.https},{p.region or ''},{p.latency},{p.source}")
        response = app.response_class(
            response="\n".join(lines),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=proxies.csv"}
        )
        return response
    
    else:  # txt
        lines = [p.proxy for p in proxies]
        response = app.response_class(
            response="\n".join(lines),
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment;filename=proxies.txt"}
        )
        return response


@app.route('/pop/')
@rate_limit
def pop():
    https = request.args.get("type", "").lower() == 'https'
    proxy = proxy_handler.pop(https)
    # 记录使用日志
    user = getattr(request, 'user', {}).get('name', 'anonymous')
    if proxy:
        usage_handler.log_usage(user, 'pop', proxy.proxy)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/refresh/')
def refresh():
    # TODO refresh会有守护程序定时执行，由api直接调用性能较差，暂不使用
    return 'success'


@app.route('/all/')
def getAll():
    https = request.args.get("type", "").lower() == 'https'
    proxies = proxy_handler.getAll(https)
    return jsonify([_.to_dict for _ in proxies])


@app.route('/delete/', methods=['GET'])
@require_admin
def delete():
    proxy = request.args.get('proxy')
    status = proxy_handler.delete(Proxy(proxy))
    return {"code": 0, "src": status}


@app.route('/count/')
def getCount():
    proxies = proxy_handler.getAll()
    http_type_dict = {}
    source_dict = {}
    region_dict = {}
    for proxy in proxies:
        http_type = 'https' if proxy.https else 'http'
        http_type_dict[http_type] = http_type_dict.get(http_type, 0) + 1
        for source in proxy.source.split('/'):
            source_dict[source] = source_dict.get(source, 0) + 1
        if proxy.region:
            region_dict[proxy.region] = region_dict.get(proxy.region, 0) + 1
    return {
        "http_type": http_type_dict,
        "source": source_dict,
        "region": region_dict,
        "count": len(proxies)
    }


# ============ Dashboard API Endpoints ============

@app.route('/api/proxies/')
@require_auth
def getProxiesPaginated():
    """Get paginated proxy list with filters and sorting"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    https_filter = request.args.get('https', '').lower()
    region_filter = request.args.get('region', '').lower()
    source_filter = request.args.get('source', '').lower()
    sort_by = request.args.get('sort', 'latency')  # latency, fail_count, check_count, last_time
    sort_order = request.args.get('order', 'asc')  # asc or desc
    
    # Get all proxies
    all_proxies = proxy_handler.getAll()
    
    # Apply filters
    filtered = all_proxies
    if https_filter == 'true':
        filtered = [p for p in filtered if p.https]
    elif https_filter == 'false':
        filtered = [p for p in filtered if not p.https]
    
    if region_filter:
        filtered = [p for p in filtered if region_filter in p.region.lower()]
    
    if source_filter:
        filtered = [p for p in filtered if source_filter in p.source.lower()]
    
    # Sort proxies
    reverse = sort_order == 'desc'
    if sort_by == 'latency':
        # Sort by latency, put 0 (no latency data) at the end
        filtered.sort(key=lambda p: (p.latency == 0, p.latency), reverse=reverse)
    elif sort_by == 'fail_count':
        filtered.sort(key=lambda p: p.fail_count, reverse=reverse)
    elif sort_by == 'check_count':
        filtered.sort(key=lambda p: p.check_count, reverse=reverse)
    elif sort_by == 'last_time':
        filtered.sort(key=lambda p: p.last_time or '', reverse=reverse)
    
    # Pagination
    total = len(filtered)
    start = (page - 1) * size
    end = start + size
    paginated = filtered[start:end]
    
    return {
        "data": [p.to_dict for p in paginated],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@app.route('/api/delete_batch/', methods=['POST'])
@require_admin
def deleteBatch():
    """Batch delete proxies"""
    data = request.get_json() or {}
    proxies = data.get('proxies', [])
    if not proxies:
        return {"code": 1, "message": "No proxies specified"}
    
    deleted = 0
    for proxy_str in proxies:
        try:
            proxy_handler.delete(Proxy(proxy_str))
            deleted += 1
        except:
            pass
    
    return {"code": 0, "message": f"Deleted {deleted} proxies", "deleted": deleted}


@app.route('/api/test/', methods=['GET', 'POST'])
def testProxy():
    """Test a proxy against a URL"""
    import requests as req
    
    if request.method == 'POST':
        data = request.get_json() or {}
        proxy_str = data.get('proxy', '')
        test_url = data.get('url', 'http://httpbin.org/ip')
    else:
        proxy_str = request.args.get('proxy', '')
        test_url = request.args.get('url', 'http://httpbin.org/ip')
    
    if not proxy_str:
        return {"code": 1, "message": "No proxy specified"}
    
    proxies = {
        "http": f"http://{proxy_str}",
        "https": f"http://{proxy_str}"
    }
    
    start_time = time.time()
    try:
        resp = req.get(test_url, proxies=proxies, timeout=10)
        latency = round((time.time() - start_time) * 1000)
        return {
            "code": 0,
            "success": True,
            "status_code": resp.status_code,
            "latency_ms": latency,
            "content": resp.text[:500] if resp.text else ""
        }
    except Exception as e:
        latency = round((time.time() - start_time) * 1000)
        return {
            "code": 0,
            "success": False,
            "error": str(e),
            "latency_ms": latency
        }


@app.route('/api/sources/')
def getSources():
    """Get statistics by source"""
    proxies = proxy_handler.getAll()
    source_stats = {}
    
    for proxy in proxies:
        for source in proxy.source.split('/'):
            if source not in source_stats:
                source_stats[source] = {
                    "name": source,
                    "total": 0,
                    "https": 0,
                    "http": 0,
                    "regions": {}
                }
            source_stats[source]["total"] += 1
            if proxy.https:
                source_stats[source]["https"] += 1
            else:
                source_stats[source]["http"] += 1
            if proxy.region:
                regions = source_stats[source]["regions"]
                regions[proxy.region] = regions.get(proxy.region, 0) + 1
    
    return {"sources": list(source_stats.values()), "total_sources": len(source_stats)}


@app.route('/api/config/')
def getConfig():
    """Get system configuration (read-only)"""
    return {
        "server_host": conf.serverHost,
        "server_port": conf.serverPort,
        "http_url": conf.httpUrl,
        "https_url": conf.httpsUrl,
        "verify_timeout": conf.verifyTimeout,
        "max_fail_count": conf.maxFailCount,
        "pool_size_min": conf.poolSizeMin,
        "proxy_region": conf.proxyRegion,
        "fetchers": conf.fetchers
    }


# ============ Health & Monitoring Endpoints ============

@app.route('/health/')
def health():
    """健康检查接口"""
    import os
    start_time = getattr(app, '_start_time', time.time())
    
    # 检查 Redis 连接
    redis_status = "connected"
    try:
        proxy_handler.getCount()
    except:
        redis_status = "disconnected"
    
    return {
        "status": "ok" if redis_status == "connected" else "degraded",
        "version": setting.VERSION,
        "uptime": int(time.time() - start_time),
        "redis": redis_status,
        "proxy_count": proxy_handler.getCount() if redis_status == "connected" else 0,
        "auth_enabled": setting.AUTH_ENABLED,
        "rate_limit_enabled": setting.RATE_LIMIT_ENABLED
    }


@app.route('/metrics/')
def metrics():
    """Prometheus 指标端点"""
    try:
        proxies = proxy_handler.getAll()
        
        # 统计数据
        total_count = len(proxies)
        https_count = sum(1 for p in proxies if p.https)
        http_count = total_count - https_count
        
        # 延迟分布
        latency_fast = sum(1 for p in proxies if 0 < p.latency < 500)
        latency_medium = sum(1 for p in proxies if 500 <= p.latency < 1000)
        latency_slow = sum(1 for p in proxies if p.latency >= 1000)
        
        # 评分分布
        score_high = sum(1 for p in proxies if p.score >= 80)
        score_medium = sum(1 for p in proxies if 60 <= p.score < 80)
        score_low = sum(1 for p in proxies if p.score < 60)
        
        # 来源统计
        source_counts = {}
        for p in proxies:
            for src in p.source.split('/'):
                source_counts[src] = source_counts.get(src, 0) + 1
        
        # 平均延迟
        latencies = [p.latency for p in proxies if p.latency > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # 平均评分
        scores = [p.score for p in proxies]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 生成 Prometheus 格式输出
        lines = [
            "# HELP proxy_pool_total Total number of proxies in the pool",
            "# TYPE proxy_pool_total gauge",
            f"proxy_pool_total {total_count}",
            "",
            "# HELP proxy_pool_https Number of HTTPS proxies",
            "# TYPE proxy_pool_https gauge",
            f"proxy_pool_https {https_count}",
            "",
            "# HELP proxy_pool_http Number of HTTP proxies",
            "# TYPE proxy_pool_http gauge",
            f"proxy_pool_http {http_count}",
            "",
            "# HELP proxy_pool_latency_avg Average latency in milliseconds",
            "# TYPE proxy_pool_latency_avg gauge",
            f"proxy_pool_latency_avg {avg_latency:.2f}",
            "",
            "# HELP proxy_pool_score_avg Average quality score",
            "# TYPE proxy_pool_score_avg gauge",
            f"proxy_pool_score_avg {avg_score:.2f}",
            "",
            "# HELP proxy_pool_latency_bucket Proxies by latency bucket",
            "# TYPE proxy_pool_latency_bucket gauge",
            f'proxy_pool_latency_bucket{{bucket="fast"}} {latency_fast}',
            f'proxy_pool_latency_bucket{{bucket="medium"}} {latency_medium}',
            f'proxy_pool_latency_bucket{{bucket="slow"}} {latency_slow}',
            "",
            "# HELP proxy_pool_score_bucket Proxies by score bucket",
            "# TYPE proxy_pool_score_bucket gauge",
            f'proxy_pool_score_bucket{{bucket="high"}} {score_high}',
            f'proxy_pool_score_bucket{{bucket="medium"}} {score_medium}',
            f'proxy_pool_score_bucket{{bucket="low"}} {score_low}',
            "",
            "# HELP proxy_pool_source Proxies by source",
            "# TYPE proxy_pool_source gauge",
        ]
        
        for src, count in sorted(source_counts.items(), key=lambda x: -x[1])[:10]:
            lines.append(f'proxy_pool_source{{source="{src}"}} {count}')
        
        response = app.response_class(
            response="\n".join(lines) + "\n",
            mimetype="text/plain; charset=utf-8"
        )
        return response
        
    except Exception as e:
        return f"# Error: {e}\n", 500


# ============ Auth Management Endpoints ============

@app.route('/api/auth/login/', methods=['POST'])
def login():
    """验证 API Key 并返回用户信息"""
    data = request.get_json() or {}
    api_key = data.get('api_key', '')
    
    if not api_key:
        return {"code": 400, "message": "API Key required"}, 400
    
    user_info = auth_handler.validate_key(api_key)
    if not user_info:
        return {"code": 401, "message": "Invalid API Key"}, 401
    
    # 获取配额信息
    quota = rate_limit_handler.get_user_quota(user_info.get('name', 'anonymous'))
    
    return {
        "code": 0,
        "user": user_info,
        "quota": quota
    }


@app.route('/api/auth/keys/', methods=['GET'])
@require_admin
def listKeys():
    """列出所有 API Keys (仅管理员)"""
    keys = auth_handler.list_keys()
    return {"code": 0, "keys": keys}


@app.route('/api/auth/keys/', methods=['POST'])
@require_admin
def createKey():
    """创建新的 API Key (仅管理员)"""
    data = request.get_json() or {}
    name = data.get('name', '')
    role = data.get('role', 'user')
    
    if not name:
        return {"code": 400, "message": "Name required"}, 400
    
    if role not in ['user', 'admin']:
        return {"code": 400, "message": "Role must be 'user' or 'admin'"}, 400
    
    api_key = auth_handler.create_key(name, role)
    return {"code": 0, "api_key": api_key, "message": "API Key created successfully"}


@app.route('/api/auth/keys/<api_key>/', methods=['DELETE'])
@require_admin
def deleteKey(api_key):
    """删除 API Key (仅管理员)"""
    if auth_handler.delete_key(api_key):
        return {"code": 0, "message": "API Key deleted"}
    return {"code": 404, "message": "API Key not found"}, 404


# ============ Usage Statistics Endpoints ============

@app.route('/api/usage/logs/')
@require_auth
def getUsageLogs():
    """获取使用日志"""
    limit = int(request.args.get('limit', 100))
    user_filter = request.args.get('user', '')
    
    # 普通用户只能看自己的日志
    if request.user.get('role') != 'admin':
        user_filter = request.user.get('name')
    
    logs = usage_handler.get_recent_logs(limit, user_filter if user_filter else None)
    return {"code": 0, "logs": logs}


@app.route('/api/usage/stats/')
@require_auth
def getUsageStats():
    """获取使用统计"""
    days = int(request.args.get('days', 7))
    
    if request.user.get('role') == 'admin':
        # 管理员看全局统计
        stats = usage_handler.get_stats_range(days)
        summary = usage_handler.get_summary()
        return {"code": 0, "stats": stats, "summary": summary}
    else:
        # 普通用户看自己的统计
        user_stats = usage_handler.get_user_stats(request.user.get('name'), days)
        return {"code": 0, "stats": user_stats}


@app.route('/api/usage/quota/')
@require_auth
def getQuota():
    """获取当前用户配额"""
    user = request.user.get('name', 'anonymous')
    quota = rate_limit_handler.get_user_quota(user)
    return {"code": 0, "quota": quota}


# ============ Alert Management Endpoints ============

@app.route('/api/alerts/', methods=['GET'])
@require_admin
def getAlertHistory():
    """获取告警历史"""
    from handler.alertHandler import AlertHandler
    alert_handler = AlertHandler()
    limit = int(request.args.get('limit', 20))
    alerts = alert_handler.get_alert_history(limit)
    return {"code": 0, "alerts": alerts}


@app.route('/api/alerts/test/', methods=['POST'])
@require_admin
def sendTestAlert():
    """发送测试告警"""
    from handler.alertHandler import AlertHandler
    alert_handler = AlertHandler()
    alert_handler.send_test_alert()
    return {"code": 0, "message": "Test alert sent"}


@app.route('/api/alerts/check/', methods=['POST'])
@require_admin
def checkAlerts():
    """触发告警检查"""
    from handler.alertHandler import AlertHandler
    alert_handler = AlertHandler()
    triggered = alert_handler.check_and_alert()
    return {"code": 0, "triggered": triggered}


# ============ Cleanup Management Endpoints ============

@app.route('/api/cleanup/', methods=['GET'])
@require_admin
def getCleanupStats():
    """获取清理统计信息"""
    from handler.cleanupHandler import CleanupHandler
    cleanup_handler = CleanupHandler()
    stats = cleanup_handler.get_cleanup_stats()
    return {"code": 0, "stats": stats}


@app.route('/api/cleanup/', methods=['POST'])
@require_admin
def runCleanup():
    """执行清理操作"""
    from handler.cleanupHandler import CleanupHandler
    cleanup_handler = CleanupHandler()
    
    data = request.get_json() or {}
    cleanup_type = data.get('type', 'all')
    
    if cleanup_type == 'stale':
        max_age = data.get('max_age_hours', 72)
        result = {"stale": cleanup_handler.cleanup_stale_proxies(max_age)}
    elif cleanup_type == 'low_score':
        min_score = data.get('min_score', 30)
        result = {"low_score": cleanup_handler.cleanup_low_score_proxies(min_score)}
    elif cleanup_type == 'failed':
        max_fail = data.get('max_fail_count', 5)
        result = {"failed": cleanup_handler.cleanup_failed_proxies(max_fail)}
    else:
        result = cleanup_handler.run_full_cleanup()
    
    return {"code": 0, "result": result}


@app.route('/api/cleanup/start/', methods=['POST'])
@require_admin
def startCleanupScheduler():
    """启动自动清理调度器"""
    from handler.cleanupHandler import CleanupHandler
    cleanup_handler = CleanupHandler()
    
    data = request.get_json() or {}
    interval = data.get('interval_hours', 6)
    
    cleanup_handler.start_cleanup_scheduler(interval)
    return {"code": 0, "message": f"Cleanup scheduler started with {interval}h interval"}


def runFlask():
    if platform.system() == "Windows":
        app.run(host=conf.serverHost, port=conf.serverPort)
    else:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                _config = dict([(key, value) for key, value in iteritems(self.options)
                                if key in self.cfg.settings and value is not None])
                for key, value in iteritems(_config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        _options = {
            'bind': '%s:%s' % (conf.serverHost, conf.serverPort),
            'workers': 4,
            'accesslog': '-',  # log to stdout
            'access_log_format': '%(h)s %(l)s %(t)s "%(r)s" %(s)s "%(a)s"'
        }
        StandaloneApplication(app, _options).run()


if __name__ == '__main__':
    runFlask()
