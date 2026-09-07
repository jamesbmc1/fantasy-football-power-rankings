import test from 'node:test'
import assert from 'node:assert/strict'

let instance = 0
async function state(storage) {
  globalThis.localStorage = storage
  return import(`../src/composables/useLeague.ts?test=${instance++}`)
}

test('restores a league and week, shares refs across pages, and persists changes', async () => {
  let saved = JSON.stringify({ leagueId: '123456789', week: 6 })
  const { useLeague } = await state({ getItem: () => saved, setItem: (_, value) => { saved = value } })
  const dashboard = useLeague(), standings = useLeague()
  assert.equal(dashboard.leagueId.value, '123456789')
  assert.equal(dashboard.week.value, 6)
  assert.equal(dashboard.leagueId, standings.leagueId)
  standings.week.value = 9
  assert.equal(dashboard.week.value, 9)
  assert.deepEqual(JSON.parse(saved), { leagueId: '123456789', week: 9 })
  dashboard.leagueId.value = ''
  dashboard.week.value = 1
  assert.deepEqual(JSON.parse(saved), { leagueId: '', week: 1 })
})

test('invalid saved values fall back to an empty league and week one', async () => {
  const { useLeague } = await state({ getItem: () => JSON.stringify({ leagueId: 'bad/id', week: 99 }), setItem() {} })
  assert.equal(useLeague().leagueId.value, '')
  assert.equal(useLeague().week.value, 1)
})

test('malformed saved JSON does not break startup', async () => {
  const { useLeague } = await state({ getItem: () => '{broken', setItem() {} })
  assert.equal(useLeague().leagueId.value, '')
  assert.equal(useLeague().week.value, 1)
})

test('navigation state works when browser storage is blocked', async () => {
  const { useLeague } = await state({ getItem() { throw new Error('blocked') }, setItem() { throw new Error('blocked') } })
  assert.doesNotThrow(() => { useLeague().leagueId.value = '456789'; useLeague().week.value = 3 })
  assert.equal(useLeague().leagueId.value, '456789')
  assert.equal(useLeague().week.value, 3)
})
