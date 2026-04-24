import type { RankedTeam, TrendData, StandingsResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const fetchPowerRankings = async (leagueId: string, week: number): Promise<RankedTeam[]> => {
    const response = await fetch(`${BASE_URL}/rankings/${leagueId}/${week}`);
    if (!response.ok) throw new Error('Failed to fetch rankings');
    return response.json();
};

export const fetchTeamTrends = async (leagueId: string, ownerName: string, currentWeek: number): Promise<TrendData[]> => {
    const response = await fetch(`${BASE_URL}/trends/${leagueId}/${ownerName}/${currentWeek}`);
    if (!response.ok) throw new Error('Failed to fetch trends');
    return response.json();
};

export const fetchStandings = async (leagueId: string, week: number, userRosterId: number, targetRosterId: number): Promise<StandingsResponse> => {
    const response = await fetch(`${BASE_URL}/standings/${leagueId}/${week}/${userRosterId}/${targetRosterId}`);
    if (!response.ok) throw new Error('Failed to fetch standings');
    return response.json();
};
