import type { RankedTeam, TrendData, StandingsResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const fetchPowerRankings = async (leagueId: string, week: number): Promise<RankedTeam[]> => {
    const response = await fetch(`${BASE_URL}/rankings/${leagueId}/${week}`);
    if (!response.ok) throw new Error('Failed to fetch rankings');
    return response.json();
};

export const fetchTeamTrends = async (leagueId: string, ownerName: string, currentWeek: number): Promise<TrendData[]> => {
    const response = await fetch(`${BASE_URL}/trends/${leagueId}/${encodeURIComponent(ownerName)}/${currentWeek}`);
    if (!response.ok) throw new Error('Failed to fetch trends');
    return response.json();
};

export const fetchStandings = async (leagueId: string, week: number, userRosterId: number, targetRosterId: number): Promise<StandingsResponse> => {
    const response = await fetch(`${BASE_URL}/standings/${leagueId}/${week}/${userRosterId}/${targetRosterId}`);
    if (!response.ok) throw new Error('Failed to fetch standings');
    return response.json();
};

export async function fetchAnalytics(leagueId: string, week: number): Promise<import('../types').LeagueAnalytics> {
    const response = await fetch(`${BASE_URL}/analytics/${encodeURIComponent(leagueId)}/${week}`);
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Unable to load league analysis. Please try again.');
    }
    return response.json();
}
