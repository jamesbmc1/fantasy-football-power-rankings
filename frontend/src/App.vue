<script setup lang="ts">
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue';
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">

    <NavBar />

    <div class="max-w-6xl mx-auto">
      <RouterView />
    </div>
  </div>
</template>