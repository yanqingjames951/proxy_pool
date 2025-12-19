<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { message, Modal } from 'ant-design-vue'
import {
  UserOutlined,
  KeyOutlined,
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  ReloadOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

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
      usageStats.value = statsRes.data.stats || []
      summary.value = statsRes.data.summary || {}
      usageLogs.value = logsRes.data.logs || []
    } else {
      const [statsRes, logsRes] = await Promise.all([
        axios.get('/api/usage/stats/?days=7'),
        axios.get('/api/usage/logs/?limit=50')
      ])
      usageStats.value = statsRes.data.stats ? [statsRes.data.stats] : []
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
    message.warning('请输入用户名')
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
      message.error(res.data.message || '创建失败')
    }
  } catch (error) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

const copyKey = (key: string) => {
  navigator.clipboard.writeText(key)
  message.success('已复制到剪贴板')
}

const deleteApiKey = (key: ApiKey) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除 ${key.name} 的 API Key 吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await axios.delete(`/api/auth/keys/${key.full_key}/`)
        message.success('删除成功')
        fetchData()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

const keyColumns = [
  { title: '用户', dataIndex: 'name', key: 'name' },
  { title: 'Key (部分)', dataIndex: 'key', key: 'key' },
  { title: '角色', dataIndex: 'role', key: 'role' },
  { title: '创建时间', dataIndex: 'created', key: 'created' },
  { title: '最后使用', dataIndex: 'last_used', key: 'last_used' },
  { title: '使用次数', dataIndex: 'usage_count', key: 'usage_count' },
  { title: '操作', key: 'action', width: 150 }
]

const logColumns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '用户', dataIndex: 'user', key: 'user', width: 120 },
  { title: '操作', dataIndex: 'action', key: 'action', width: 80 },
  { title: '代理', dataIndex: 'proxy', key: 'proxy' }
]
</script>

<template>
  <div class="admin-view">
    <a-spin :spinning="loading">
      <!-- Admin: API Keys Management -->
      <template v-if="isAdmin">
        <a-card title="API Key 管理" class="section-card">
          <template #extra>
            <a-space>
              <a-button @click="fetchData">
                <ReloadOutlined /> 刷新
              </a-button>
              <a-button type="primary" @click="showCreateModal">
                <PlusOutlined /> 创建 Key
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
                  {{ record.role === 'admin' ? '管理员' : '用户' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'last_used'">
                {{ record.last_used || '-' }}
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-tooltip title="复制完整 Key">
                    <a-button size="small" @click="copyKey(record.full_key)">
                      <CopyOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip title="删除">
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
            <a-statistic title="今日调用" :value="summary.today || 0">
              <template #prefix><BarChartOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic title="本周调用" :value="summary.week || 0">
              <template #prefix><BarChartOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic title="活跃用户" :value="summary.active_users || 0">
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
      <a-card title="使用日志" class="section-card">
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
      title="创建 API Key"
      @ok="createApiKey"
      :confirmLoading="creating"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名" required>
          <a-input v-model:value="createForm.name" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="角色">
          <a-radio-group v-model:value="createForm.role">
            <a-radio value="user">普通用户</a-radio>
            <a-radio value="admin">管理员</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- New Key Display Modal -->
    <a-modal
      v-model:open="newKeyVisible"
      title="API Key 创建成功"
      :footer="null"
    >
      <a-alert
        message="请保存此 API Key，关闭后将无法再次查看完整内容"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-input-group compact>
        <a-input :value="newKey" style="width: calc(100% - 80px)" readonly />
        <a-button type="primary" @click="copyKey(newKey)">
          <CopyOutlined /> 复制
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
