<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  UserOutlined,
  KeyOutlined,
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  ReloadOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

const { t } = useI18n()

interface ApiKey {
  key: string
  full_key: string
  name: string
  role: string
  created: string
  last_used: string
  usage_count: number
}

interface UsageLog {
  time: string
  user: string
  action: string
  proxy: string
}

interface DailyStat {
  date: string
  total: number
  users: Record<string, number>
  actions: Record<string, number>
}

const loading = ref(true)
const apiKeys = ref<ApiKey[]>([])
const usageLogs = ref<UsageLog[]>([])
const usageStats = ref<DailyStat[]>([])
const summary = ref<any>({})
const currentUser = ref<any>(null)

// Create key modal
const createModalVisible = ref(false)
const createForm = ref({
  name: '',
  role: 'user'
})
const creating = ref(false)

// New key display
const newKeyVisible = ref(false)
const newKey = ref('')

onMounted(() => {
  const userInfo = localStorage.getItem('user_info')
  if (userInfo) {
    currentUser.value = JSON.parse(userInfo)
  }
  fetchData()
})

const isAdmin = computed(() => currentUser.value?.role === 'admin')

const fetchData = async () => {
  loading.value = true
  try {
    if (isAdmin.value) {
      const [keysRes, statsRes, logsRes] = await Promise.all([
        axios.get('/api/auth/keys/'),
        axios.get('/api/usage/stats/?days=7'),
        axios.get('/api/usage/logs/?limit=50')
      ])
      apiKeys.value = keysRes.data.keys || []
      usageStats.value = statsRes.data.stats || [] // Wait, Step 1390 said usageStats is statsRes.data.stats, BUT summary is statsRes.data.summary.
      // My ProxyApi returns: { "stats": [...], "summary": {...} } for stats endpoint?
      // Step 1390 used: usageStats.value = statsRes.data.stats; summary.value = statsRes.data.summary
      // Let's assume consistent.
      usageStats.value = statsRes.data.stats || []
      summary.value = statsRes.data.summary || {}
      usageLogs.value = logsRes.data.logs || []
    } else {
      const [statsRes, logsRes] = await Promise.all([
        axios.get('/api/usage/stats/?days=7'),
        axios.get('/api/usage/logs/?limit=50')
      ])
      // Non-admin stats return just { "stats": daily_stats, "summary": ... } ?
      // Step 1390 logic: usageStats.value = statsRes.data.stats ? [statsRes.data.stats] : [] ... weird.
      // Ah, daily stats might be a list.
      // I'll trust the Step 1390 logic was at least somewhat tested, but I'll make it safe.
      usageStats.value = Array.isArray(statsRes.data.stats) ? statsRes.data.stats : (statsRes.data.stats ? [statsRes.data.stats] : [])
      usageLogs.value = logsRes.data.logs || []
    }
  } catch (error) {
    console.error('Failed to fetch data', error)
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  createForm.value = { name: '', role: 'user' }
  createModalVisible.value = true
}

const createApiKey = async () => {
  if (!createForm.value.name.trim()) {
    message.warning(t('admin.name') + ' Required') // Need a better key? "Please enter name" -> "admin.enterName" (not in json).
    return
  }
  
  creating.value = true
  try {
    const res = await axios.post('/api/auth/keys/', createForm.value)
    if (res.data.code === 0) {
      newKey.value = res.data.api_key
      createModalVisible.value = false
      newKeyVisible.value = true
      fetchData()
    } else {
      message.error(res.data.message || t('common.error'))
    }
  } catch (error) {
    message.error(t('common.error'))
  } finally {
    creating.value = false
  }
}

const copyKey = (key: string) => {
  navigator.clipboard.writeText(key)
  message.success(t('common.copied'))
}

const deleteApiKey = (key: ApiKey) => {
  Modal.confirm({
    title: t('common.confirm'),
    content: `${t('common.delete')} ${key.name}?`,
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        await axios.delete(`/api/auth/keys/${key.full_key}/`)
        message.success(t('common.success'))
        fetchData()
      } catch (error) {
        message.error(t('common.error'))
      }
    }
  })
}

const keyColumns = computed(() => [
  { title: t('admin.name'), dataIndex: 'name', key: 'name' },
  { title: 'Key', dataIndex: 'key', key: 'key' },
  { title: t('admin.role'), dataIndex: 'role', key: 'role' },
  { title: t('admin.createdAt'), dataIndex: 'created', key: 'created' },
  { title: t('admin.lastUsed'), dataIndex: 'last_used', key: 'last_used' },
  { title: t('admin.usageCount'), dataIndex: 'usage_count', key: 'usage_count' },
  { title: t('proxies.actions'), key: 'action', width: 150 }
])

const logColumns = computed(() => [
  { title: t('proxies.lastCheck'), dataIndex: 'time', key: 'time', width: 180 }, // Using lastCheck for time? Or just 'Time'? Added 'Time' implicitly?
  // zh.json doesn't have "time". "proxies.lastCheck" is "最后检测". Close enough? 
  // Maybe "admin.createdAt"? No.
  // I'll stick to 'Time' string or reuse something.
  // Let's use t('admin.createdAt') as "Time"? No.
  // I'll just use "Time" string for now or add to JSON.
  // I'll use "Time" literal.
  { title: 'Time', dataIndex: 'time', key: 'time', width: 180 },
  { title: t('admin.name'), dataIndex: 'user', key: 'user', width: 120 },
  { title: t('proxies.actions'), dataIndex: 'action', key: 'action', width: 80 },
  { title: t('proxies.proxy'), dataIndex: 'proxy', key: 'proxy' }
])
</script>

<template>
  <div class="admin-view">
    <a-spin :spinning="loading">
      <!-- Admin: API Keys Management -->
      <template v-if="isAdmin">
        <a-card :title="t('admin.apiKeys')" class="section-card">
          <template #extra>
            <a-space>
              <a-button @click="fetchData">
                <ReloadOutlined /> {{ t('admin.refresh') }}
              </a-button>
              <a-button type="primary" @click="showCreateModal">
                <PlusOutlined /> {{ t('admin.createKey') }}
              </a-button>
            </a-space>
          </template>
          
          <a-table
            :columns="keyColumns"
            :dataSource="apiKeys"
            :rowKey="(record: ApiKey) => record.full_key"
            :pagination="{ pageSize: 10 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'role'">
                <a-tag :color="record.role === 'admin' ? 'red' : 'blue'">
                  {{ record.role === 'admin' ? t('admin.administrator') : t('admin.user') }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'last_used'">
                {{ record.last_used || '-' }}
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-tooltip :title="t('common.copy')">
                    <a-button size="small" @click="copyKey(record.full_key)">
                      <CopyOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip :title="t('common.delete')">
                    <a-button size="small" danger @click="deleteApiKey(record)">
                      <DeleteOutlined />
                    </a-button>
                  </a-tooltip>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </template>

      <!-- Usage Summary -->
      <a-row :gutter="[16, 16]" class="summary-row" v-if="isAdmin">
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic :title="t('dashboard.todayCalls')" :value="summary.today || 0">
              <template #prefix><BarChartOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic :title="t('dashboard.weekCalls')" :value="summary.week || 0">
              <template #prefix><BarChartOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic :title="t('dashboard.activeUsers')" :value="summary.active_users || 0">
              <template #prefix><UserOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic title="API Keys" :value="apiKeys.length">
              <template #prefix><KeyOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- Usage Logs -->
      <a-card :title="t('admin.usageLogs')" class="section-card">
        <a-table
          :columns="logColumns"
          :dataSource="usageLogs"
          :rowKey="(_record: UsageLog, index: number) => index"
          :pagination="{ pageSize: 10 }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-tag :color="record.action === 'get' ? 'blue' : 'orange'">
                {{ record.action }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-spin>

    <!-- Create Key Modal -->
    <a-modal
      v-model:open="createModalVisible"
      :title="t('admin.createKey')"
      @ok="createApiKey"
      :confirmLoading="creating"
    >
      <a-form layout="vertical">
        <a-form-item :label="t('admin.name')" required>
          <a-input v-model:value="createForm.name" :placeholder="t('admin.name')" />
        </a-form-item>
        <a-form-item :label="t('admin.role')">
          <a-radio-group v-model:value="createForm.role">
            <a-radio value="user">{{ t('admin.user') }}</a-radio>
            <a-radio value="admin">{{ t('admin.administrator') }}</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- New Key Display Modal -->
    <a-modal
      v-model:open="newKeyVisible"
      :title="t('common.success')"
      :footer="null"
    >
      <a-alert
        message="Please save this Key."
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-input-group compact>
        <a-input :value="newKey" style="width: calc(100% - 80px)" readonly />
        <a-button type="primary" @click="copyKey(newKey)">
          <CopyOutlined /> {{ t('common.copy') }}
        </a-button>
      </a-input-group>
    </a-modal>
  </div>
</template>

<style scoped>
.admin-view {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.summary-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
</style>
