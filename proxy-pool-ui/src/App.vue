<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  DashboardOutlined,
  UnorderedListOutlined,
  CloudServerOutlined,
  ToolOutlined,
  GithubOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  BulbOutlined,
  BulbFilled,
  GlobalOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import { message, theme } from 'ant-design-vue'
import { setLocale, supportedLocales, getLocale } from './locales'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const selectedKeys = computed(() => [route.name as string])
const userInfo = ref<any>(null)
const currentLocale = ref(getLocale())

// 暗黑模式
const isDarkMode = ref(false)

// 菜单项使用 i18n
const menuItems = computed(() => [
  { key: 'dashboard', icon: DashboardOutlined, label: t('nav.dashboard'), path: '/' },
  { key: 'proxies', icon: UnorderedListOutlined, label: t('nav.proxies'), path: '/proxies' },
  { key: 'sources', icon: CloudServerOutlined, label: t('nav.sources'), path: '/sources' },
  { key: 'tools', icon: ToolOutlined, label: t('nav.tools'), path: '/tools' },
  { key: 'docs', icon: FileTextOutlined, label: t('nav.docs'), path: '/docs' },
  { key: 'admin', icon: SettingOutlined, label: t('nav.admin'), path: '/admin' },
])

const isLoggedIn = computed(() => !!localStorage.getItem('api_key'))
const isLoginPage = computed(() => route.path === '/login')

onMounted(() => {
  const storedUser = localStorage.getItem('user_info')
  if (storedUser) {
    try {
      userInfo.value = JSON.parse(storedUser)
    } catch (e) {
      console.error('Failed to parse user info')
    }
  }
  
  // 读取保存的主题偏好
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
  } else if (!savedTheme) {
    // 如果没有保存的偏好，检测系统偏好
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  applyTheme()
})

const handleMenuClick = (item: { key: string }) => {
  const menuItem = menuItems.value.find((m: any) => m.key === item.key)
  if (menuItem) {
    router.push(menuItem.path)
  }
}

const logout = () => {
  localStorage.removeItem('api_key')
  localStorage.removeItem('user_info')
  userInfo.value = null
  message.success(t('auth.logout'))
  router.push('/login')
}

// 切换语言
const switchLocale = (code: string) => {
  setLocale(code)
  currentLocale.value = code
}

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
  applyTheme()
}

const applyTheme = () => {
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    document.body.style.backgroundColor = '#141414'
  } else {
    document.documentElement.classList.remove('dark')
    document.body.style.backgroundColor = '#f0f2f5'
  }
}

watch(isDarkMode, applyTheme)
</script>

<template>
  <!-- Login page: no layout -->
  <a-config-provider
    :theme="{
      algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    }"
  >
    <RouterView v-if="isLoginPage" />
    
    <!-- Normal layout -->
    <a-layout v-else style="min-height: 100vh" :class="{ 'dark-layout': isDarkMode }">
      <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark">
        <div class="logo">
          <span v-if="!collapsed">🌐 Proxy Pool</span>
          <span v-else>🌐</span>
        </div>
        <a-menu
          theme="dark"
          mode="inline"
          :selectedKeys="selectedKeys"
          @click="handleMenuClick"
        >
          <a-menu-item v-for="item in menuItems" :key="item.key">
            <component :is="item.icon" />
            <span>{{ item.label }}</span>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>
      <a-layout>
        <a-layout-header class="header" :class="{ 'dark-header': isDarkMode }">
          <div class="header-content">
            <h2>{{ t('dashboard.title') }}</h2>
            <div class="header-right">
              <!-- 主题切换按钮 -->
              <a-tooltip :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
                <a-button 
                  type="text" 
                  @click="toggleTheme"
                  class="theme-toggle"
                >
                  <BulbFilled v-if="isDarkMode" style="color: #faad14; font-size: 18px;" />
                  <BulbOutlined v-else style="font-size: 18px;" />
                </a-button>
              </a-tooltip>
              
              <!-- 语言切换 -->
              <a-dropdown>
                <a-button type="text" class="lang-toggle">
                  <GlobalOutlined style="font-size: 18px;" />
                  <span style="margin-left: 4px;">{{ (supportedLocales as any[]).find((l: any) => l.code === currentLocale)?.flag }}</span>
                </a-button>
                <template #overlay>
                  <a-menu @click="(info: any) => switchLocale(info.key)">
                    <a-menu-item v-for="lang in supportedLocales" :key="lang.code">
                      {{ lang.flag }} {{ lang.name }}
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
              
              <template v-if="userInfo || isLoggedIn">
                <a-dropdown>
                  <a class="user-info" @click.prevent>
                    <UserOutlined />
                    <span>{{ userInfo?.name || 'User' }}</span>
                    <a-tag v-if="userInfo?.role === 'admin'" color="red" size="small">Admin</a-tag>
                  </a>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="logout" @click="logout">
                        <LogoutOutlined /> {{ t('auth.logout') }}
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </template>
              <a href="https://github.com/yanqingjames951/proxy_pool" target="_blank" class="github-link">
                <GithubOutlined /> GitHub
              </a>
            </div>
          </div>
        </a-layout-header>
        <a-layout-content class="content" :class="{ 'dark-content': isDarkMode }">
          <RouterView />
        </a-layout-content>
        <a-layout-footer class="footer" :class="{ 'dark-footer': isDarkMode }">
          Proxy Pool Dashboard ©2024 | Powered by Vue 3 + Ant Design Vue
        </a-layout-footer>
      </a-layout>
    </a-layout>
  </a-config-provider>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  transition: background-color 0.3s ease;
}

.logo {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.1);
  margin: 8px;
  border-radius: 8px;
}

/* Force override Ant Design header background */
.header.ant-layout-header {
  background: white !important;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  line-height: normal; /* Fix alignment */
  height: 64px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.dark-header.ant-layout-header {
  background: #1f1f1f !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.dark-header h2 {
  color: rgba(255, 255, 255, 0.85) !important;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  width: 100%;
}

.header-content h2 {
  margin: 0;
  font-size: 18px;
  color: #1a1a2e;
  transition: color 0.3s ease;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  transition: background 0.2s;
}

.theme-toggle:hover {
  background: rgba(0, 0, 0, 0.06);
}

.dark-header .theme-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
  transition: background 0.2s, color 0.3s;
}

.dark-header .user-info {
  color: rgba(255, 255, 255, 0.85);
}

.user-info:hover {
  background: #f5f5f5;
}

.dark-header .user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.github-link {
  color: #333;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: color 0.2s, background 0.2s;
}

.dark-header .github-link {
  color: rgba(255, 255, 255, 0.85);
}

.github-link:hover {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  background-color: rgba(24, 144, 255, 0.1); /* Explicit */
}

.lang-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  height: 36px;
  border-radius: 8px;
  transition: background 0.2s;
}

.dark-header .lang-toggle {
  color: rgba(255, 255, 255, 0.85);
}

.lang-toggle:hover {
  background: rgba(0, 0, 0, 0.06);
}

.dark-header .lang-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
}

.content {
  margin: 16px;
  padding: 16px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px - 70px - 32px);
  transition: background-color 0.3s ease;
}

.dark-content {
  background: #141414;
}

.footer {
  text-align: center;
  color: #888;
  background: white;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.dark-footer {
  background: #1f1f1f;
  color: rgba(255, 255, 255, 0.45);
}

/* 全局暗色模式覆盖 */
.dark-layout .ant-card {
  background: #1f1f1f;
  border-color: #303030;
}

.dark-layout .ant-table {
  background: #1f1f1f;
}

.dark-layout .ant-table-thead > tr > th {
  background: #1f1f1f;
}
</style>
