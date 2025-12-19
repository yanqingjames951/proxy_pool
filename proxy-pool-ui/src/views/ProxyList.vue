<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  DeleteOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'

interface Proxy {
  proxy: string
  https: boolean
  fail_count: number
  region: string
  anonymous: string
  source: string
  check_count: number
  last_status: string
  last_time: string
  latency: number
}

interface ProxyResponse {
  data: Proxy[]
  total: number
  page: number
  size: number
  pages: number
}

const proxies = ref<Proxy[]>([])
const loading = ref(true)
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0
})

// Filters
const filters = ref({
  https: '',
  region: '',
  source: ''
})

// Sorting - default by latency ascending (fastest first)
const sorter = ref({
  field: 'latency',
  order: 'asc'
})

// Selection
const selectedRowKeys = ref<string[]>([])
const selectedRows = ref<Proxy[]>([])

// Testing state
const testingProxy = ref<string | null>(null)
const testResults = ref<Record<string, any>>({})

const columns = [
  {
    title: '代理地址',
    dataIndex: 'proxy',
    key: 'proxy',
    width: 180
  },
  {
    title: '延迟',
    dataIndex: 'latency',
    key: 'latency',
    width: 100,
    sorter: true,
    defaultSortOrder: 'ascend'
  },
  {
    title: '协议',
    dataIndex: 'https',
    key: 'https',
    width: 80
  },
  {
    title: '地区',
    dataIndex: 'region',
    key: 'region',
    width: 150,
    ellipsis: true
  },
  {
    title: '来源',
    dataIndex: 'source',
    key: 'source',
    width: 150,
    ellipsis: true
  },
  {
    title: '检测次数',
    dataIndex: 'check_count',
    key: 'check_count',
    width: 100,
    sorter: true
  },
  {
    title: '失败次数',
    dataIndex: 'fail_count',
    key: 'fail_count',
    width: 100,
    sorter: true
  },
  {
    title: '最后检测',
    dataIndex: 'last_time',
    key: 'last_time',
    width: 180,
    sorter: true
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

const fetchProxies = async () => {
  try {
    loading.value = true
    const params = new URLSearchParams({
      page: String(pagination.value.current),
      size: String(pagination.value.pageSize),
      sort: sorter.value.field,
      order: sorter.value.order
    })
    
    if (filters.value.https) params.append('https', filters.value.https)
    if (filters.value.region) params.append('region', filters.value.region)
    if (filters.value.source) params.append('source', filters.value.source)
    
    const res = await axios.get<ProxyResponse>(`/api/proxies/?${params}`)
    proxies.value = res.data.data
    pagination.value.total = res.data.total
  } catch (error) {
    console.error('Failed to fetch proxies', error)
    message.error('获取代理列表失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any, _filters: any, sort: any) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  
  // Handle sorting
  if (sort.field) {
    sorter.value.field = sort.field
    sorter.value.order = sort.order === 'descend' ? 'desc' : 'asc'
  }
  
  fetchProxies()
}

const getLatencyColor = (latency: number): string => {
  if (latency === 0) return '#999'
  if (latency < 500) return '#52c41a'
  if (latency < 1000) return '#faad14'
  if (latency < 2000) return '#fa8c16'
  return '#ff4d4f'
}

const getLatencyLabel = (latency: number): string => {
  if (latency === 0) return '-'
  return `${latency}ms`
}

const copyProxy = (proxy: string) => {
  navigator.clipboard.writeText(proxy)
  message.success('已复制到剪贴板')
}

const deleteProxy = async (proxy: string) => {
  try {
    await axios.get(`/delete/?proxy=${encodeURIComponent(proxy)}`)
    message.success('删除成功')
    fetchProxies()
  } catch (error) {
    message.error('删除失败')
  }
}

const testProxy = async (proxy: string) => {
  testingProxy.value = proxy
  try {
    const res = await axios.get(`/api/test/?proxy=${encodeURIComponent(proxy)}`)
    testResults.value[proxy] = res.data
    if (res.data.success) {
      message.success(`测试成功! 延迟: ${res.data.latency_ms}ms`)
    } else {
      message.warning(`测试失败: ${res.data.error}`)
    }
  } catch (error) {
    message.error('测试请求失败')
  } finally {
    testingProxy.value = null
  }
}

const batchDelete = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要删除的代理')
    return
  }
  
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedRowKeys.value.length} 个代理吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await axios.post('/api/delete_batch/', { proxies: selectedRowKeys.value })
        message.success('批量删除成功')
        selectedRowKeys.value = []
        selectedRows.value = []
        fetchProxies()
      } catch (error) {
        message.error('批量删除失败')
      }
    }
  })
}

const onSelectChange = (keys: string[], rows: Proxy[]) => {
  selectedRowKeys.value = keys
  selectedRows.value = rows
}

const clearFilters = () => {
  filters.value = { https: '', region: '', source: '' }
  pagination.value.current = 1
  fetchProxies()
}

const exportProxies = (format: string) => {
  const params = new URLSearchParams({
    format,
    count: '100'
  })
  if (filters.value.https) params.append('type', filters.value.https === 'true' ? 'https' : '')
  if (filters.value.region) params.append('region', filters.value.region)
  
  window.open(`/export/?${params}`, '_blank')
  message.success(`正在导出 ${format.toUpperCase()} 格式`)
}

onMounted(() => {
  fetchProxies()
})
</script>

<template>
  <div class="proxy-list">
    <!-- Filter Bar -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :xs="24" :sm="12" :md="6" :lg="4">
          <a-select
            v-model:value="filters.https"
            placeholder="协议类型"
            allowClear
            style="width: 100%"
            @change="() => { pagination.current = 1; fetchProxies() }"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="true">HTTPS</a-select-option>
            <a-select-option value="false">HTTP</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6" :lg="4">
          <a-input
            v-model:value="filters.region"
            placeholder="搜索地区"
            allowClear
            @pressEnter="() => { pagination.current = 1; fetchProxies() }"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6" :lg="4">
          <a-input
            v-model:value="filters.source"
            placeholder="搜索来源"
            allowClear
            @pressEnter="() => { pagination.current = 1; fetchProxies() }"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6" :lg="12">
          <a-space>
            <a-button type="primary" @click="() => { pagination.current = 1; fetchProxies() }">
              <SearchOutlined /> 搜索
            </a-button>
            <a-button @click="clearFilters">
              清除筛选
            </a-button>
            <a-button @click="fetchProxies">
              <ReloadOutlined /> 刷新
            </a-button>
            <a-button 
              type="primary" 
              danger 
              @click="batchDelete"
              :disabled="selectedRowKeys.length === 0"
            >
              <DeleteOutlined /> 批量删除 ({{ selectedRowKeys.length }})
            </a-button>
            <a-dropdown>
              <a-button>
                <DownloadOutlined /> 导出
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="txt" @click="exportProxies('txt')">
                    📄 TXT 格式 (仅 IP:Port)
                  </a-menu-item>
                  <a-menu-item key="json" @click="exportProxies('json')">
                    📋 JSON 格式 (完整信息)
                  </a-menu-item>
                  <a-menu-item key="csv" @click="exportProxies('csv')">
                    📊 CSV 格式 (表格)
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- Table -->
    <a-card class="table-card" :bordered="false">
      <a-table
        :columns="columns"
        :dataSource="proxies"
        :loading="loading"
        :pagination="{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total: number) => `共 ${total} 条`
        }"
        :rowKey="(record: Proxy) => record.proxy"
        :rowSelection="{
          selectedRowKeys,
          onChange: onSelectChange
        }"
        :scroll="{ x: 1400 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'latency'">
            <span :style="{ color: getLatencyColor(record.latency), fontWeight: 'bold' }">
              <ThunderboltOutlined v-if="record.latency > 0 && record.latency < 500" />
              {{ getLatencyLabel(record.latency) }}
            </span>
          </template>
          <template v-else-if="column.key === 'https'">
            <a-tag :color="record.https ? 'green' : 'blue'">
              {{ record.https ? 'HTTPS' : 'HTTP' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="复制">
                <a-button size="small" @click="copyProxy(record.proxy)">
                  <CopyOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="测试">
                <a-button 
                  size="small" 
                  :loading="testingProxy === record.proxy"
                  @click="testProxy(record.proxy)"
                >
                  <ExperimentOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button size="small" danger @click="deleteProxy(record.proxy)">
                  <DeleteOutlined />
                </a-button>
              </a-tooltip>
              <template v-if="testResults[record.proxy]">
                <a-tag v-if="testResults[record.proxy].success" color="success">
                  <CheckCircleOutlined /> {{ testResults[record.proxy].latency_ms }}ms
                </a-tag>
                <a-tag v-else color="error">
                  <CloseCircleOutlined /> 失败
                </a-tag>
              </template>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.proxy-list {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.filter-card {
  margin-bottom: 16px;
  border-radius: 12px;
}

.table-card {
  border-radius: 12px;
}

.table-card :deep(.ant-table) {
  border-radius: 8px;
}
</style>
