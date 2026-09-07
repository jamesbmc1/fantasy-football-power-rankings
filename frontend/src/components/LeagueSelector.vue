<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLeague } from '../composables/useLeague'
const { leagueId, week, refreshKey } = useLeague()
const route = useRoute()
const router = useRouter()
const draftId = ref(leagueId.value)
const error = ref('')
watch(leagueId, value => { draftId.value = value })
function apply() {
  const value = draftId.value.trim()
  if (!/^\d+$/.test(value)) { error.value = 'Enter a numeric Sleeper league ID.'; return }
  error.value = ''
  const changed = value !== leagueId.value
  leagueId.value = value
  if (!changed) refreshKey.value++
  if (changed && (route.name === 'team-trends' || route.name === 'team-detail')) router.push('/')
}
function forget() {
  leagueId.value = ''
  week.value = 1
  error.value = ''
  router.push('/')
}
</script>
<template>
  <section class="league-bar" aria-label="League settings">
    <div class="league-context"><span class="eyebrow">YOUR LEAGUE</span><p>{{ leagueId ? 'One league. Every perspective.' : 'Start with your Sleeper league.' }}</p></div>
    <form @submit.prevent="apply" class="league-form">
      <div class="league-input"><label for="league-id">Sleeper league ID</label><input id="league-id" v-model="draftId" inputmode="numeric" placeholder="Enter league ID" autocomplete="off" :aria-invalid="!!error" :aria-describedby="error ? 'league-error' : undefined" /></div>
      <div><label for="global-week">Through week</label><select id="global-week" v-model="week"><option v-for="w in 18" :key="w" :value="w">Week {{ w }}</option></select></div>
      <button type="submit" class="button-primary">Load league</button>
      <button v-if="leagueId" type="button" class="button-quiet" @click="forget">Forget</button>
    </form>
    <p v-if="error" id="league-error" role="alert" class="form-error">{{ error }}</p>
    <p class="league-note">{{ leagueId ? 'League and week remembered in this browser.' : 'Find your league ID in the URL of your league on Sleeper.' }}</p>
  </section>
</template>
