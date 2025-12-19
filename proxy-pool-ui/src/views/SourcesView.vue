<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

interface SourceStat {
  name: string
  total: number
  https: number
  http: number
  regions: Record<string, number>
}

const sources = ref<SourceStat[]>([])
const loading = ref(true)
const totalSources = ref(0)

const fetchSources = async () => {
  try {
    loading.value = true
    const res = await axios.get('/api/sources/')
    sources.value = res.data.sources.sort((a: SourceStat, b: SourceStat) => b.total - a.total)
    totalSources.value = res.data.total_sources
  } catch (error) {
    console.error('Failed to fetch sources', error)
  } finally {
    loading.value = false
  }
}

const getChartData = (source: SourceStat) => ({
  labels: ['HTTP', 'HTTPS'],
  datasets: [{
    data: [source.http, source.https],
    backgroundColor: ['#1890ff', '#52c41a'],
    borderRadius: 4
  }]
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1
      }
    }
  }
}

const columns = [
  {
    title: '来源名称',
    dataIndex: 'name',
    key: 'name',
    width: 180
  },
  {
    title: '总数',
    dataIndex: 'total',
    key: 'total',
    width: 100,
    sorter: (a: SourceStat, b: SourceStat) => a.total - b.total
  },
  {
    title: 'HTTP',
    dataIndex: 'http',
    key: 'http',
    width: 100
  },
  {
    title: 'HTTPS',
    dataIndex: 'https',
    key: 'https',
    width: 100
  },
  {
    title: '地区分布',
    key: 'regions',
    width: 300
  }
]

onMounted(() => {
  fetchSources()
})
</script>

<template>
  <div class="sources-view">
    <a-spin :spinning="loading">
      <!-- Summary Card -->
      <a-row :gutter="[16, 16]" class="summary-row">
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic title="活跃代理源" :value="totalSources">
              <template #prefix>
                <span class="stat-icon">📡</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic 
              title="总代理数" 
              :value="sources.reduce((sum, s) => sum + s.total, 0)"
            >
              <template #prefix>
                <span class="stat-icon">🌐</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic 
              title="最大来源" 
              :value="sources[0]?.name || '-'"
            >
              <template #prefix>
                <span class="stat-icon">🏆</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic 
              title="最大来源代理数" 
              :value="sources[0]?.total || 0"
            >
              <template #prefix>
                <span class="stat-icon">📊</span>
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- Sources Table -->
      <a-card title="代理源详情" class="table-card" :bordered="false">
        <template #extra>
          <a-button type="primary" @click="fetchSources">
            🔄 刷新
          </a-button>
        </template>
        
        <a-table
          :columns="columns"
          :dataSource="sources"
          :loading="loading"
          :rowKey="(record: SourceStat) => record.name"
          :pagination="{ pageSize: 10, showSizeChanger: true }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'total'">
              <a-tag color="blue">{{ record.total }}</a-tag>
            </template>
            <template v-else-if="column.key === 'http'">
              <a-tag color="processing">{{ record.http }}</a-tag>
            </template>
            <template v-else-if="column.key === 'https'">
              <a-tag color="success">{{ record.https }}</a-tag>
            </template>
            <template v-else-if="column.key === 'regions'">
              <div class="regions-container">
                <template v-if="Object.keys(record.regions).length > 0">
                  <a-tag 
                    v-for="entry in Object.entries(record.regions).slice(0, 5)" 
                    :key="entry[0]"
                    size="small"
                  >
                    {{ entry[0] }}: {{ entry[1] }}
                  </a-tag>
                  <a-tag v-if="Object.keys(record.regions).length > 5" size="small">
                    +{{ Object.keys(record.regions).length - 5 }} 更多
                  </a-tag>
                </template>
                <span v-else class="no-data">-</span>
              </div>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- Visual Cards -->
      <a-row :gutter="[16, 16]" class="visual-row" v-if="sources.length > 0">
        <a-col 
          v-for="source in sources.slice(0, 6)" 
          :key="source.name"
          :xs="24" 
          :sm="12" 
          :lg="8"
        >
          <a-card class="source-card">
            <template #title>
              <div class="source-title">
                <span>{{ source.name }}</span>
                <a-tag color="blue">{{ source.total }}</a-tag>
              </div>
            </template>
            <div class="mini-chart">
              <Bar :data="getChartData(source)" :options="chartOptions" />
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-empty 
        v-if="!loading && sources.length === 0" 
        description="暂无代理源数据，请先运行调度程序抓取代理" 
      />
    </a-spin>
  </div>
</template>

<style scoped>
.sources-view {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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

.stat-icon {
  font-size: 20px;
  margin-right: 8px;
}

.table-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.regions-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.no-data {
  color: #999;
}

.visual-row {
  margin-top: 16px;
}

.source-card {
  border-radius: 12px;
}

.source-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mini-chart {
  height: 120px;
}
</style>
