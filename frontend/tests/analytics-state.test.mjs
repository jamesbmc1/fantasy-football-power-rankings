import test from 'node:test'
import assert from 'node:assert/strict'
import { nextTick, ref } from 'vue'
import { createAnalyticsState } from '../src/composables/analyticsState.ts'
const context = () => ({ leagueId: ref(''), week: ref(1), refreshKey: ref(0) })
const flush = async () => { await Promise.resolve(); await nextTick() }

test('an older response cannot replace a newer selected week', async () => {
  const league = context(), pending = []
  const state = createAnalyticsState(league, (id, week) => new Promise(resolve => pending.push({ id, week, resolve })))
  league.leagueId.value = '123'; await nextTick()
  league.week.value = 2; await nextTick()
  assert.equal(pending.length, 2)
  pending[1].resolve({ league_id: '123', through_week: 2 }); await flush()
  pending[0].resolve({ league_id: '123', through_week: 1 }); await flush()
  assert.equal(state.analytics.value.through_week, 2)
  assert.equal(state.isLoading.value, false)
  state.stop()
})

test('forgetting a league clears results and ignores an in-flight request', async () => {
  const league = context(); let resolve
  const state = createAnalyticsState(league, () => new Promise(done => { resolve = done }))
  league.leagueId.value = '123'; await nextTick()
  league.leagueId.value = ''; await nextTick()
  resolve({ league_id: '123', through_week: 1 }); await flush()
  assert.equal(state.analytics.value, null)
  assert.equal(state.isLoading.value, false)
  assert.equal(state.error.value, '')
  state.stop()
})

test('refresh retries a failed request and exposes the error to every consumer', async () => {
  const league = context(); let calls = 0
  const state = createAnalyticsState(league, async () => {
    if (++calls === 1) throw new Error('Sleeper unavailable')
    return { league_id: '123', through_week: 1 }
  })
  league.leagueId.value = '123'; await nextTick(); await flush()
  assert.equal(state.error.value, 'Sleeper unavailable')
  assert.equal(state.isLoading.value, false)
  league.refreshKey.value++; await nextTick(); await flush()
  assert.equal(state.error.value, '')
  assert.equal(state.analytics.value.league_id, '123')
  assert.equal(calls, 2)
  state.stop()
})
