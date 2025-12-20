# ProxyPool 爬虫代理IP池

> 本项目基于 [jhao104/proxy_pool](https://github.com/jhao104/proxy_pool) 开发，在此基础上进行了大规模功能重构与增强。

**v2.4.0 新增功能** 🎉

- **现代化 Dashboard**: Vue 3 + Ant Design Vue 开发的实时监控面板
- **全方位监控**: 代理池健康状态、协议分布、地区分布、API 调用统计
- **企业级特性**: API Key 认证、请求限流、webhook 告警 (钉钉/企微/Slack/TG)
- **运维友好**: Docker Compose 一键部署、Kubernetes 支持、Prometheus 指标
- **质量保障**: 自动评分系统、自动清理过期/低分代理、延迟监控
- **多语言支持**: 🇨🇳 中文 / 🇺🇸 English 自由切换

---

## 🚀 快速启动

### 1. Docker Compose (推荐)

最快速的部署方式，包含 API、Dashboard 和 Redis。

```bash
# 克隆项目
git clone git@github.com:yanqingjames951/proxy_pool.git
cd proxy_pool

# 启动服务
docker compose up -d
```

服务启动后访问：
- **Web 仪表盘**: http://127.0.0.1:5011 (默认无需密码，建议配置 API Key)
- **API 地址**: http://127.0.0.1:5010
- **API 文档**: http://127.0.0.1:5010/docs/

### 2. Kubernetes 部署

```bash
kubectl apply -k k8s/
```

---

## 🛠 功能特性详解

### 1. 代理获取与管理

支持多种方式获取代理：

- **API 获取**: 
  - 随机获取: `GET /get/?type=https`
  - 批量获取: `GET /get_batch/?count=10&region=美国`
  - 导出代理: `GET /export/?format=txt` (支持 TXT/JSON/CSV)

- **自动维护**:
  - 定时抓取: 系统内置 15+ 免费代理源，自动定时抓取入库
  - 自动清理: 自动移除 >72h 未更新或评分 <30 的低质量代理
  - 实时评分: 根据响应延迟、成功率自动计算 0-100 分值

### 2. 安全与监控

在 `k8s/deployment.yaml` 或 `docker-compose.yml` 中配置环境变量：

```yaml
environment:
  RATE_LIMIT_ENABLED: "True"      # 开启限流
  AUTH_ENABLED: "True"            # 开启 API Key 认证
  ALERT_ENABLED: "True"           # 开启告警
  ALERT_WEBHOOK: "https://oapi.dingtalk.com/..." # 钉钉/企微机器人
```

### 3. 可视化仪表盘

访问 `http://127.0.0.1:5011`，提供以下功能：
- **概览**: 代理总量、HTTPS 占比、地区分布图
- **管理**: 代理列表查询、批量删除、一键复制
- **测试**: 在线测试代理连通性
- **监控**: 查看 API 调用日志、Top 用户统计

---

## 📖 API文档

完整文档请访问 `/docs/` 端点或查看以下简表：

| 方法 | 路径 | 描述 | 参数 |
|---|---|---|---|
| GET | `/get/` | 随机获取代理 | `type`, `region` |
| GET | `/get_batch/` | 批量获取 | `count`, `type` |
| GET | `/export/` | 导出文件 | `format` (txt/json/csv) |
| GET | `/count/` | 代理总数 | - |
| GET | `/health/` | 系统健康状态 | - |
| POST | `/api/delete_batch/`| 批量删代理 | JSON Body |

---

## 📄 版权说明

本项目核心逻辑 Fork 自 [jhao104/proxy_pool](https://github.com/jhao104/proxy_pool)，感谢原作者的开源贡献。

在此基础上，本项目增加了 Web UI、认证鉴权、K8s 支持等大量企业级功能。
