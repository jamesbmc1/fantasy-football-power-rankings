import { useLeague } from './useLeague'
import { fetchAnalytics } from '../api/sleeperApi'
import { createAnalyticsState } from './analyticsState'

// One snapshot is shared across all pages. Navigation does not refetch history.
const state = createAnalyticsState(useLeague(), fetchAnalytics)
export function useAnalytics() { return state }
