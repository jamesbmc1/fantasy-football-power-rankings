<script setup lang="ts">
import { ref, watch } from 'vue'
import { fetchStandings, fetchPowerRankings } from '../api/sleeperApi'
import type { StandingsResponse, RankedTeam } from '../types'

const leagueId = ref('')
const week = ref(1)
const userRosterId = ref<number | null>(null)
const targetRosterId = ref<number | null>(null)

const teams = ref<RankedTeam[]>([])
const standings = ref<StandingsResponse | null>(null)
const isLoading = ref(false)
const isLoadingTeams = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

const loadTeams = async () => {
  if (!leagueId.value.trim()) return
  
  isLoadingTeams.value = true
  try {
    const data = await fetchPowerRankings(leagueId.value.trim(), week.value)
    teams.value = data
    // Reset selections if teams change significantly
    userRosterId.value = null
    targetRosterId.value = null
  } catch (err) {
    console.error('Failed to load teams', err)
  } finally {
    isLoadingTeams.value = false
  }
}

// Watch for leagueId changes to load teams list
watch([leagueId, week], () => {
  if (leagueId.value.length > 5) {
    loadTeams()
  }
})

const loadStandings = async () => {
  if (!leagueId.value.trim() || !userRosterId.value || !targetRosterId.value) {
    error.value = 'Please fill in all fields.'
    return
  }

  isLoading.value = true
  error.value = null
  hasSearched.value = true

  try {
    standings.value = await fetchStandings(
      leagueId.value.trim(),
      week.value,
      userRosterId.value,
      targetRosterId.value
    )
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch standings'
    standings.value = null
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6 text-slate-300">
    <!-- Header & Search -->
    <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-sm">
      <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 mb-6">
        League Standings
      </h1>
      
      <form @submit.prevent="loadStandings" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">League ID</label>
          <input 
            type="text" 
            v-model="leagueId"
            @blur="loadTeams"
            placeholder="Sleeper ID"
            class="w-full bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 outline-none focus:ring-emerald-500 focus:border-emerald-500"
          >
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">Week</label>
          <select 
            v-model="week"
            class="w-full bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 outline-none focus:ring-emerald-500"
          >
            <option v-for="w in 17" :key="w" :value="w">Week {{ w }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">Your Team</label>
          <select 
            v-model="userRosterId"
            :disabled="isLoadingTeams || teams.length === 0"
            class="w-full bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 outline-none focus:ring-emerald-500"
          >
            <option :value="null">Select Team</option>
            <option v-for="team in teams" :key="team.owner_name" :value="team.roster_id">
              {{ team.owner_name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">Rival Team</label>
          <select 
            v-model="targetRosterId"
            :disabled="isLoadingTeams || teams.length === 0"
            class="w-full bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 outline-none focus:ring-emerald-500"
          >
            <option :value="null">Select Rival</option>
            <option v-for="team in teams" :key="team.owner_name" :value="team.roster_id">
              {{ team.owner_name }}
            </option>
          </select>
        </div>

        <button 
          type="submit"
          :disabled="isLoading || !userRosterId || !targetRosterId"
          class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-2.5 px-5 rounded-lg transition-colors disabled:opacity-50"
        >
          {{ isLoading ? 'Loading...' : 'Compare' }}
        </button>
      </form>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-xl">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center h-64 bg-slate-800 rounded-xl border border-slate-700">
      <div class="text-emerald-400 font-medium animate-pulse">Calculating standings...</div>
    </div>

    <!-- Empty State -->
    <div v-if="!hasSearched && !isLoading" class="flex flex-col justify-center items-center h-64 bg-slate-800 rounded-xl border border-slate-700 text-slate-400">
      <p class="text-lg">Select teams to view detailed standings and rivalries.</p>
    </div>

    <!-- Data Display -->
    <div v-if="standings" class="space-y-8">
      
      <!-- Rivalry Section -->
      <section>
        <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <span class="text-emerald-400">⚔️</span> Head-to-Head Rivalry
        </h2>
        <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
              <tr>
                <th class="px-6 py-4">Manager</th>
                <th class="px-6 py-4">VS Rival</th>
                <th class="px-6 py-4">Wins</th>
                <th class="px-6 py-4">Losses</th>
                <th class="px-6 py-4">Ties</th>
                <th class="px-6 py-4">PF</th>
                <th class="px-6 py-4">PA</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rival in standings.rivals" :key="rival.owner_name" class="border-b border-slate-700 hover:bg-slate-700/30 transition-colors">
                <td class="px-6 py-4 font-bold text-white">{{ rival.owner_name }}</td>
                <td class="px-6 py-4 text-emerald-400 font-medium">{{ rival.rival_name }}</td>
                <td class="px-6 py-4 font-mono">{{ rival.wins }}</td>
                <td class="px-6 py-4 font-mono">{{ rival.losses }}</td>
                <td class="px-6 py-4 font-mono">{{ rival.ties }}</td>
                <td class="px-6 py-4 font-mono text-green-400">{{ rival.points_user.toFixed(2) }}</td>
                <td class="px-6 py-4 font-mono text-red-400">{{ rival.points_rival.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <!-- Regular Standings -->
        <section>
          <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span class="text-emerald-400">📊</span> Regular Season H2H
          </h2>
          <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
            <div class="overflow-x-auto">
              <table class="w-full text-sm text-left">
                <thead class="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
                  <tr>
                    <th class="px-6 py-4">Manager</th>
                    <th class="px-6 py-4">W-L-T</th>
                    <th class="px-6 py-4">Pct</th>
                    <th class="px-6 py-4">PF</th>
                    <th class="px-6 py-4">PA</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="team in standings.regular" :key="team.owner_name" 
                      :class="['border-b border-slate-700 hover:bg-slate-700/30 transition-colors', 
                               team.owner_name === teams.find(t => t.roster_id === userRosterId)?.owner_name ? 'bg-emerald-500/10' : '']">
                    <td class="px-6 py-4 font-bold text-white">{{ team.owner_name }}</td>
                    <td class="px-6 py-4 font-mono">{{ team.wins }}-{{ team.losses }}-{{ team.ties }}</td>
                    <td class="px-6 py-4 font-mono">{{ team.win_pct.toFixed(3) }}</td>
                    <td class="px-6 py-4 font-mono">{{ team.points.toFixed(1) }}</td>
                    <td class="px-6 py-4 font-mono text-slate-500">{{ team.opponent_points.toFixed(1) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- All-Play Standings -->
        <section>
          <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span class="text-emerald-400">🌍</span> All-Play Record
          </h2>
          <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
            <div class="overflow-x-auto">
              <table class="w-full text-sm text-left">
                <thead class="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
                  <tr>
                    <th class="px-6 py-4">Manager</th>
                    <th class="px-6 py-4">W-L</th>
                    <th class="px-6 py-4">Win Pct</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="team in standings.all_play" :key="team.owner_name"
                      :class="['border-b border-slate-700 hover:bg-slate-700/30 transition-colors', 
                               team.owner_name === teams.find(t => t.roster_id === userRosterId)?.owner_name ? 'bg-emerald-500/10' : '']">
                    <td class="px-6 py-4 font-bold text-white">{{ team.owner_name }}</td>
                    <td class="px-6 py-4 font-mono">{{ team.all_play_wins }}-{{ team.all_play_losses }}</td>
                    <td class="px-6 py-4 font-mono">{{ team.win_pct.toFixed(3) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
