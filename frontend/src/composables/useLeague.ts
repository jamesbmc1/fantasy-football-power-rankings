import { ref, watch } from 'vue'

const STORAGE_KEY = 'fantasy-power-rankings:league'
function restore(): { leagueId: string; week: number } {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return {
      leagueId: typeof saved.leagueId === 'string' && /^\d+$/.test(saved.leagueId) ? saved.leagueId : '',
      week: Number.isInteger(saved.week) && saved.week >= 1 && saved.week <= 18 ? saved.week : 1,
    }
  } catch { return { leagueId: '', week: 1 } }
}
const saved = restore()
const leagueId = ref(saved.leagueId)
const week = ref(saved.week)
const refreshKey = ref(0)
watch([leagueId, week], () => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ leagueId: leagueId.value, week: week.value })) }
  catch { /* Navigation still works when browser storage is unavailable. */ }
}, { flush: 'sync' })

export function useLeague() { return { leagueId, week, refreshKey } }
