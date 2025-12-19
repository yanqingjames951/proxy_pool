<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

const stats = ref({
  count: 0,
  http_type: { http: 0, https: 0 },
  source: {}
});

const loading = ref(true);

const fetchStats = async () => {
  try {
    // Note: This URL assumes proxy set up in vite.config.ts or CORS enabled on backend
    const res = await axios.get('/api/count/'); 
    stats.value = res.data;
  } catch (error) {
    console.error('Failed to fetch stats', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchStats();
});
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else>
    <a-row :gutter="16">
      <a-col :span="8">
        <a-statistic title="Total Proxies" :value="stats.count" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="HTTP" :value="stats.http_type.http" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="HTTPS" :value="stats.http_type.https" />
      </a-col>
    </a-row>
    
    <a-divider />
    
    <h3>Source Distribution</h3>
    <a-list bordered :data-source="Object.entries(stats.source)">
      <template #renderItem="{ item }">
        <a-list-item>
          {{ item[0] }}: {{ item[1] }}
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>
