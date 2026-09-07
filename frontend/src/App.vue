<script setup lang="ts">
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import LeagueSelector from './components/LeagueSelector.vue'
</script>
<template>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <NavBar />
  <main id="main-content" class="app-main">
    <LeagueSelector />
    <RouterView />
    <footer class="app-footer"><span>Fantasy Power Rankings</span><span>League-relative analysis · Powered by Sleeper data</span></footer>
  </main>
</template>
