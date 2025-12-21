<p align="center">
  <img src="https://github.com/jhao104/proxy_pool/blob/master/logo.png" alt="Proxy Pool Logo" width="128">
</p>

# Proxy Pool

[English](#english) | [中文](#chinese)

<div id="english"></div>

## 📖 Introduction

A high-performance Proxy Pool tailored for web spiders. It features a modern Vue 3 Dashboard, efficient Python async backend, and Redis storage.

Based on [jhao104/proxy_pool](https://github.com/jhao104/proxy_pool), enhanced with:
- **WebSocket**: Real-time stats push.
- **i18n**: English/Chinese support for Dashboard.
- **UI/UX**: Dark mode, improved layout.

## ✨ Features

- **Modern UI**: Vue 3 + Ant Design Vue 4.
- **High Performance**: Async Python fetchers & Redis.
- **Docker Ready**: Deployment in seconds.
- **Developer Friendly**: REST API & easy integration.

## 🛠 Deployment (Docker)

Recommended method.

```bash
# Clone
git clone https://github.com/yanqingjames951/proxy_pool.git
cd proxy_pool

# Start
docker-compose up -d
```

Access:
- **API**: `http://127.0.0.1:5010`
- **Dashboard**: `http://127.0.0.1:5011` (or configured port)

## 🔌 API Usage

After startup, API is available at `http://127.0.0.1:5010`.

| API | Method | Description | Params |
| --- | --- | --- | --- |
| `/` | GET | API Info | None |
| `/get` | GET | Get one random proxy | `?type=https` (optional) |
| `/pop` | GET | Get and delete one | `?type=https` (optional) |
| `/all` | GET | Get all proxies | `?type=https` (optional) |
| `/count` | GET | Get count | None |
| `/delete` | GET | Delete proxy | `?proxy=host:ip` |

## 🕷 Crawler Integration

Example python code to use the proxy pool:

```python
import requests

def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

# Usage in spider
def get_html():
    retry_count = 5
    proxy = get_proxy().get("proxy")
    while retry_count > 0:
        try:
            html = requests.get('http://www.example.com', proxies={"http": "http://{}".format(proxy)})
            return html
        except Exception:
            retry_count -= 1
    delete_proxy(proxy)
    return None
```

## 🧩 Extension

To add a custom proxy source:

1. Add a method in `fetcher/proxyFetcher.py`:
```python
class ProxyFetcher(object):
    @staticmethod
    def freeProxyCustom1():
        proxies = ["x.x.x.x:3128", "x.x.x.x:80"]
        for proxy in proxies:
            yield proxy
```

2. Enable it in `setting.py`:
```python
PROXY_FETCHER = [
    "freeProxy01",
    "freeProxyCustom1"
]
```

## 📋 Proxy Sources (2025-12-20)

| Source | Status |
| --- | --- |
| Kuaidaili | ✔ OK |
| YunProxy | ✔ OK |
| XiaoHuan | ✔ OK |
| 89Proxy | ✔ OK |
| ProxyScrape | ✔ OK |
| Spys.one | ✔ OK |
| UU-Proxy | ✔ OK |
| ProxyNova | ✔ OK |
| FreeProxy.world | ✔ OK |
| Free-Proxy-List | ✔ OK |

---

<div id="chinese"></div>

## 📖 简介 (Chinese)

一个基于 Python 的高性能代理池，专为爬虫设计。具备现代化的 Vue 3 仪表盘、异步后端和 Redis 存储。

本项目基于 [jhao104/proxy_pool](https://github.com/jhao104/proxy_pool) 开发，新增特性：
- **WebSocket**: 实时数据推送。
- **国际化**: 仪表盘支持中英文切换。
- **UI改进**: 适配暗黑模式与移动端。

## ✨ 特性

- **现代化 UI**: 采用 Vue 3 + Ant Design Vue 4.
- **高性能**: 异步 Python 抓取与 Redis 存储。
- **Docker 部署**: 一键启动。
- **开发者友好**: 完善的 API 文档与集成示例。

## 🛠 Docker 部署 (推荐)

```bash
# 克隆项目
git clone https://github.com/yanqingjames951/proxy_pool.git
cd proxy_pool

# 启动所有服务
docker compose up -d
```

服务访问:
- **API 服务**: `http://127.0.0.1:5010`
- **Web 仪表盘**: `http://127.0.0.1:5011` (具体端口请查看 docker-compose.yml 映射)

## 🔌 API 使用

启动后 API 服务默认地址: `http://127.0.0.1:5010`

| API | 方法 | 描述 | 参数 |
| --- | --- | --- | --- |
| `/` | GET | 接口介绍 | None |
| `/get` | GET | 随机获取一个代理 | `?type=https` (过滤 HTTPS) |
| `/pop` | GET | 获取并删除一个 | `?type=https` |
| `/all` | GET | 获取所有代理 | `?type=https` |
| `/count` | GET | 代理数量 | None |
| `/delete` | GET | 删除代理 | `?proxy=host:ip` |

## 🕷 爬虫使用示例

```python
import requests

def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

def get_html():
    retry_count = 5
    proxy = get_proxy().get("proxy")
    while retry_count > 0:
        try:
            html = requests.get('http://www.example.com', proxies={"http": "http://{}".format(proxy)})
            return html
        except Exception:
            retry_count -= 1
    delete_proxy(proxy)
    return None
```

## 🧩 扩展代理源

添加自定义抓取源:

1. 在 `fetcher/proxyFetcher.py` 中添加静态方法:
```python
class ProxyFetcher(object):
    @staticmethod
    def freeProxyCustom1():
        proxies = ["x.x.x.x:3128", "x.x.x.x:80"]
        for proxy in proxies:
            yield proxy
```

2. 在 `setting.py` 中注册:
```python
PROXY_FETCHER = [
    "freeProxy01",
    "freeProxyCustom1"
]
```

## 📋 免费代理源列表

目前支持的免费源 (2025-12-20 测试状态):

| 代理名称 | 状态 | 浏览器访问测试 | 更新速度 | 可用率 |
| --- | --- | --- | --- | --- |
| 快代理 | ✔ | ✔ 正常 | ★ | * |
| 云代理 | ✔ | ✔ 正常 | ★ | * |
| 小幻代理 | ✔ | ✔ 正常 | ★★ | * |
| 89代理 | ✔ | ✔ 正常 | ☆ | * |
| ProxyScrape | ✔ | ✔ 正常 | ★ | * |
| Spys.one | ✔ | ✔ 正常 | ★ | * |
| UU-Proxy | ✔ | ✔ 正常 | ★ | * |
| ProxyNova | ✔ | ✔ 正常 | ★ | * |
| FreeProxy.world | ✔ | ✔ 正常 | ★ | * |
| Free-Proxy-List | ✔ | ✔ 正常 | ★ | * |
