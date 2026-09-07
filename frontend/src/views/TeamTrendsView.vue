<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalytics } from '../composables/useAnalytics'
import { useLeague } from '../composables/useLeague'
import MetricChart from '../components/MetricChart.vue'
import AnalyticsNotice from '../components/AnalyticsNotice.vue'
const route = useRoute()
const { leagueId, refreshKey } = useLeague()
const { analytics, isLoading, error } = useAnalytics()
watch(() => route.params.leagueId, id => { if (/^\d+$/.test(String(id))) leagueId.value = String(id) }, { immediate: true })
const candidates = computed(() => analytics.value?.rankings.filter(t => route.params.rosterId ? t.roster_id === Number(route.params.rosterId) : t.owner_name === route.params.ownerName) || [])
const team = computed(() => candidates.value.length === 1 ? candidates.value[0] : undefined)
const history = computed(() => analytics.value?.history.filter(t => t.roster_id === team.value?.roster_id) || [])
const current = computed(() => history.value[history.value.length - 1])
const categories = computed(() => history.value.map(t => `W${t.week}`))
const contributions = computed(() => team.value ? [
  { name: 'Scoring production · 45%', value: team.value.scoring_contribution },
  { name: 'All-play performance · 40%', value: team.value.all_play_contribution },
  { name: `Starter projections · 15%${team.value.projections_available ? '' : ' · unavailable'}`, value: team.value.projection_contribution },
] : [])
const movement = computed(() => { const c = team.value?.rank_change; return c == null ? 'No comparable previous ranking' : c > 0 ? `↑ ${c} places from last week` : c < 0 ? `↓ ${Math.abs(c)} places from last week` : 'No change from last week' })
const signed = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}`
</script>
<template>
  <div class="space-y-6">
    <RouterLink to="/" class="back-link">← Back to rankings</RouterLink>
    <div v-if="isLoading" class="empty-state" role="status"><h2>Loading team analysis…</h2></div>
    <div v-else-if="error" class="empty-state" role="alert"><p>{{ error }}</p><button class="button-primary" @click="refreshKey++">Try again</button></div>
    <template v-else>
      <AnalyticsNotice />
      <div v-if="!team || !current" class="empty-state"><h2>{{ candidates.length > 1 ? 'This manager name matches multiple teams.' : 'No team history available.' }}</h2><p>Open a manager from the rankings table to select their roster, or choose a completed week.</p></div>
      <template v-else>
        <header class="page-heading"><div><p class="eyebrow">THE STORY BEHIND THE RANK</p><h1>{{ team.owner_name }}</h1><p class="page-description">Cumulative rankings and weekly scoring through week {{ analytics?.through_week }}.</p></div></header>
        <section class="team-summary"><article class="summary-card"><p class="eyebrow">LEAGUE RANK</p><h2>#{{ team.rank }}</h2><p>{{ movement }}</p></article><article class="summary-card"><p class="eyebrow">POWER INDEX</p><h2>{{ team.power_index.toFixed(2) }}</h2><p>Relative to this league</p></article><article class="summary-card"><p class="eyebrow">H2H RECORD</p><h2>{{ current.wins }}–{{ current.losses }}–{{ current.ties }}</h2><p>Actual opponent results · W–L–T</p></article><article class="summary-card"><p class="eyebrow">EXPECTED WINS</p><h2>{{ current.expected_wins.toFixed(2) }}</h2><p>{{ signed(current.schedule_advantage) }} schedule advantage</p><p>Based on scores, not a forecast</p></article></section>
        <section class="ranking-panel"><div class="panel-heading"><div><h2>Season trajectory</h2><p>Two aligned charts: rating strength above, league position below. Rank 1 is at the top.</p></div></div><MetricChart :categories="categories" :series="[{ name: 'Power Index', data: history.map(t => t.power_index) }]" :min="0" :max="100" label="Cumulative Power Index by included week" /><MetricChart :categories="categories" :series="[{ name: 'League rank', data: history.map(t => t.rank) }]" reversed integer :min="1" :max="Math.max(2, analytics?.rankings.length || 2)" :colors="['#b2b2bc']" label="Cumulative league rank by included week, rank one at the top" /><p class="table-note">Reconstructed using currently available scores and projections; later corrections can revise history. Data notes identify weeks with unavailable projections.</p></section>
        <section class="ranking-panel"><div class="panel-heading"><div><h2>Scoring by week</h2><p>Your weekly score versus the average team score in that same week.</p></div></div><MetricChart :categories="categories" :series="[{ name: team.owner_name, data: history.map(t => t.points) }, { name: 'League average', data: history.map(t => t.league_average) }]" :min="Math.min(0, ...history.map(t => t.points), ...history.map(t => t.league_average))" label="Team weekly points compared with weekly league average" /></section>
        <section class="ranking-panel"><div class="panel-heading"><div><h2>What makes up this rating?</h2><p>Each contribution is measured in Power Index points, added to a baseline of 50.</p></div></div><div class="contribution-list"><div v-for="part in contributions" :key="part.name"><span>{{ part.name }}</span><strong :class="{ positive: part.value > 0, negative: part.value < 0 }">{{ signed(part.value) }}</strong></div><div class="contribution-total"><span>50 + contributions, capped at 0–100</span><strong>{{ team.power_index.toFixed(2) }}</strong></div></div><p class="table-note">{{ team.projections_available ? 'Projection data is available for every occupied starter this week.' : 'Complete starter projections are unavailable. Every team receives a neutral projection contribution; the remaining weights are unchanged.' }} Displayed contributions may differ from the total by a rounding cent.</p></section>
        <details class="ranking-panel chart-data"><summary>View exact weekly history</summary><div class="table-scroll"><table class="power-table"><thead><tr><th>Week</th><th>Rank</th><th>Index</th><th>Your points</th><th>League average</th><th>Projection data</th></tr></thead><tbody><tr v-for="row in history" :key="row.week"><td>{{ row.week }}</td><td>{{ row.rank }}</td><td>{{ row.power_index.toFixed(2) }}</td><td>{{ row.points.toFixed(2) }}</td><td>{{ row.league_average.toFixed(2) }}</td><td>{{ row.projections_available ? 'Available' : 'Unavailable' }}</td></tr></tbody></table></div></details>
      </template>
    </template>
  </div>
</template>
