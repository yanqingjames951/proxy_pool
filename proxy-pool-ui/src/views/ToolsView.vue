<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  ExperimentOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'

const { t } = useI18n()

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
    message.warning(t('tools.enterProxy'))
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
    message.error(t('tools.testFailed'))
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
      message.success(t('common.success'))
    } else {
      message.warning(t('proxies.noData'))
      randomProxy.value = null
    }
  } catch (error) {
    message.error(t('common.error'))
  } finally {
    gettingProxy.value = false
  }
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
  message.success(t('common.copied'))
}

const apiData = computed(() => [
  { url: '/get/', method: 'GET', params: 'type=https', desc: t('tools.apiDesc.get') },
  { url: '/pop/', method: 'GET', params: 'type=https', desc: t('tools.apiDesc.pop') },
  { url: '/all/', method: 'GET', params: 'type=https', desc: t('tools.apiDesc.all') },
  { url: '/count/', method: 'GET', params: '-', desc: t('tools.apiDesc.count') },
  { url: '/delete/', method: 'GET', params: 'proxy=ip:port', desc: t('tools.apiDesc.delete') },
  { url: '/api/proxies/', method: 'GET', params: 'page, size, https, region, source', desc: t('tools.apiDesc.list') },
  { url: '/api/test/', method: 'POST', params: 'proxy, url', desc: t('tools.apiDesc.test') },
  { url: '/api/sources/', method: 'GET', params: '-', desc: t('tools.apiDesc.sources') },
  { url: '/api/config/', method: 'GET', params: '-', desc: t('tools.apiDesc.config') },
])

const apiColumns = computed(() => [
  { title: t('tools.table.url'), dataIndex: 'url', key: 'url' },
  { title: t('tools.table.method'), dataIndex: 'method', key: 'method' },
  { title: t('tools.table.params'), dataIndex: 'params', key: 'params' },
  { title: t('tools.table.desc'), dataIndex: 'desc', key: 'desc' },
])

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="tools-view">
    <a-row :gutter="[16, 16]">
      <!-- Proxy Tester -->
      <a-col :xs="24" :lg="12">
        <a-card :title="'🧪 ' + t('tools.proxyTester')" class="tool-card">
          <a-space direction="vertical" style="width: 100%" size="middle">
            <!-- Quick Get Proxy -->
            <div class="quick-actions">
              <a-button 
                :loading="gettingProxy" 
                @click="getRandomProxy(false)"
              >
                {{ t('tools.getHttpProxy') }}
              </a-button>
              <a-button 
                :loading="gettingProxy" 
                @click="getRandomProxy(true)"
              >
                {{ t('tools.getHttpsProxy') }}
              </a-button>
            </div>
            
            <!-- Proxy Input -->
            <a-input-group compact>
              <a-input
                v-model:value="proxyInput"
                :placeholder="t('tools.enterProxy')"
                style="width: calc(100% - 100px)"
                @pressEnter="testProxy"
              />
              <a-button 
                type="primary" 
                :loading="testing"
                @click="testProxy"
                style="width: 100px"
              >
                <ExperimentOutlined /> {{ t('tools.test') }}
              </a-button>
            </a-input-group>
            
            <!-- Test URL -->
            <a-input
              v-model:value="testUrl"
              :placeholder="t('tools.testUrl')"
              :addonBefore="t('tools.testUrlLabel')"
            />
            
            <!-- Current Proxy Info -->
            <a-descriptions 
              v-if="randomProxy" 
              :title="t('tools.currentProxy')" 
              :column="1" 
              bordered
              size="small"
            >
              <a-descriptions-item :label="t('proxies.proxy')">
                {{ randomProxy.proxy }}
                <a-button size="small" type="link" @click="copyToClipboard(randomProxy.proxy)">
                  <CopyOutlined />
                </a-button>
              </a-descriptions-item>
              <a-descriptions-item :label="t('proxies.protocol')">
                <a-tag :color="randomProxy.https ? 'green' : 'blue'">
                  {{ randomProxy.https ? 'HTTPS' : 'HTTP' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item :label="t('proxies.region')">
                {{ randomProxy.region || '-' }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('proxies.source')">
                {{ randomProxy.source || '-' }}
              </a-descriptions-item>
            </a-descriptions>
            
            <!-- Test Result -->
            <a-card v-if="testResult" class="result-card" :bordered="false">
              <template #title>
                <span v-if="testResult.success" class="success-title">
                  <CheckCircleOutlined /> {{ t('tools.testSuccess') }}
                </span>
                <span v-else class="error-title">
                  <CloseCircleOutlined /> {{ t('tools.testFailed') }}
                </span>
              </template>
              
              <a-descriptions :column="1" size="small">
                <a-descriptions-item :label="t('tools.status')">
                  <a-tag :color="testResult.success ? 'success' : 'error'">
                    {{ testResult.success ? t('tools.success') : t('tools.failed') }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item :label="t('tools.latency')">
                  <span :class="{ 'latency-good': testResult.latency_ms < 1000, 'latency-bad': testResult.latency_ms >= 1000 }">
                    {{ testResult.latency_ms }} ms
                  </span>
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.status_code" :label="t('tools.statusCode')">
                  {{ testResult.status_code }}
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.error" :label="t('tools.errorMsg')">
                  <a-typography-text type="danger">{{ testResult.error }}</a-typography-text>
                </a-descriptions-item>
                <a-descriptions-item v-if="testResult.content" :label="t('tools.response')">
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
        <a-card :title="'⚙️ ' + t('tools.systemConfig')" class="tool-card">
          <a-spin :spinning="configLoading">
            <a-descriptions 
              v-if="config" 
              :column="1" 
              bordered 
              size="small"
            >
              <a-descriptions-item :label="t('tools.config.serverHost')">
                {{ config.server_host }}:{{ config.server_port }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.httpUrl')">
                {{ config.http_url }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.httpsUrl')">
                {{ config.https_url }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.timeout')">
                {{ config.verify_timeout }} s
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.maxFail')">
                {{ config.max_fail_count }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.minPool')">
                {{ config.pool_size_min }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('tools.config.region')">
                <a-tag :color="config.proxy_region ? 'success' : 'default'">
                  {{ config.proxy_region ? 'Yes' : 'No' }}
                </a-tag>
              </a-descriptions-item>
            </a-descriptions>
            
            <a-divider>{{ t('tools.enabledSources') }} ({{ config?.fetchers?.length || 0 }})</a-divider>
            
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
    <a-card :title="'📚 ' + t('tools.apiDocs')" class="api-card" style="margin-top: 16px">
      <a-table
        :dataSource="apiData"
        :columns="apiColumns"
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
