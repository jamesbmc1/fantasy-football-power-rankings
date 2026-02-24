export interface RankedTeam {
    rank: number;
    owner_id: string;
    power_index: number;
    z_points: number;
    z_wins: number;
    z_projected_points: number;
}

export interface TrendData {
    week: number;
    rank: number;
    power_index: number;
}