<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAnalytics } from '../composables/useAnalytics'
import AnalyticsNotice from '../components/AnalyticsNotice.vue'
import WeeklyScores from '../components/WeeklyScores.vue'
import { useLeague } from '../composables/useLeague'
const { leagueId, week, refreshKey } = useLeague()
const { analytics, isLoading, error } = useAnalytics()
const rankings = computed(() => analytics.value?.rankings || [])
const displayWeek = computed(() => analytics.value?.through_week ?? week.value)
const movement = (change: number | null) => change === null ? 'N/A' : change > 0 ? `↑ ${change}` : change < 0 ? `↓ ${Math.abs(change)}` : '—'
const movers = computed(() => {
  const changes = rankings.value.filter(t => t.rank_change !== null)
  const up = Math.max(0, ...changes.map(t => t.rank_change!))
  const down = Math.min(0, ...changes.map(t => t.rank_change!))
  return { risers: changes.filter(t => up > 0 && t.rank_change === up), fallers: changes.filter(t => down < 0 && t.rank_change === down) }
})
const search = ref('')
const visibleTeams = computed(() => rankings.value.filter(team => (team.owner_name || '').toLowerCase().includes(search.value.toLowerCase())))
const leader = computed(() => rankings.value[0])
const leaders = computed(() => rankings.value.filter(t => t.rank === leader.value?.rank))
const average = computed(() => rankings.value.length ? (rankings.value.reduce((sum, t) => sum + t.power_index, 0) / rankings.value.length).toFixed(1) : '—')
const signed = (value: number) => {
  const rounded = Number(value.toFixed(2))
  return `${rounded > 0 ? '+' : ''}${rounded.toFixed(2)}`
}
</script>
<template>
  <div class="dashboard">
    <header class="page-heading"><div><p class="eyebrow">THE LEAGUE, IN PERSPECTIVE</p><h1>Power rankings<span class="heading-dot">.</span></h1><p class="page-description">A clearer picture of team performance, beyond the win–loss record.</p></div><span v-if="leagueId" class="context-pill">Through week {{ displayWeek }}</span></header>
    <div v-if="!leagueId" class="empty-state"><span class="eyebrow">WELCOME TO YOUR LEAGUE’S BIGGER PICTURE</span><h2>Every score tells a story.</h2><p>Load your league above to compare scoring production, all-play performance, and starter projections in one Power Index.</p><div class="empty-features"><span>01 / Power rankings</span><span>02 / Season trends</span><span>03 / Rivalry comparisons</span></div></div>
    <div v-else-if="isLoading" class="empty-state" role="status"><div class="loading-line"></div><h2>Building your league picture</h2><p>Fetching scores and calculating rankings. The first request may take a little longer.</p></div>
    <div v-else-if="error" class="empty-state" role="alert"><h2>We couldn’t load this league.</h2><p>{{ error }} Check the league ID and selected week, then try again.</p><button class="button-primary" @click="refreshKey++">Try again</button></div>
    <template v-else-if="rankings.length">
      <AnalyticsNotice />
      <section class="summary-grid" aria-label="League summary">
        <article class="summary-card"><p class="eyebrow">{{ leaders.length > 1 ? 'JOINT LEADERS' : 'TOP-RANKED MANAGER' }}</p><h2 class="leader-name">{{ leaders.length > 2 ? `${leaders.length} teams tied at #${leader?.rank}` : leaders.map(t => t.owner_name).join(', ') }}</h2><p><strong>{{ leader?.power_index.toFixed(1) }}</strong> Power Index</p><details v-if="leaders.length > 2" class="tied-managers"><summary>View tied managers</summary><p>{{ leaders.map(t => t.owner_name).join(', ') }}</p></details></article>
        <article class="summary-card"><p class="eyebrow">LEAGUE AVERAGE</p><h2>{{ average }}</h2><p>Power Index across all teams</p></article>
        <article class="summary-card"><p class="eyebrow">TEAMS RANKED</p><h2>{{ rankings.length.toString().padStart(2, '0') }}</h2><p>Cumulative results through Week {{ displayWeek }}</p></article>
      </section>
      <section class="movement-strip" aria-label="Weekly rank movement"><p><strong>Biggest riser{{ movers.risers.length > 1 ? 's' : '' }}</strong><span v-if="movers.risers.length">{{ movers.risers.map(t => t.owner_name).join(', ') }} · {{ movement(movers.risers[0]!.rank_change) }}</span><span v-else>No upward movement to report</span></p><p><strong>Biggest faller{{ movers.fallers.length > 1 ? 's' : '' }}</strong><span v-if="movers.fallers.length">{{ movers.fallers.map(t => t.owner_name).join(', ') }} · {{ movement(movers.fallers[0]!.rank_change) }}</span><span v-else>No downward movement to report</span></p><small>Versus the previous included week. N/A means no comparable previous ranking.</small></section>
      <section class="ranking-panel"><div class="panel-heading"><div><h2>The power table</h2><p>Select a manager to explore their season trends.</p></div><div><label class="sr-only" for="manager-search">Find a manager</label><input id="manager-search" v-model="search" placeholder="Find a manager…" type="search" /></div></div>
        <div class="table-scroll"><table class="power-table"><thead><tr><th scope="col">Rank</th><th scope="col">Change</th><th scope="col">Manager</th><th scope="col">Power Index</th><th scope="col">Scoring <span>Z-score</span></th><th scope="col">All-play <span>Z-score</span></th><th scope="col">Projections <span>Z-score</span></th></tr></thead><tbody>
          <tr v-for="team in visibleTeams" :key="team.roster_id"><td class="rank-number">{{ String(team.rank).padStart(2, '0') }}</td><td :class="{ positive: (team.rank_change || 0) > 0, negative: (team.rank_change || 0) < 0 }">{{ movement(team.rank_change) }}</td><td><RouterLink class="manager-link" :to="{ name: 'team-detail', params: { leagueId, rosterId: team.roster_id } }"><span class="manager-avatar" aria-hidden="true">{{ (team.owner_name || '?').slice(0, 2).toUpperCase() }}</span><span>{{ team.owner_name || 'Unknown manager' }}</span><span class="manager-arrow" aria-hidden="true">↗</span></RouterLink></td><td><div class="index-value">{{ team.power_index.toFixed(2) }}</div><div class="index-track" aria-hidden="true"><span :style="{ width: `${team.power_index}%` }"></span></div></td><td :class="{ 'positive': team.z_points > 0, 'negative': team.z_points < 0 }">{{ signed(team.z_points) }}</td><td :class="{ 'positive': team.z_all_play_wins > 0, 'negative': team.z_all_play_wins < 0 }">{{ signed(team.z_all_play_wins) }}</td><td :class="{ 'positive': team.z_projected_points > 0, 'negative': team.z_projected_points < 0 }">{{ team.projections_available ? signed(team.z_projected_points) : 'N/A' }}</td></tr>
          <tr v-if="!visibleTeams.length"><td colspan="7">No managers match “{{ search }}”.</td></tr>
        </tbody></table></div>
        <div class="table-note">Positive Z-scores are above the league average; negative scores are below it.</div>
      </section>
      <WeeklyScores />
    </template>
    <div v-else><AnalyticsNotice /><div class="empty-state"><h2>No completed rankings yet.</h2><p>Results appear after a completed regular-season week is available.</p></div></div>
    <details class="methodology"><summary>How the Power Index works <span>45% / 40% / 15%</span></summary><div class="methodology-grid"><p><strong>45% scoring production</strong>Cumulative points compared with the league average.</p><p><strong>40% all-play performance</strong>Results against every team each week, with half credit for ties.</p><p><strong>15% starter projections</strong>League-scored projections for starters in the selected week.</p></div><p class="methodology-note">The weighted standardized components are scaled around 50 and capped at 0–100. This is a relative rating, not a win probability. Missing projections contribute zero for every team in that week, without redistributing their weight. Equal index values share a rank. Historical ratings are reconstructed from currently available data.</p></details>
  </div>
</template>
