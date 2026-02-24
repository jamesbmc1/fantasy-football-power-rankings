<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchTeamTrends } from '../api/sleeperApi'
import type { TrendData } from '../types'

const route = useRoute()
const router = useRouter()

// 1. Grab variables (Ensure these match your router/index.ts path exactly!)
const leagueId = route.params.leagueId as string
const ownerName = route.params.ownerName as string

// State
const week = ref(5)
const trendData = ref<TrendData[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

// 2. Extract the fetch logic into a reusable function
const loadTrends = async () => {
  isLoading.value = true
  error.value = null
  try {
    trendData.value = await fetchTeamTrends(leagueId, ownerName, week.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load trends'
  } finally {
    isLoading.value = false
  }
}

// 3. Run it once when the page first loads
onMounted(() => {
  loadTrends()
})

// 4. Automatically run it again whenever the 'week' dropdown changes
watch(week, () => {
  loadTrends()
})

const chartOptions = computed(() => ({
  chart: {
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'inherit'
  },
  theme: { mode: 'dark' },
  // Emerald for Power Index, Sky Blue for Rank
  colors: ['#34d399', '#38bdf8'], 
  stroke: {
    curve: 'smooth',
    width: [4, 3],
    dashArray: [0, 6], // Solid line for Power Index, Dashed line for Rank to tell them apart
    dropShadow: { enabled: true, top: 4, left: 0, blur: 4, opacity: 0.1 }
  },
  xaxis: {
    categories: trendData.value.map(d => `Week ${d.week}`),
    labels: { style: { colors: '#94a3b8' } },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  // We change yaxis to an array so we can have two different scales!
  yaxis: [
    {
      seriesName: 'Power Index',
      labels: { style: { colors: '#34d399' } },
      title: { text: 'Power Index', style: { color: '#34d399', fontWeight: 600 } },
    },
    {
      seriesName: 'Rank',
      opposite: true, // This puts the Rank numbers on the RIGHT side of the screen
      reversed: true, // This flips the axis so Rank #1 is at the top!
      labels: { 
        style: { colors: '#38bdf8' },
        formatter: (value: number) => Math.round(value).toString() // Keeps ranks as whole numbers
      },
      title: { text: 'League Rank', style: { color: '#38bdf8', fontWeight: 600 } },
    }
  ],
  grid: {
    borderColor: '#334155',
    strokeDashArray: 4,
    xaxis: { lines: { show: true } }
  },
  tooltip: { theme: 'dark' },
  legend: {
    position: 'top',
    labels: { colors: '#f8fafc' }
  }
}))

const chartSeries = computed(() => [
  {
    name: 'Power Index',
    type: 'line',
    data: trendData.value.map(d => Number(d.power_index.toFixed(2)))
  },
  {
    name: 'Rank',
    type: 'line',
    data: trendData.value.map(d => d.rank)
  }
])
</script>

<template>
  <div class="space-y-6">

    <div class="flex items-center justify-between">
      <button 
        @click="router.push('/')"
        class="flex items-center gap-2 text-slate-400 hover:text-emerald-400 transition-colors font-medium bg-slate-800 px-4 py-2 rounded-lg border border-slate-700 hover:border-emerald-500/50"
      >
        <ArrowLeft class="w-5 h-5" />
        Back to Dashboard
      </button>
    </div>

    <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-sm flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-extrabold text-white">
          {{ ownerName }}'s <span class="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Season Trends</span>
        </h1>
        <p class="text-slate-400 mt-1">League ID: {{ leagueId }}</p>
      </div>
      
      <div class="hidden sm:block">
        <label for="week-select" class="text-slate-400 font-medium mr-3">Data up to Week</label>
        <select
            id="week-select" 
            v-model="week"class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 p-2.5 outline-none"
            >
            <option v-for="w in 17" :key="w" :value="w">{{ w }}</option>
        </select>
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center items-center h-96 bg-slate-800 rounded-xl border border-slate-700">
      <div class="text-emerald-400 font-medium animate-pulse">Rendering analytics...</div>
    </div>

    <div v-else-if="error" class="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-xl">
      {{ error }}
    </div>

    <div v-else class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl h-[500px]">
      <apexchart 
        type="line" 
        height="100%" 
        :options="chartOptions" 
        :series="chartSeries"
      ></apexchart>
    </div>

  </div>
</template>