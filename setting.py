"""
-------------------------------------------------
   File Name：     setting.py
   Description :   配置文件
   Author :        ProxyPool Team
   Original :      JHao (https://github.com/jhao104/proxy_pool)
   date：          2024/12/20
-------------------------------------------------
"""

BANNER = r"""
****************************************************************
*** ______  ********************* ______ *********** _  ********
*** | ___ \_ ******************** | ___ \ ********* | | ********
*** | |_/ / \__ __   __  _ __   _ | |_/ /___ * ___  | | ********
*** |  __/|  _// _ \ \ \/ /| | | ||  __// _ \ / _ \ | | ********
*** | |   | | | (_) | >  < \ |_| || |  | (_) | (_) || |___  ****
*** \_|   |_|  \___/ /_/\_\ \__  |\_|   \___/ \___/ \_____/ ****
****                       __ / /                          *****
************************* /___ / *******************************
*************************       ********************************
****************************************************************
"""

VERSION = "2.4.0"

# ############### server config ###############
HOST = "0.0.0.0"

PORT = 5010

# ############### database config ###################
# db connection uri
# example:
#      Redis: redis://:password@ip:port/db
#      Ssdb:  ssdb://:password@ip:port
DB_CONN = 'redis://:pwd@127.0.0.1:6379/0'

# proxy table name
TABLE_NAME = 'use_proxy'


# ###### config the proxy fetch function ######
PROXY_FETCHER = [
    "freeProxy01",  # 站大爷
    "freeProxy05",  # 快代理
    "freeProxy07",  # 云代理
    "freeProxy08",  # 小幻代理
    "freeProxy10",  # 89代理
    "freeProxy12",  # ProxyScrape
    "freeProxy15",  # Proxy-List.download
    "freeProxy17",  # FreeProxy.world
    "freeProxy18",  # Free-Proxy-List
    # 新增可靠代理源
    "freeProxy19",  # GeoNode API
    "freeProxy20",  # TheSpeedX (GitHub)
    "freeProxy21",  # clarketm (GitHub)
    "freeProxy22",  # jetkai (GitHub)
    "freeProxy23",  # monosans (GitHub)
]

# ############# proxy validator #################
# 代理验证目标网站
HTTP_URL = "http://httpbin.org"

HTTPS_URL = "https://www.qq.com"

# 代理验证时超时时间
VERIFY_TIMEOUT = 10

# 近PROXY_CHECK_COUNT次校验中允许的最大失败次数,超过则剔除代理
MAX_FAIL_COUNT = 0

# 近PROXY_CHECK_COUNT次校验中允许的最大失败率,超过则剔除代理
# MAX_FAIL_RATE = 0.1

# proxyCheck时代理数量少于POOL_SIZE_MIN触发抓取
POOL_SIZE_MIN = 20

# ############# proxy attributes #################
# 是否启用代理地域属性
PROXY_REGION = True

# ############# scheduler config #################

# Set the timezone for the scheduler forcely (optional)
# If it is running on a VM, and
#   "ValueError: Timezone offset does not match system offset"
#   was raised during scheduling.
# Please uncomment the following line and set a timezone for the scheduler.
# Otherwise it will detect the timezone from the system automatically.

TIMEZONE = "Asia/Shanghai"

# ############# authentication config #################
# 是否启用 API Key 认证
AUTH_ENABLED = True

# ############# rate limiting config #################
# 是否启用请求限流
RATE_LIMIT_ENABLED = True

# 每分钟最大请求数 (0 表示不限制)
RATE_LIMIT_PER_MINUTE = 60

# 每日最大请求数 (0 表示不限制)
RATE_LIMIT_PER_DAY = 1000

# ############# usage logging config #################
# 是否启用使用日志
USAGE_LOG_ENABLED = True

# 日志保留天数
USAGE_LOG_RETENTION_DAYS = 7

# 最大日志条数
USAGE_LOG_MAX_ENTRIES = 10000

# ############# alert config #################
# 是否启用告警通知
ALERT_ENABLED = True

# 告警 Webhook URL (支持钉钉、企业微信、Slack、Telegram 或通用 JSON webhook)
# 钉钉机器人: https://oapi.dingtalk.com/robot/send?access_token=xxx
# 企业微信: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
# Slack: https://hooks.slack.com/services/xxx
# Telegram: https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>
ALERT_WEBHOOK = ""

# 告警冷却时间（秒），同一类型告警在此时间内不重复发送
ALERT_COOLDOWN = 300

# ############# scheduler config #################
# 动态调度：当代理池低于此值时加快抓取频率
DYNAMIC_FETCH_THRESHOLD = 500

# 正常抓取间隔（秒）
FETCH_INTERVAL_NORMAL = 300

# 紧急抓取间隔（秒）- 代理池数量低时使用
FETCH_INTERVAL_URGENT = 60

