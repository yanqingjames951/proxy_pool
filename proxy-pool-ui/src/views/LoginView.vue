<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { KeyOutlined, LoginOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const apiKey = ref('')
const loading = ref(false)

const login = async () => {
  if (!apiKey.value.trim()) {
    message.warning('请输入 API Key')
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
      
      message.success(`欢迎, ${res.data.user.name}!`)
      router.push('/')
    } else {
      message.error(res.data.message || '登录失败')
    }
  } catch (error: any) {
    if (error.response?.status === 401) {
      message.error('API Key 无效')
    } else {
      message.error('登录失败，请重试')
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
      <div class="logo">
        <span class="logo-icon">🌐</span>
        <h1>Proxy Pool</h1>
        <p class="subtitle">代理池管理系统</p>
      </div>
      
      <div class="login-form">
        <a-input-password
          v-model:value="apiKey"
          placeholder="请输入 API Key"
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
          登录
        </a-button>
      </div>
      
      <div class="tips">
        <a-alert 
          message="提示" 
          description="请联系管理员获取 API Key" 
          type="info" 
          show-icon 
        />
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
