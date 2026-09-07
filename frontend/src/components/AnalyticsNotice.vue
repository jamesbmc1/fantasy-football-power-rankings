<script setup lang="ts">
import { useAnalytics } from '../composables/useAnalytics'
const { analytics } = useAnalytics()
</script>
<template>
  <aside v-if="analytics" class="analysis-context">
    <p><strong>{{ analytics.league_name }}</strong> · {{ analytics.season }} · {{ analytics.through_week ? `Completed regular season through week ${analytics.through_week}` : 'No completed weeks yet' }}</p>
    <details v-if="analytics.warnings.length" class="data-notice"><summary>Data notes · {{ analytics.warnings.length }}</summary><ul><li v-for="note in analytics.warnings" :key="note">{{ note }}</li></ul></details>
    <p v-if="analytics.through_week !== analytics.requested_week" class="cutoff-note">Your selection includes weeks outside the completed regular-season data. Results below use {{ analytics.through_week ? `weeks through ${analytics.through_week}` : 'no weeks yet' }}.</p>
  </aside>
</template>
