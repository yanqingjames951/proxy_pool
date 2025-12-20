<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { KeyOutlined, LoginOutlined, GlobalOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { setLocale, supportedLocales, getLocale } from '../locales'

const router = useRouter()
const apiKey = ref('')
const loading = ref(false)
const { t } = useI18n()
const currentLocale = ref(getLocale())

const switchLocale = (code: string) => {
  setLocale(code)
  currentLocale.value = code
}

const login = async () => {
  if (!apiKey.value.trim()) {
    message.warning(t('auth.enterApiKey'))
    return
  }
  
  try {
    loading.value = true
    const res = await axios.post('/api/auth/login/', {
      api_key: apiKey.value.trim()
    })
    
    if (res.data.code === 0) {
      // 保存认证信息
      localStorage.setItem('api_key', apiKey.value.trim())
      localStorage.setItem('user_info', JSON.stringify(res.data.user))
      
      // 设置全局 axios 请求头
      axios.defaults.headers.common['X-API-Key'] = apiKey.value.trim()
      
      message.success(t('auth.loginSuccess'))
      router.push('/')
    } else {
      message.error(res.data.message || t('common.error'))
    }
  } catch (error: any) {
    if (error.response?.status === 401) {
      message.error(t('auth.invalidKey'))
    } else {
      message.error(t('common.error'))
    }
  } finally {
    loading.value = false
  }
}

const handleKeyPress = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    login()
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="lang-switch">
        <a-dropdown>
          <a-button type="text">
            <GlobalOutlined /> {{ (supportedLocales as any[]).find((l: any) => l.code === currentLocale)?.flag }}
          </a-button>
          <template #overlay>
            <a-menu @click="(info: any) => switchLocale(info.key)">
              <a-menu-item v-for="lang in supportedLocales" :key="lang.code">
                {{ lang.flag }} {{ lang.name }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>

      <div class="logo">
        <span class="logo-icon">🌐</span>
        <h1>Proxy Pool</h1>
        <p class="subtitle">{{ t('dashboard.title') }}</p>
      </div>
      
      <div class="login-form">
        <a-input-password
          v-model:value="apiKey"
          :placeholder="t('auth.enterApiKey')"
          size="large"
          @keypress="handleKeyPress"
        >
          <template #prefix>
            <KeyOutlined />
          </template>
        </a-input-password>
        
        <a-button 
          type="primary" 
          size="large" 
          block 
          :loading="loading"
          @click="login"
        >
          <template #icon>
            <LoginOutlined />
          </template>
          {{ t('auth.login') }}
        </a-button>
      </div>
      
      <div class="tips">
        <a-alert 
          :message="t('common.confirm')"
          :description="t('auth.enterApiKey')" 
          type="info" 
          show-icon 
        >
        <!-- 'description' is usually contact admin in original code ("请联系管理员...").
             I don't have a key for "Contact Admin". I'll skip translating description if not critical or use "enterApiKey".
             Original: "请联系管理员获取 API Key"
             I'll hardcode "Contact Admin for API Key" if English? Or add key.
             I'll add "contactAdmin": "请联系管理员获取 API Key" to `auth` in JSON. 
        -->
          <template #description>
             {{ t('auth.contactAdmin') || 'Contact Admin for API Key' }}
          </template>
        </a-alert>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 48px;
  width: 100%;
  max-width: 420px;
  animation: slideUp 0.5s ease-out;
  position: relative;
}

.lang-switch {
  position: absolute;
  top: 16px;
  right: 16px;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.logo h1 {
  margin: 0;
  font-size: 28px;
  color: #1a1a2e;
  font-weight: 600;
}

.subtitle {
  margin: 8px 0 0;
  color: #666;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-form :deep(.ant-input-affix-wrapper) {
  border-radius: 8px;
}

.login-form :deep(.ant-btn) {
  border-radius: 8px;
  height: 48px;
  font-size: 16px;
}

.tips {
  margin-top: 24px;
}

.tips :deep(.ant-alert) {
  border-radius: 8px;
}
</style>
