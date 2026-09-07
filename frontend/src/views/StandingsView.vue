<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAnalytics } from '../composables/useAnalytics'
import { useLeague } from '../composables/useLeague'
import AnalyticsNotice from '../components/AnalyticsNotice.vue'
import MetricChart from '../components/MetricChart.vue'
const { analytics, isLoading, error } = useAnalytics()
const { leagueId, refreshKey } = useLeague()
const first = ref<number | null>(null)
const second = ref<number | null>(null)
watch(analytics, data => { first.value = data?.rankings[0]?.roster_id ?? null; second.value = data?.rankings[1]?.roster_id ?? null }, { immediate: true })
const schedule = computed(() => [...(analytics.value?.schedule || [])].sort((a, b) => b.schedule_advantage - a.schedule_advantage || a.roster_id - b.roster_id))
const extent = computed(() => Math.max(1, ...schedule.value.map(t => Math.abs(t.schedule_advantage))) * 1.15)
const signed = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}`
const rivalry = computed(() => {
  if (first.value === null || second.value === null || first.value === second.value) return null
  const a = analytics.value?.weekly_scores.filter(t => t.roster_id === first.value) || []
  const b = analytics.value?.weekly_scores.filter(t => t.roster_id === second.value) || []
  const pairs = a.flatMap(t => { const opponent = b.find(o => o.week === t.week); return opponent ? [{ ...t, opponent: opponent.points }] : [] })
  return { first: a[0]?.owner_name, second: b[0]?.owner_name, wins: pairs.filter(t => t.points > t.opponent).length, losses: pairs.filter(t => t.points < t.opponent).length, ties: pairs.filter(t => t.points === t.opponent).length, points: pairs.reduce((sum, t) => sum + t.points, 0), opponent: pairs.reduce((sum, t) => sum + t.opponent, 0), weeks: pairs.length }
})
</script>
<template>
  <div class="space-y-6 standings-page">
    <header class="page-heading"><div><p class="eyebrow">RESULTS & OPPORTUNITY</p><h1>Standings & rivalry<span class="heading-dot">.</span></h1><p class="page-description">Compare your record with your scoring performance and any other manager.</p></div></header>
    <div v-if="!leagueId" class="empty-state"><h2>Your league’s records, explained.</h2><p>Load a league above to explore standings and schedule advantage.</p></div>
    <div v-else-if="isLoading" class="empty-state" role="status"><h2>Calculating league results…</h2></div>
    <div v-else-if="error" class="empty-state" role="alert"><p>{{ error }}</p><button class="button-primary" @click="refreshKey++">Try again</button></div>
    <template v-else-if="analytics">
      <AnalyticsNotice />
      <div v-if="!analytics.rankings.length" class="empty-state"><h2>No completed weeks yet.</h2><p>Standings appear after a completed regular-season week is available.</p></div>
      <template v-else>
        <section class="ranking-panel">
          <div class="panel-heading"><div><h2>Actual vs. expected wins</h2><p>Schedule advantage = actual win equivalents − expected wins. Ties count as half a win.</p></div></div>
          <MetricChart kind="bar" horizontal distributed :categories="schedule.map(t => t.owner_name)" :series="[{ name: 'Schedule advantage', data: schedule.map(t => t.schedule_advantage) }]" :min="-extent" :max="extent" :average="0" reference-label="Even" :colors="schedule.map(t => t.schedule_advantage > 0 ? '#d9bd83' : '#92929b')" :height="Math.max(280, schedule.length * 42)" label="Schedule advantage in win equivalents, centered at zero" />
          <p class="chart-explanation">Left of zero: fewer wins than scoring would suggest. Right: more wins. Expected wins sum your weekly chance of beating a uniformly chosen league opponent. This describes scheduling outcomes, not future wins or manager skill. Byes and extra median games are excluded from both sides.</p>
          <div class="table-scroll"><table class="power-table"><thead><tr><th scope="col">Manager</th><th scope="col">H2H games</th><th scope="col">Actual wins + ½ ties</th><th scope="col">Expected wins</th><th scope="col">Difference</th></tr></thead><tbody><tr v-for="team in schedule" :key="team.roster_id"><td>{{ team.owner_name }}</td><td>{{ team.games }}</td><td>{{ team.actual_wins.toFixed(1) }}</td><td>{{ team.expected_wins.toFixed(2) }}</td><td>{{ signed(team.schedule_advantage) }}</td></tr></tbody></table></div><p class="table-note">Actual win equivalents include half credit for ties. Values are rounded for display; calculations use full precision.</p>
        </section>
        <div class="standings-grid">
          <section class="ranking-panel"><div class="panel-heading"><div><h2>Head-to-head record</h2><p>Actual results against scheduled opponents in included completed weeks.</p></div></div><div class="table-scroll"><table class="power-table"><thead><tr><th scope="col">Manager</th><th scope="col">W–L–T</th><th scope="col">Win %</th><th scope="col">PF</th><th scope="col">PA</th></tr></thead><tbody><tr v-for="team in analytics.regular" :key="team.roster_id"><td>{{ team.owner_name }}</td><td>{{ team.wins }}–{{ team.losses }}–{{ team.ties }}</td><td>{{ (team.win_pct * 100).toFixed(1) }}%</td><td>{{ team.points.toFixed(2) }}</td><td>{{ team.opponent_points.toFixed(2) }}</td></tr></tbody></table></div><p class="table-note">PF / PA: points for / against in played H2H games. Sorted by win percentage, then points.</p></section>
          <section class="ranking-panel"><div class="panel-heading"><div><h2>All-play record</h2><p>If you faced every other team each week.</p></div></div><div class="table-scroll"><table class="power-table"><thead><tr><th scope="col">Manager</th><th scope="col">W–L–T</th><th scope="col">Win %</th></tr></thead><tbody><tr v-for="team in analytics.all_play" :key="team.roster_id"><td>{{ team.owner_name }}</td><td>{{ team.all_play_wins }}–{{ team.all_play_losses }}–{{ team.all_play_ties }}</td><td>{{ (team.win_pct * 100).toFixed(1) }}%</td></tr></tbody></table></div></section>
        </div>
        <section class="ranking-panel"><div class="panel-heading"><div><h2>Every-week rivalry</h2><p>Choose two managers to compare their scores in every included week, regardless of their actual opponents.</p></div></div><div class="chart-controls rivalry-controls"><div><label for="first-manager">First manager</label><select id="first-manager" v-model="first"><option v-for="t in analytics.rankings" :key="t.roster_id" :value="t.roster_id">{{ t.owner_name }}</option></select></div><div><label for="second-manager">Second manager</label><select id="second-manager" v-model="second"><option v-for="t in analytics.rankings" :key="t.roster_id" :value="t.roster_id">{{ t.owner_name }}</option></select></div></div><div v-if="rivalry" class="rivalry-result"><p>{{ rivalry.first }} <span>vs.</span> {{ rivalry.second }}</p><strong>{{ rivalry.wins }}–{{ rivalry.losses }}–{{ rivalry.ties }}</strong><p>First manager’s hypothetical W–L–T across {{ rivalry.weeks }} weeks</p><p>{{ rivalry.points.toFixed(2) }} points vs. {{ rivalry.opponent.toFixed(2) }}</p></div><p v-else class="chart-explanation" role="status">Choose two different managers to compare.</p></section>
      </template>
    </template>
  </div>
</template>
