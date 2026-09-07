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
    all_play_ties: number;
    win_pct: number;
}

export interface StandingsResponse {
    regular: RegularStanding[];
    all_play: AllWinsStanding[];
    rivals: RivalStanding[];
}
export interface AnalyticsTeam extends RankedTeam {
    rank_change: number | null;
    projections_available: boolean;
    scoring_contribution: number;
    all_play_contribution: number;
    projection_contribution: number;
    unclipped_index: number;
}
export interface TeamHistory extends AnalyticsTeam {
    week: number;
    points: number;
    league_average: number;
    wins: number;
    losses: number;
    ties: number;
    actual_wins: number;
    expected_wins: number;
    schedule_advantage: number;
}
export interface WeeklyScore {
    week: number;
    roster_id: number;
    owner_name: string;
    points: number;
    league_average: number;
}
export interface ScheduleTeam {
    roster_id: number;
    owner_name: string;
    wins: number;
    losses: number;
    ties: number;
    games: number;
    actual_wins: number;
    expected_wins: number;
    schedule_advantage: number;
}
export interface LeagueAnalytics {
    league_id: string;
    league_name: string;
    season: string;
    requested_week: number;
    through_week: number | null;
    weeks: number[];
    warnings: string[];
    rankings: AnalyticsTeam[];
    history: TeamHistory[];
    weekly_scores: WeeklyScore[];
    schedule: ScheduleTeam[];
    regular: (RegularStanding & { roster_id: number })[];
    all_play: (AllWinsStanding & { roster_id: number })[];
    generated_at: string;
}
