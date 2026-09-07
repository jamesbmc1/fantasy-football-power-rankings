# Local development

Use two terminal windows, starting in this project directory. Python 3.11 or newer and Node 22.12+ are suitable for the pinned Python dependencies and Vite 7. Create a fresh environment; do not reuse the virtual environments bundled in the original ZIP.

## Backend

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest trio
python -m uvicorn src.app:app --reload --port 8000
```

Open http://localhost:8000/docs to inspect and try API requests. The backend root path has no handler; a 404 there is expected. Run the server from the project root so `src.app` imports correctly.

## Frontend (second terminal)

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The API defaults to http://localhost:8000. If you have an existing frontend/.env.local pointing to Render, set VITE_API_BASE_URL=http://localhost:8000 and restart Vite. If port 5173 is occupied, stop the other process or use `npm run dev -- --port 5173 --strictPort`; other ports are not in the current backend CORS allowlist.

## Verification

From the project root, with the virtual environment active:

```sh
python -m pytest src/tests -q
```

From frontend:

```sh
npm test
npm run build
```

Use a league ID and a completed week. Compare dashboard values to that team's trend for the same week, inspect standings and rivalry results, and check the browser's Network panel for failed requests. Mocked tests do not prove the live Sleeper projections endpoint is available. Test live requests separately. Preseason shows an empty state. Analysis excludes the current NFL week until Sleeper advances and stops before incomplete weeks.

Local source edits do not update Vercel or Render. Deployment requires updating the repository connected to those services.

## Dashboard and navigation

The league selector is shared by all pages. Submit a numeric league ID with Load league; changing Through week refreshes the active page immediately. Both choices are saved in this browser. Forget clears the league and resets the week. No account is required, and selections do not sync between devices.

The dashboard summaries and projection column use the shared analytics response. Searching managers only filters visible rows; it does not recalculate ranks. Manager links open team detail with the shared week. Direct trend links adopt their league ID. Switching leagues from a trend returns to rankings because that manager may not exist in the new league.

Standings automatically loads the remembered league and initially compares the first two ranked managers. Choose a different pair to update the comparison immediately. All pages share the new /analytics endpoint; the older API URLs delegate to the same calculation service.

Frontend state tests run with Node 22.12+ using `npm test` in frontend. They cover remembered selections, shared state, malformed or unavailable storage, stale responses, forgetting, and retries.
