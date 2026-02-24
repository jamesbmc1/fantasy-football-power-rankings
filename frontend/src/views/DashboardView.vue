<script setup lang="ts">
import { ref } from 'vue'
import { fetchPowerRankings } from '../api/sleeperApi'
import type { RankedTeam } from '../types'

// state variables
const leagueId = ref('')
const week = ref(1)
const rankings = ref<RankedTeam[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

// 2. Fetch function triggered by the search button
const loadRankings = async () => {
  if (!leagueId.value.trim()) {
    error.value = 'Please enter a valid Sleeper League ID.'
    return
  }

  isLoading.value = true
  error.value = null
  hasSearched.value = true

  try {
    rankings.value = await fetchPowerRankings(leagueId.value.trim(), week.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch rankings'
    rankings.value = []
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    
    <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 shrink-0">
        Power Rankings
      </h1>
      
      <form @submit.prevent="loadRankings" class="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
        
        <div class="w-full sm:w-auto">
          <label for="league-id" class="sr-only">League ID</label>
          <input 
            id="league-id" 
            type="text" 
            v-model="leagueId"
            placeholder="Enter Sleeper League ID"
            class="w-full bg-slate-900 border border-slate-600 text-white text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block p-2.5 outline-none placeholder-slate-500"
          >
        </div>

        <div class="w-full sm:w-auto flex items-center gap-3">
          <label for="week-select" class="text-slate-400 font-medium whitespace-nowrap">Week</label>
          <select 
            id="week-select" 
            v-model="week"
            class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block p-2.5 outline-none"
          >
            <option v-for="w in 17" :key="w" :value="w">{{ w }}</option>
          </select>
          
          <button 
            type="submit"
            :disabled="isLoading"
            class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-2.5 px-5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Loading...' : 'Search' }}
          </button>
        </div>
      </form>
    </div>

    <div v-if="!hasSearched && !isLoading" class="flex flex-col justify-center items-center h-64 bg-slate-800 rounded-xl border border-slate-700 text-slate-400">
      <p class="text-lg">Enter your League ID to generate power rankings.</p>
    </div>

    <div v-else-if="isLoading" class="flex justify-center items-center h-64 bg-slate-800 rounded-xl border border-slate-700">
      <div class="text-emerald-400 font-medium animate-pulse">Crunching the numbers...</div>
    </div>

    <div v-else-if="error" class="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-xl">
      {{ error }}
    </div>

    <div v-else-if="rankings.length > 0" class="overflow-hidden bg-slate-800 rounded-xl border border-slate-700 shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-slate-300">
          <thead class="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
            <tr>
              <th scope="col" class="px-6 py-4">Rank</th>
              <th scope="col" class="px-6 py-4">Manager</th>
              <th scope="col" class="px-6 py-4">Power Index</th>
              <th scope="col" class="px-6 py-4">Z-Points</th>
              <th scope="col" class="px-6 py-4">Z-Wins</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="team in rankings" 
              :key="team.owner_id"
              class="border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors"
            >
              <td class="px-6 py-4 font-bold text-white text-lg">#{{ team.rank }}</td>
              <td class="px-6 py-4">
                <router-link :to="`/trends/${leagueId}/${team.owner_id}`" class="font-bold text-emerald-400 hover:text-emerald-300 hover:underline">
                  {{ team.owner_id }}
                </router-link>
              </td>
              <td class="px-6 py-4 font-mono text-white">{{ team.power_index.toFixed(2) }}</td>
              <td class="px-6 py-4 font-mono" :class="team.z_points > 0 ? 'text-green-400' : 'text-red-400'">
                {{ team.z_points > 0 ? '+' : '' }}{{ team.z_points.toFixed(2) }}
              </td>
              <td class="px-6 py-4 font-mono" :class="team.z_wins > 0 ? 'text-green-400' : 'text-red-400'">
                {{ team.z_wins > 0 ? '+' : '' }}{{ team.z_wins.toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>