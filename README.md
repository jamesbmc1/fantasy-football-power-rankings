# Sleeper Fantasy Football Power Rankings

A Vue and FastAPI application for exploring a Sleeper league beyond its win–loss records. The Power Index combines cumulative scoring production, all-play results, and available starter projections. It is a league-relative rating under chosen weights, not a validated forecast or proof of the strongest roster.

## Features

- Black/charcoal dashboard with manager search, summary cards, component Z-scores, and weekly rank changes. Tied leaders and tied biggest movers are included.
- Shared league ID and week across pages, remembered in browser storage. Load league refreshes; Forget clears the selection.
- Actual versus expected H2H wins with a zero-centered schedule-advantage chart.
- Team detail with aligned Power Index/rank trajectories, weekly scoring versus league average, and additive rating contributions.
- Week in review: a single-week scoring chart with a manager highlight and exact-data table.
- H2H and all-play standings, plus an every-week rivalry comparison that updates when a different manager is selected.

See [LEAGUE_GUIDE.md](LEAGUE_GUIDE.md) for the shareable explanation and [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for the changes from the original project.

## Architecture

`Sleeper API → client → analytics service → FastAPI → shared Vue state → views/charts`

- `src/api_clients/sleeper.py`: asynchronous HTTP requests with a concurrency limit, including NFL state.
- `src/utils/calculations.py`: score normalization, standings, all-play, Power Index, and expected-win math.
- `src/services/analytics.py`: validates complete weeks, applies the regular-season cutoff, handles optional projections, and builds one consistent league snapshot.
- `src/app.py`: `/analytics/{league_id}/{week}` plus compatible rankings, trends, and standings routes backed by the same service.
- `frontend/src/composables`: remembered league context and shared analytics loading/error/data state. The asynchronous state helper is tested independently.
- Vue views use the snapshot for every table and chart. New roster-ID team links avoid ambiguous display names; old name-based trend links remain supported when unambiguous.

Navigation reuses the snapshot. Changing league/week or pressing Load league fetches a new one. There is no database, login, cross-device preference sync, or archival snapshot storage.

## Math and data scope

For each team, standardize cumulative points, tie-adjusted cumulative all-play wins, and the selected included week's starter projections across the league (sample standard deviation). A constant component has Z-score zero.

`Power Index = clip(50 + 10 × (0.45 × scoring Z + 0.40 × all-play Z + 0.15 × projection Z), 0, 100)`

The weighted composite is not re-standardized, so the resulting index does not necessarily have standard deviation 10. Clipping can also shift its mean. Weekly scoring Z-scores are available internally but are not the index's scoring component. Equal index values at four-decimal precision share a competition rank, e.g. 1, 1, 3.

For each played H2H week:

`Expected wins = (all-play wins + 0.5 × all-play ties) / number of other teams`

Sum those fractions; subtract them from actual wins plus half the actual ties to obtain schedule advantage. Byes and median bonus games contribute to neither side. In a fully paired league, expected-win totals and actual win equivalents both equal half the number of team-games.

Only completed NFL regular-season weeks are included, from the league's configured start week to before fantasy playoffs. The current NFL week is excluded until Sleeper advances to the next week. This can lag Monday night results. An incomplete week stops the analysis instead of dropping teams. Commissioner score overrides, including zero, are respected.

If complete starter projections are unavailable for any team, the projection component is neutral for every team that week; the 45% and 40% weights remain unchanged. Movement is suppressed when projection availability changes. Data notes explain this in the UI. History is reconstructed from currently available data and can change after corrections.

## Run locally

See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for the full setup. From the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn src.app:app --reload --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000`; `VITE_API_BASE_URL` overrides it. Open `http://localhost:5173` for the site and `http://localhost:8000/docs` for API documentation.

## Validation

```sh
# Project root, with the virtual environment activated
python -m pip install pytest trio
python -m pytest src/tests -v

# Frontend
cd frontend
npm test
npm run build
```

Backend tests cover independent numerical examples, ties, fractional scores, byes, overrides, expected-win conservation, history agreement, missing projections, season cutoffs, input validation, and legacy endpoint agreement. Frontend tests cover persistence, shared selections, blocked storage, stale responses, forgetting, and retries. Mocked tests do not establish live Sleeper availability.

## Deployment

The existing setup uses Render for FastAPI and Vercel for Vue/Vite. Deploy the backend with the new `/analytics` route before deploying the updated frontend. The older routes remain available to the previous frontend, subject to the new completed-week scope.

Live site: [Fantasy Football Power Rankings](https://fantasy-football-power-rankings-black.vercel.app/). Local edits do not update the hosted site automatically unless they are pushed to a deployment-connected branch.
