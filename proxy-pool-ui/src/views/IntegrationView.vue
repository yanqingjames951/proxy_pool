<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined, CodeOutlined, ApiOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const activeTab = ref('python')
const apiKey = localStorage.getItem('api_key') || 'YOUR_API_KEY'
const baseUrl = window.location.origin

const pythonCode = computed(() => `import requests

api_key = "${apiKey}"
api_url = "${baseUrl}"

headers = {
    "X-API-Key": api_key
}

# 1. Get a single proxy (获取单个代理)
# type: 'http' or 'https' (optional)
try:
    response = requests.get(f"{api_url}/get/?type=https", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("Proxy:", data.get("proxy"))
    else:
        print("Error:", response.text)
except Exception as e:
    print(e)

# 2. Get batch proxies (批量获取)
# count: number of proxies (optional, default 10)
response = requests.get(f"{api_url}/get_batch/?count=5&type=https", headers=headers)
print(response.json())
`)

const phpCode = computed(() => `<?php
$api_key = "${apiKey}";
$api_url = "${baseUrl}";

function get_proxy($url, $key) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        "X-API-Key: $key"
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200) {
        return json_decode($response, true);
    }
    return null;
}

// 1. Get a single proxy
$result = get_proxy("$api_url/get/?type=https", $api_key);
print_r($result);

// 2. Get batch proxies
$batch = get_proxy("$api_url/get_batch/?count=5", $api_key);
print_r($batch);
?>
`)

const copyCode = (code: string) => {
  navigator.clipboard.writeText(code)
  message.success(t('common.copied')) // Need to add this key
}
</script>

<template>
  <div class="integration-view">
    <a-card class="doc-card" :title="t('docs.title')">
      <template #extra>
        <ApiOutlined />
      </template>

      <!-- Base Info -->
      <a-descriptions :title="t('docs.baseInfo')" bordered>
        <a-descriptions-item label="API Base URL" :span="3">
          <code>{{ baseUrl }}</code>
        </a-descriptions-item>
        <a-descriptions-item label="Authentication" :span="3">
          Header: <code>X-API-Key: {{ apiKey }}</code>
        </a-descriptions-item>
      </a-descriptions>

      <a-divider />

      <!-- Code Examples -->
      <h3><CodeOutlined /> {{ t('docs.examples') }}</h3>
      
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="python" tab="Python">
          <div class="code-block">
            <a-button class="copy-btn" size="small" @click="copyCode(pythonCode)">
              <CopyOutlined /> {{ t('common.copy') }}
            </a-button>
            <pre><code class="language-python">{{ pythonCode }}</code></pre>
          </div>
        </a-tab-pane>
        <a-tab-pane key="php" tab="PHP">
          <div class="code-block">
            <a-button class="copy-btn" size="small" @click="copyCode(phpCode)">
              <CopyOutlined /> {{ t('common.copy') }}
            </a-button>
            <pre><code class="language-php">{{ phpCode }}</code></pre>
          </div>
        </a-tab-pane>
      </a-tabs>

      <a-divider />

      <!-- API Reference List (Simple) -->
      <h3>{{ t('docs.apiReference') }}</h3>
      <a-list item-layout="horizontal" :data-source="[
        { method: 'GET', url: '/get/', desc: t('docs.api.get') },
        { method: 'GET', url: '/get_batch/', desc: t('docs.api.getBatch') },
        { method: 'GET', url: '/pop/', desc: t('docs.api.pop') },
        { method: 'GET', url: '/count/', desc: t('docs.api.count') },
        { method: 'GET', url: '/health/', desc: t('docs.api.health') },
      ]" size="small" bordered>
        <template #renderItem="{ item }">
          <a-list-item>
            <a-tag :color="item.method === 'GET' ? 'green' : 'blue'">{{ item.method }}</a-tag>
            <span class="api-url">{{ item.url }}</span>
            <span>{{ item.desc }}</span>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<style scoped>
.integration-view {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.doc-card {
  border-radius: 12px;
}

.code-block {
  position: relative;
  background: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.dark-layout .code-block {
  background: #141414;
  border: 1px solid #303030;
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
}

pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
}

.api-url {
  font-weight: bold;
  margin-right: 16px;
  font-family: monospace;
}
</style>
