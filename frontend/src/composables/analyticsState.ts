import { ref, watch } from 'vue'
import type { Ref } from 'vue'
import type { LeagueAnalytics } from '../types'

type LeagueContext = { leagueId: Ref<string>; week: Ref<number>; refreshKey: Ref<number> }
type FetchSnapshot = (leagueId: string, week: number) => Promise<LeagueAnalytics>

export function createAnalyticsState(context: LeagueContext, fetchSnapshot: FetchSnapshot) {
    const analytics = ref<LeagueAnalytics | null>(null)
    const isLoading = ref(false)
    const error = ref('')
    const stop = watch([context.leagueId, context.week, context.refreshKey], async ([id, week], _, onCleanup) => {
        let active = true
        onCleanup(() => { active = false })
        analytics.value = null
        error.value = ''
        isLoading.value = !!id
        if (!id) return
        try {
            const snapshot = await fetchSnapshot(id, week)
            if (active) analytics.value = snapshot
        } catch (err) {
            if (active) error.value = err instanceof Error ? err.message : 'Unable to load analytics.'
        } finally {
            if (active) isLoading.value = false
        }
    }, { immediate: true })
    return { analytics, isLoading, error, stop }
}
