import { createRouter, createWebHistory } from 'vue-router'
// We will create these view files in the next step!
import DashboardView from '../views/DashboardView.vue'
import TeamTrendsView from '../views/TeamTrendsView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'dashboard',
            component: DashboardView
        },
        {
            path: '/trends/:leagueId/:ownerName',
            name: 'team-trends',
            component: TeamTrendsView
        }
    ]            
})

export default router