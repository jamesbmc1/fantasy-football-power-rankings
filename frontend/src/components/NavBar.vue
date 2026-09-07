<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { ChartNoAxesCombined } from 'lucide-vue-next'
const route = useRoute()
</script>
<template>
  <header class="site-header"><div class="nav-inner">
    <RouterLink to="/" class="brand"><span class="brand-icon"><ChartNoAxesCombined :size="21" /></span><span>Fantasy<span class="brand-secondary"> / Power Rankings</span></span></RouterLink>
    <nav class="page-nav" aria-label="Main navigation">
      <RouterLink to="/" :class="{ selected: route.name === 'dashboard' || route.name === 'team-trends' || route.name === 'team-detail' }">Rankings</RouterLink>
      <RouterLink to="/standings" :class="{ selected: route.name === 'standings' }">Standings & Rivalry</RouterLink>
    </nav>
  </div></header>
</template>
