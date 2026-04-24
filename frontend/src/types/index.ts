export interface RankedTeam {
    rank: number;
    roster_id: number;
    owner_name: string;
    power_index: number;
    z_points: number;
    z_all_play_wins: number;
    z_projected_points: number;
}

export interface TrendData {
    week: number;
    rank: number;
    power_index: number;
}

export interface RegularStanding {
    owner_name: string;
    wins: number;
    losses: number;
    ties: number;
    points: number;
    opponent_points: number;
    win_pct: number;
}

export interface RivalStanding {
    owner_name: string;
    rival_name: string;
    wins: number;
    losses: number;
    ties: number;
    points_user: number;
    points_rival: number;
}

export interface AllWinsStanding {
    owner_name: string;
    all_play_wins: number;
    all_play_losses: number;
    win_pct: number;
}

export interface StandingsResponse {
    regular: RegularStanding[];
    all_play: AllWinsStanding[];
    rivals: RivalStanding[];
}