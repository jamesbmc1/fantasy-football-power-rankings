import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import TeamTrendsView from '../views/TeamTrendsView.vue'
import StandingsView from '../views/StandingsView.vue'

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
        },
        {
            path: '/standings',
            name: 'standings',
            component: StandingsView
        }
    ]            
})

export default router