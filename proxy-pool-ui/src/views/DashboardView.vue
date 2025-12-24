<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()

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
    if (statsRes.data.stats) {
      dailyStats.value = statsRes.data.stats || [] 
    }
  } catch (error) {
    console.error('Failed to fetch usage stats', error)
  }
}

// Protocol chart data
const protocolChartData = computed(() => ({
  labels: Object.keys(stats.value.http_type).map(k => k.toUpperCase()),
  datasets: [{
    data: Object.values(stats.value.http_type),
    backgroundColor: ['#1890ff', '#52c41a', '#fa8c16'],
    hoverBackgroundColor: ['#40a9ff', '#73d13d', '#ffc069']
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
      label: t('dashboard.sourcesCount'),
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
      label: t('dashboard.regionTop8'),
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
      labels: [t('common.noData')],
      datasets: []
    }
  }
  
  const reversed = [...dailyStats.value].reverse() 
  
  return {
    labels: reversed.map(d => d.date.slice(5)), 
    datasets: [{
      label: t('dashboard.todayCalls'), 
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

// Safe accessor for top_users
const topUsers = computed(() => usageSummary.value?.top_users || [])

onMounted(() => {
  fetchStats()
  fetchUsageStats()
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
            <a-statistic :title="t('dashboard.totalProxies')" :value="stats.count">
              <template #prefix>
                <span class="stat-icon">🌐</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card http">
            <a-statistic :title="t('dashboard.httpProxies')" :value="stats.http_type.http || 0">
              <template #prefix>
                <span class="stat-icon">🔓</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card https">
            <a-statistic :title="t('dashboard.httpsProxies')" :value="stats.http_type.https || 0">
              <template #prefix>
                <span class="stat-icon">🔒</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card sources">
            <a-statistic :title="t('dashboard.sourcesCount')" :value="Object.keys(stats.source).length">
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
            <a-statistic :title="t('dashboard.todayCalls')" :value="usageSummary.today" prefix="📊" />
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-card class="stat-card usage">
            <a-statistic :title="t('dashboard.weekCalls')" :value="usageSummary.week" prefix="📈" />
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-card class="stat-card usage">
            <a-statistic :title="t('dashboard.activeUsers')" :value="usageSummary.active_users" prefix="👥" />
          </a-card>
        </a-col>
      </a-row>

      <!-- Charts Row -->
      <a-row :gutter="[16, 16]" class="charts-row">
        <a-col :xs="24" :lg="8">
          <a-card :title="t('dashboard.protocolDistribution')" class="chart-card">
            <div class="chart-container" v-if="stats.count > 0">
              <Doughnut :data="protocolChartData" :options="chartOptions" />
            </div>
            <a-empty v-else :description="t('common.noData')" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="8">
          <a-card :title="t('dashboard.sourceTop10')" class="chart-card">
            <div class="chart-container" v-if="Object.keys(stats.source).length > 0">
              <Bar :data="sourceChartData" :options="barChartOptions" />
            </div>
            <a-empty v-else :description="t('common.noData')" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="8">
          <a-card :title="t('dashboard.apiTrend')" class="chart-card">
            <div class="chart-container">
              <Line :data="usageTrendData" :options="lineChartOptions" />
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- Second Charts Row -->
      <a-row :gutter="[16, 16]" class="charts-row">
        <a-col :xs="24" :lg="12">
          <a-card :title="t('dashboard.regionTop8')" class="chart-card">
            <div class="chart-container" v-if="Object.keys(stats.region).length > 0">
              <Bar :data="regionChartData" :options="barChartOptions" />
            </div>
            <a-empty v-else :description="t('common.noData')" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card :title="t('dashboard.topUsers')" class="chart-card" v-if="topUsers.length > 0">
            <a-list :dataSource="topUsers" size="small">
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar :style="{ backgroundColor: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : index === 2 ? '#d48806' : '#1890ff' }">
                        {{ index + 1 }}
                      </a-avatar>
                    </template>
                    <template #title>{{ item[0] }}</template>
                    <template #description>{{ item[1] }} {{ t('dashboard.todayCalls') }}</template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
          <a-card :title="t('dashboard.topUsers')" class="chart-card" v-else>
            <a-empty :description="t('common.noData')" />
          </a-card>
        </a-col>
      </a-row>

      <!-- Quick Actions -->
      <a-row :gutter="[16, 16]" class="actions-row">
        <a-col :span="24">
          <a-card :title="t('dashboard.quickActions')">
            <a-space>
              <a-button type="primary" @click="fetchStats">
                🔄 {{ t('dashboard.refresh') }}
              </a-button>
              <router-link to="/proxies">
                <a-button type="default">
                  📋 {{ t('dashboard.viewProxies') }}
                </a-button>
              </router-link>
              <router-link to="/tools">
                <a-button type="default">
                  🧪 {{ t('dashboard.testTool') }}
                </a-button>
              </router-link>
              <router-link to="/admin">
                <a-button type="default">
                  ⚙️ {{ t('dashboard.adminPanel') }}
                </a-button>
              </router-link>
            </a-space>
            <div class="last-update" v-if="lastUpdate">
              {{ t('dashboard.lastUpdate') }}: {{ lastUpdate.toLocaleTimeString() }}
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

.stats-row, .charts-row, .actions-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.chart-card {
  border-radius: 12px;
  height: 100%;
}

.chart-container {
  height: 250px; /* Reduced specific height for responsiveness */
  position: relative;
}

.stat-icon {
  font-size: 24px;
  margin-right: 12px;
}

.last-update {
  margin-top: 16px;
  color: #8c8c8c;
  font-size: 12px;
  text-align: right;
}
</style>
