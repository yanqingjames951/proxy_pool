<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import {
  ExperimentOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'

// Proxy Tester State
const proxyInput = ref('')
const testUrl = ref('http://httpbin.org/ip')
const testing = ref(false)
const testResult = ref<any>(null)

// Config State
const config = ref<any>(null)
const configLoading = ref(true)

// Quick Get Proxy
const randomProxy = ref<any>(null)
const gettingProxy = ref(false)

const testProxy = async () => {
  if (!proxyInput.value.trim()) {
    message.warning('请输入代理地址')
    return
  }
  
  testing.value = true
  testResult.value = null
  
  try {
    const res = await axios.post('/api/test/', {
      proxy: proxyInput.value.trim(),
      url: testUrl.value
    })
    testResult.value = res.data
  } catch (error) {
    message.error('测试请求失败')
  } finally {
    testing.value = false
  }
}

const fetchConfig = async () => {
  try {
    configLoading.value = true
    const res = await axios.get('/api/config/')
    config.value = res.data
  } catch (error) {
    console.error('Failed to fetch config', error)
  } finally {
    configLoading.value = false
  }
}

const getRandomProxy = async (https: boolean = false) => {
  gettingProxy.value = true
  try {
    const url = https ? '/get/?type=https' : '/get/'
    const res = await axios.get(url)
    if (res.data.proxy) {
      randomProxy.value = res.data
      proxyInput.value = res.data.proxy
      message.success('获取代理成功')
    } else {
      message.warning('代理池为空')
      randomProxy.value = null
    }
  } catch (error) {
    message.error('获取代理失败')
  } finally {
    gettingProxy.value = false
  }
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
  message.success('已复制到剪贴板')
}

const formatConfigKey = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="tools-view">
    <a-row :gutter="[16, 16]">
      <!-- Proxy Tester -->
      <a-col :xs="24" :lg="12">
        <a-card title="🧪 代理测试工具" class="tool-card">
          <a-space direction="vertical" style="width: 100%" size="middle">
            <!-- Quick Get Proxy -->
            <div class="quick-actions">
              <a-button 
                :loading="gettingProxy" 
                @click="getRandomProxy(false)"
              >
                获取 HTTP 代理
              </a-button>
              <a-button 
                :loading="gettingProxy" 
                @click="getRandomProxy(true)"
              >
                获取 HTTPS 代理
              </a-button>
            </div>
            
            <!-- Proxy Input -->
            <a-input-group compact>
              <a-input
                v-model:value="proxyInput"
                placeholder="输入代理地址，如: 127.0.0.1:8080"
                style="width: calc(100% - 100px)"
                @pressEnter="testProxy"
              />
              <a-button 
                type="primary" 
                :loading="testing"
                @click="testProxy"
                style="width: 100px"
              >
                <ExperimentOutlined /> 测试
              </a-button>
            </a-input-group>
            
            <!-- Test URL -->
            <a-input
              v-model:value="testUrl"
              placeholder="测试目标 URL"
              addonBefore="测试URL"
            />
            
            <!-- Current Proxy Info -->
            <a-descriptions 
              v-if="randomProxy" 
              title="当前代理信息" 
              :column="1" 
              bordered
              size="small"
            >
              <a-descriptions-item label="代理地址">
                {{ randomProxy.proxy }}
                <a-button size="small" type="link" @click="copyToClipboard(randomProxy.proxy)">
                  <CopyOutlined />
                </a-button>
              </a-descriptions-item>
              <a-descriptions-item label="协议">
                <a-tag :color="randomProxy.https ? 'green' : 'blue'">
                  {{ randomProxy.https ? 'HTTPS' : 'HTTP' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="地区">
                {{ randomProxy.region || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="来源">
                {{ randomProxy.source || '-' }}
              </a-descriptions-item>
            </a-descriptions>
            
            <!-- Test Result -->
            <a-card v-if="testResult" class="result-card" :bordered="false">
              <template #title>
                <span v-if="testResult.success" class="success-title">
                  <CheckCircleOutlined /> 测试成功
                </span>
                <span v-else class="error-title">
                  <CloseCircleOutlined /> 测试失败
                </span>
              </template>
              
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="状态">
                  <a-tag :color="testResult.success ? 'success' : 'error'">
                    {{ testResult.success ? '成功' : '失败' }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="延迟">
                  <span :class="{ 'latency-good': testResult.latency_ms < 1000, 'latency-bad': testResult.latency_ms >= 1000 }">
                    {{ testResult.latency_ms }} ms
                  </span>
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.status_code" label="状态码">
                  {{ testResult.status_code }}
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.error" label="错误信息">
                  <a-typography-text type="danger">{{ testResult.error }}</a-typography-text>
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.content" label="响应内容">
                  <a-typography-paragraph 
                    :ellipsis="{ rows: 3, expandable: true }"
                    :content="testResult.content"
                  />
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-space>
        </a-card>
      </a-col>

      <!-- System Config -->
      <a-col :xs="24" :lg="12">
        <a-card title="⚙️ 系统配置" class="tool-card">
          <a-spin :spinning="configLoading">
            <a-descriptions 
              v-if="config" 
              :column="1" 
              bordered 
              size="small"
            >
              <a-descriptions-item label="服务器地址">
                {{ config.server_host }}:{{ config.server_port }}
              </a-descriptions-item>
              <a-descriptions-item label="HTTP 验证 URL">
                {{ config.http_url }}
              </a-descriptions-item>
              <a-descriptions-item label="HTTPS 验证 URL">
                {{ config.https_url }}
              </a-descriptions-item>
              <a-descriptions-item label="验证超时">
                {{ config.verify_timeout }} 秒
              </a-descriptions-item>
              <a-descriptions-item label="最大失败次数">
                {{ config.max_fail_count }}
              </a-descriptions-item>
              <a-descriptions-item label="最小代理池大小">
                {{ config.pool_size_min }}
              </a-descriptions-item>
              <a-descriptions-item label="启用地区检测">
                <a-tag :color="config.proxy_region ? 'success' : 'default'">
                  {{ config.proxy_region ? '是' : '否' }}
                </a-tag>
              </a-descriptions-item>
            </a-descriptions>
            
            <a-divider>已启用的代理源 ({{ config?.fetchers?.length || 0 }})</a-divider>
            
            <div class="fetchers-grid" v-if="config?.fetchers">
              <a-tag 
                v-for="fetcher in config.fetchers" 
                :key="fetcher"
                color="blue"
              >
                {{ fetcher }}
              </a-tag>
            </div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>

    <!-- API Documentation -->
    <a-card title="📚 API 文档" class="api-card" style="margin-top: 16px">
      <a-table
        :dataSource="[
          { url: '/get/', method: 'GET', params: 'type=https', desc: '随机获取一个代理' },
          { url: '/pop/', method: 'GET', params: 'type=https', desc: '获取并删除一个代理' },
          { url: '/all/', method: 'GET', params: 'type=https', desc: '获取所有代理' },
          { url: '/count/', method: 'GET', params: '-', desc: '获取代理统计信息' },
          { url: '/delete/', method: 'GET', params: 'proxy=ip:port', desc: '删除指定代理' },
          { url: '/api/proxies/', method: 'GET', params: 'page, size, https, region, source', desc: '分页获取代理列表' },
          { url: '/api/test/', method: 'POST', params: 'proxy, url', desc: '测试代理连通性' },
          { url: '/api/sources/', method: 'GET', params: '-', desc: '获取代理源统计' },
          { url: '/api/config/', method: 'GET', params: '-', desc: '获取系统配置' },
        ]"
        :columns="[
          { title: 'URL', dataIndex: 'url', key: 'url' },
          { title: '方法', dataIndex: 'method', key: 'method' },
          { title: '参数', dataIndex: 'params', key: 'params' },
          { title: '描述', dataIndex: 'desc', key: 'desc' },
        ]"
        :pagination="false"
        size="small"
        :rowKey="(record: any) => record.url"
      />
    </a-card>
  </div>
</template>

<style scoped>
.tools-view {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.tool-card {
  border-radius: 12px;
  height: 100%;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.result-card {
  background: #fafafa;
  border-radius: 8px;
}

.success-title {
  color: #52c41a;
}

.error-title {
  color: #ff4d4f;
}

.latency-good {
  color: #52c41a;
  font-weight: bold;
}

.latency-bad {
  color: #faad14;
  font-weight: bold;
}

.fetchers-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.api-card {
  border-radius: 12px;
}
</style>
