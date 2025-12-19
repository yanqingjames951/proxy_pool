<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #fff; padding: 0 24px; display: flex; align-items: center">
      <h2 style="margin: 0">Proxy Pool Dashboard</h2>
    </a-layout-header>
    <a-layout-content style="margin: 24px 16px; padding: 24px; background: #fff; min-height: 280px">
      <RouterView />
    </a-layout-content>
    <a-layout-footer style="text-align: center">
      Proxy Pool ©2025 Created by Antigravity
    </a-layout-footer>
  </a-layout>
</template>

<style scoped>
</style>
