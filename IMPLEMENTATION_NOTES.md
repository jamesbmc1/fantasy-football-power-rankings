# Implementation notes: from the original project to the analytics update

## What was kept

Vue 3, TypeScript, Vite, Tailwind, ApexCharts, FastAPI, Pandas and Sleeper remain the stack. The existing 45/40/15 weighting and 0–100 index scale remain. H2H standings, all-play records and rivalry comparisons remain available. Existing API URLs still work, now through the shared service. No database, authentication system or hosting migration was introduced.

## Earlier foundation work

The blue dashboard became black/charcoal with white text, subtle borders, gold index accents and muted green/red Z-scores. LeagueSelector and useLeague replaced independent page-local league/week fields and save selections in browser storage. Search, top-manager/average/team-count cards, projection Z-scores, inline methodology, accessible focus states, mobile layout and a matching favicon were added.

The original standings integer cast was removed so fractional scores determine the correct winner. All-play ties are separate from losses and receive half credit. Dashboard and history now use the same week's projection basis. Documentation was corrected to describe cumulative scoring production rather than unused weekly-normalization calculations.

## Four new features

1. **Rank movement (dashboard).** Previous comparable rank minus the current cumulative ranking, presented as upward or downward movement. All tied biggest movers are listed. Shared ranks remove arbitrary ordering among equal ratings. No prior week or a projection-availability change produces N/A.
2. **Schedule advantage (standings).** A zero-centered horizontal bar chart and exact table compare actual H2H win equivalents with expected wins from weekly all-play fractions. Positive means more actual wins; negative means fewer. Both sides exclude byes and median bonus games. This describes the schedule, not a forecast or management quality.
3. **Expanded team detail.** Roster-ID links open a page with current rank/movement, index, H2H record and expected wins. Separate aligned charts show index and rank, with rank 1 at the top. Another chart compares weekly points with weekly league average. Contributions explain how baseline 50 plus scoring/all-play/projections produces the clipped index. Exact weekly history is expandable.
4. **Week in review (dashboard).** A horizontal single-week scoring chart beneath the rankings, sorted highest first. The average reference line, week selector and manager highlight let users inspect an individual week without changing the cumulative rankings. An expandable table provides full names and exact values.

## Structural changes and why

- `src/services/analytics.py` builds one snapshot containing rankings, history, weekly scoring, schedule metrics and standings. This avoids separate page calculations drifting apart.
- `src/app.py` is now a thin API layer over that service. `/analytics/{league_id}/{week}` is the primary frontend endpoint; legacy routes delegate to it. Input and upstream-error handling prevent avoidable raw failures.
- `src/api_clients/sleeper.py` adds NFL state so the service can determine a conservative completed-week cutoff.
- `src/utils/calculations.py` adds schedule advantage and valid-pair filtering, respects commissioner score overrides including zero, handles zero-variance Z-scores, shares equal ranks and sorts tie-adjusted standings correctly.
- `useAnalytics.ts` owns a single frontend instance; `analyticsState.ts` isolates loading/error/race handling for tests. Navigation reuses data; league/week/refresh changes fetch a new snapshot. Older responses cannot replace newer choices.
- `MetricChart.vue` centralizes chart style and axes. `WeeklyScores.vue` owns single-week controls. `AnalyticsNotice.vue` explains the active data scope and limitations.
- Types cover the complete response. Roster IDs provide stable team selection even if manager names duplicate or contain URL punctuation. Name-based links remain supported only when unambiguous.

## Verified issues and corrections

- Commissioner custom scores were ignored; they now override raw scores consistently.
- Joining null matchup IDs could invent games between bye teams. Only two-team non-null matchup groups count as H2H games.
- Equal ratings previously received different ordinal ranks. Competition ranking now shares ranks at four-decimal index precision.
- All-play ordering previously ignored half-credit ties when sorting. It now uses tie-adjusted win percentage.
- Unplayed/current weeks could be processed as meaningful results. Analysis now uses completed regular-season weeks and stops at incomplete data.
- The original /v1 projections endpoint returned empty player objects. The client now uses Sleeper’s separate projections feed and converts player rows into a player-ID map. Draft-position-only entries remain unavailable; missing starter projections neutralize the component league-wide without redistributing its weight.

## Math and verification

Expected wins add (weekly all-play wins + half weekly all-play ties) / other teams for weeks with a valid H2H game. Schedule advantage subtracts that sum from actual wins plus half actual ties. Independent hand calculations and randomized tied-score leagues verify conservation: when every team is paired, expected wins and actual win equivalents both total half the team-games. Tests also independently reconstruct the weighted Power Index and reconcile dashboard, history, and contributions.

The latest audit passed 51 backend tests, seven frontend tests, TypeScript checking and the production build. A live Week 1 audit of league 1402478683377176576 independently recomputed Power Index values, expected wins and scheduled results for all ten teams, and checked dashboard/history agreement and JSON numeric validity. Earlier browser checks used sample Sleeper responses through the real FastAPI/Pandas pipeline. The latest audit did not revalidate the deployed Render/Vercel environment or perform a new browser layout review.

## Boundaries to understand before sharing

Current NFL weeks are included only after Sleeper advances its state. This may lag Monday night results. Fantasy playoffs are excluded; league start/playoff settings determine the window. History is reconstructed, not archived snapshots, and can change after corrections. Missing projection data can affect the rating scale, so the UI describes the fallback and suppresses movement across availability changes. The Power Index's weights are design choices, not a validated model of future wins.

The build still reports the existing large JavaScript chunk warning, and backend tests report a dependency deprecation warning. Neither prevents the tests/build from passing. No deployment or commit was made. Deploy the new backend before the frontend because the frontend now calls `/analytics`.

## Specification audit — September 15, 2026

The shared snapshot, roster-ID selection, remembered navigation, completed regular-season scope, 45/40/15 rating formula, all-play ties and scheduled-game expected wins match the documented requirements. The data pipeline accepts a supplied NFL league ID rather than embedding one league in its calculations.

The audit corrected an inconsistency where teams with no valid H2H games were omitted from the H2H table while appearing elsewhere. Those teams now remain visible with zero games and zero H2H PF/PA, while their scores still count in all-play and weekly charts. Two regression tests cover partial and league-wide byes. Commissioner score overrides now use explicit numeric types to avoid Pandas’ deprecated implicit conversion. The rank-movement description was corrected to previous rank minus current rank.

Projection availability confirms usable scoring data for each occupied starter; it does not confirm complete custom scoring coverage. Team detail and the League Guide now explain that missing projected categories are treated as zero and may differ from Sleeper’s displayed totals. Exact bonus/kicking parity, frozen historical projections, playoff/median-game support, and deployed hosting verification are outside the verified behavior. No weights or missing-data policy were changed by this audit.
