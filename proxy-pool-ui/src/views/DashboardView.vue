<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Filler
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler)

interface Stats {
  count: number
  http_type: Record<string, number>
  source: Record<string, number>
  region: Record<string, number>
}

interface UsageSummary {
  today: number
  week: number
  active_users: number
  top_users: [string, number][]
}

interface DailyStats {
  date: string
  total: number
  users: Record<string, number>
  actions: Record<string, number>
}

const stats = ref<Stats>({
  count: 0,
  http_type: {},
  source: {},
  region: {}
})

const usageSummary = ref<UsageSummary | null>(null)
const dailyStats = ref<DailyStats[]>([])
const loading = ref(true)
const lastUpdate = ref<Date | null>(null)

const fetchStats = async () => {
  try {
    loading.value = true
    const res = await axios.get('/count/')
    stats.value = res.data
    lastUpdate.value = new Date()
  } catch (error) {
    console.error('Failed to fetch stats', error)
  } finally {
    loading.value = false
  }
}

const fetchUsageStats = async () => {
  try {
    const [summaryRes, statsRes] = await Promise.all([
      axios.get('/api/usage/stats/').catch(() => ({ data: { stats: null } })),
      axios.get('/api/usage/stats/?days=7').catch(() => ({ data: { daily: [] } }))
    ])
    
    if (summaryRes.data.stats) {
      usageSummary.value = summaryRes.data.stats
    }
    if (statsRes.data.daily) {
      dailyStats.value = statsRes.data.daily
    }
  } catch (error) {
    console.error('Failed to fetch usage stats', error)
  }
}

// Protocol chart data
const protocolChartData = computed(() => ({
  labels: Object.keys(stats.value.http_type),
  datasets: [{
    data: Object.values(stats.value.http_type),
    backgroundColor: ['#1890ff', '#52c41a'],
    hoverBackgroundColor: ['#40a9ff', '#73d13d']
  }]
}))

// Source chart data
const sourceChartData = computed(() => {
  const sortedSources = Object.entries(stats.value.source)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
  
  return {
    labels: sortedSources.map(([name]) => name),
    datasets: [{
      label: '代理数量',
      data: sortedSources.map(([, count]) => count),
      backgroundColor: '#1890ff',
      borderRadius: 4
    }]
  }
})

// Region chart data  
const regionChartData = computed(() => {
  const sortedRegions = Object.entries(stats.value.region)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
  
  return {
    labels: sortedRegions.map(([name]) => name),
    datasets: [{
      label: '代理数量',
      data: sortedRegions.map(([, count]) => count),
      backgroundColor: '#722ed1',
      borderRadius: 4
    }]
  }
})

// Usage trend chart
const usageTrendData = computed(() => {
  if (!dailyStats.value || dailyStats.value.length === 0) {
    return {
      labels: ['暂无数据'],
      datasets: [{
        label: 'API 调用次数',
        data: [0],
        borderColor: '#1890ff',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        fill: true,
        tension: 0.4
      }]
    }
  }
  
  const reversed = [...dailyStats.value].reverse()
  return {
    labels: reversed.map(d => d.date.slice(5)), // MM-DD format
    datasets: [{
      label: 'API 调用次数',
      data: reversed.map(d => d.total),
      borderColor: '#1890ff',
      backgroundColor: 'rgba(24, 144, 255, 0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: '#1890ff'
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const
    }
  }
}

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}

onMounted(() => {
  fetchStats()
  fetchUsageStats()
  // Auto refresh every 30 seconds
  setInterval(fetchStats, 30000)
})
</script>

<template>
  <div class="dashboard">
    <a-spin :spinning="loading">
      <!-- Stats Cards -->
      <a-row :gutter="[16, 16]" class="stats-row">
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card total">
            <a-statistic title="总代理数" :value="stats.count">
              <template #prefix>
                <span class="stat-icon">🌐</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card http">
            <a-statistic title="HTTP 代理" :value="stats.http_type.http || 0">
              <template #prefix>
                <span class="stat-icon">🔓</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card https">
            <a-statistic title="HTTPS 代理" :value="stats.http_type.https || 0">
              <template #prefix>
                <span class="stat-icon">🔒</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card sources">
            <a-statistic title="代理源数量" :value="Object.keys(stats.source).length">
              <template #prefix>
                <span class="stat-icon">📡</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- Usage Stats Cards -->
      <a-row :gutter="[16, 16]" class="stats-row" v-if="usageSummary">
        <a-col :xs="24" :sm="8">
          <a-card class="stat-card usage">
            <a-statistic title="今日调用" :value="usageSummary.today" prefix="📊" />
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-card class="stat-card usage">
            <a-statistic title="本周调用" :value="usageSummary.week" prefix="📈" />
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-card class="stat-card usage">
            <a-statistic title="活跃用户" :value="usageSummary.active_users" prefix="👥" />
          </a-card>
        </a-col>
      </a-row>

      <!-- Charts Row -->
      <a-row :gutter="[16, 16]" class="charts-row">
        <a-col :xs="24" :lg="8">
          <a-card title="协议分布" class="chart-card">
            <div class="chart-container" v-if="stats.count > 0">
              <Doughnut :data="protocolChartData" :options="chartOptions" />
            </div>
            <a-empty v-else description="暂无数据" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="8">
          <a-card title="代理源 Top 10" class="chart-card">
            <div class="chart-container" v-if="Object.keys(stats.source).length > 0">
              <Bar :data="sourceChartData" :options="barChartOptions" />
            </div>
            <a-empty v-else description="暂无数据" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="8">
          <a-card title="API 调用趋势 (7天)" class="chart-card">
            <div class="chart-container">
              <Line :data="usageTrendData" :options="lineChartOptions" />
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- Second Charts Row -->
      <a-row :gutter="[16, 16]" class="charts-row">
        <a-col :xs="24" :lg="12">
          <a-card title="地区分布 Top 8" class="chart-card">
            <div class="chart-container" v-if="Object.keys(stats.region).length > 0">
              <Bar :data="regionChartData" :options="barChartOptions" />
            </div>
            <a-empty v-else description="暂无地区数据" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card title="Top 用户调用量" class="chart-card" v-if="usageSummary && usageSummary.top_users.length > 0">
            <a-list :dataSource="usageSummary.top_users" size="small">
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar :style="{ backgroundColor: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : index === 2 ? '#d48806' : '#1890ff' }">
                        {{ index + 1 }}
                      </a-avatar>
                    </template>
                    <template #title>{{ item[0] }}</template>
                    <template #description>{{ item[1] }} 次调用</template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
          <a-card title="Top 用户调用量" class="chart-card" v-else>
            <a-empty description="暂无使用数据" />
          </a-card>
        </a-col>
      </a-row>

      <!-- Quick Actions -->
      <a-row :gutter="[16, 16]" class="actions-row">
        <a-col :span="24">
          <a-card title="快捷操作">
            <a-space>
              <a-button type="primary" @click="fetchStats">
                🔄 刷新数据
              </a-button>
              <router-link to="/proxies">
                <a-button type="default">
                  📋 查看代理列表
                </a-button>
              </router-link>
              <router-link to="/tools">
                <a-button type="default">
                  🧪 代理测试工具
                </a-button>
              </router-link>
              <router-link to="/admin">
                <a-button type="default">
                  ⚙️ 管理面板
                </a-button>
              </router-link>
            </a-space>
            <div class="last-update" v-if="lastUpdate">
              最后更新: {{ lastUpdate.toLocaleTimeString() }}
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<style scoped>
.dashboard {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.stats-row {
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

.stat-card.total {
  border-left: 4px solid #1890ff;
}

.stat-card.http {
  border-left: 4px solid #52c41a;
}

.stat-card.https {
  border-left: 4px solid #faad14;
}

.stat-card.sources {
  border-left: 4px solid #722ed1;
}

.stat-card.usage {
  border-left: 4px solid #13c2c2;
}

.stat-icon {
  font-size: 20px;
  margin-right: 8px;
}

.charts-row {
  margin-bottom: 16px;
}

.chart-card {
  border-radius: 12px;
  height: 100%;
}

.chart-container {
  height: 250px;
  padding: 10px;
}

.actions-row .ant-card {
  border-radius: 12px;
}

.last-update {
  margin-top: 16px;
  color: #999;
  font-size: 12px;
}
</style>
