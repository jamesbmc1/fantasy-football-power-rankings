<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAnalytics } from '../composables/useAnalytics'
import MetricChart from './MetricChart.vue'
const { analytics } = useAnalytics()
const selectedWeek = ref(1)
const highlighted = ref<number | null>(null)
watch(analytics, data => { selectedWeek.value = data?.through_week || 1; highlighted.value = null }, { immediate: true })
const scores = computed(() => (analytics.value?.weekly_scores || []).filter(t => t.week === selectedWeek.value).sort((a, b) => b.points - a.points || a.roster_id - b.roster_id))
</script>
<template>
  <details v-if="scores.length" class="ranking-panel week-review" open>
    <summary>Week in review <span>Single-week scoring</span></summary>
    <div class="panel-heading"><div><h2>Week {{ selectedWeek }} only</h2><p>Raw weekly points, ordered highest to lowest. The line marks the league average.</p></div><div class="chart-controls"><div><label for="score-week">Scoring week</label><select id="score-week" v-model="selectedWeek"><option v-for="w in analytics?.weeks" :key="w" :value="w">Week {{ w }}</option></select></div><div><label for="highlight-team">Highlight manager</label><select id="highlight-team" v-model="highlighted"><option :value="null">All managers</option><option v-for="t in analytics?.rankings" :key="t.roster_id" :value="t.roster_id">{{ t.owner_name }}</option></select></div></div></div>
    <MetricChart kind="bar" horizontal distributed :categories="scores.map(s => s.owner_name)" :series="[{ name: 'Weekly points', data: scores.map(s => s.points) }]" :colors="scores.map(s => s.roster_id === highlighted ? '#d9bd83' : '#86868f')" :average="scores[0]?.league_average" :min="Math.min(0, ...scores.map(s => s.points))" :height="Math.max(280, scores.length * 42)" :label="`Week ${selectedWeek} scoring compared with the league average`" />
    <details class="chart-data"><summary>View exact scores</summary><div class="table-scroll"><table class="power-table"><thead><tr><th>Manager</th><th>Points</th><th>League average</th></tr></thead><tbody><tr v-for="s in scores" :key="s.roster_id"><td>{{ s.owner_name }}</td><td>{{ s.points.toFixed(2) }}</td><td>{{ s.league_average.toFixed(2) }}</td></tr></tbody></table></div></details>
  </details>
</template>
