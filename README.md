# Sleeper Fantasy Football Power Rankings

## Project Overview

This platform is a full-stack data analytics application designed to provide objective, statistically normalized power rankings for fantasy football leagues. By integrating directly with the Sleeper API, the system bypasses the limitations of standard win-loss records—which are often skewed by schedule luck—and provides a **"Power Index"** based on scoring consistency, all-play records, and roster strength.

The application allows league managers to identify the "true" best teams by stripping away the noise of head-to-head scheduling.

---

## 🚀 Key Features

- **Power Rankings Dashboard:** A comprehensive leaderboard ranking teams by their Power Index, featuring Z-Score breakdowns for points and all-play performance.
- **Season Trends:** Interactive ApexCharts visualizations showing a team's Power Index and League Rank progression over the season.
- **League Standings & All-Play:** Detailed tables for regular H2H standings and "All-Play" records (your record if you played every team every week).
- **Rivalry Simulator:** A head-to-head comparison tool that simulates a matchup between two managers for every week of the season to determine who is statistically superior.

---

## 🛠 Technical Architecture

The project is a modern full-stack application:

#### Backend: FastAPI & Pandas
- **FastAPI:** Asynchronous Python backend managing data orchestration.
- **Pandas Engine:** Processes raw Sleeper JSON data into a statistical pipeline.
- **Asynchronous Data Fetching:** Uses `asyncio.gather` and `httpx` to concurrently fetch matchup and projection data, managed by a semaphore to respect API rate limits.

#### Frontend: Vue 3 & TypeScript
- **Framework:** Vue 3 with the Composition API and Vite.
- **Styling:** Tailwind CSS for a responsive, dark-themed UI.
- **Visualizations:** ApexCharts for rendering season performance trends.
- **Type Safety:** Full TypeScript integration ensuring data integrity between the API and the UI.

---

## 🧪 Statistical Methodology: The Power Index

The **Power Index** is the platform's core metric, defined mathematically as a T-Score (Mean=50, StdDev=10).

#### 1. Weighted Composite Formula
Final rankings are derived from three key pillars (configurable in `calculations.py`):
- **Scoring Consistency (45%):** Measured via season-long Z-Scores of total points.
- **All-Play Record (40%):** Calculated by ranking scores within each week to determine a theoretical record against the entire league.
- **Roster Projections (15%):** Incorporates predictive data based on current starters and league scoring settings.

#### 2. Calculation Process
1.  **Weekly Normalization:** Weekly points are converted to Z-scores using the league's mean and standard deviation for that specific week.
2.  **Aggregation:** Weekly Z-scores, total points, and all-play wins are summed to create a season-long profile.
3.  **T-Score Transformation:** The weighted composite Z-score is transformed into the Power Index:
    $$Power Index = 50 + (Composite Z-Score \times 10)$$
    *Scores are clipped between 0 and 100.*

---

## 📖 League Guide
For a non-technical explanation of how these rankings work, please refer to the **[Manager's Guide (LEAGUE_GUIDE.md)](./LEAGUE_GUIDE.md)**.

---

## 🚦 Getting Started

### Local Development

#### Backend
1. Navigate to the root directory.
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python src/app.py` (Starts at `http://localhost:8000`)

#### Frontend
1. Navigate to `/frontend`.
2. Install dependencies: `npm install`
3. Run the dev server: `npm run dev` (Starts at `http://localhost:5173`)

### Environment Variables
The frontend requires a `VITE_API_BASE_URL` if pointing to a production backend. Locally, it defaults to `http://localhost:8000`.

---

## 🌐 Deployment
- **Backend:** Hosted on Render (FastAPI).
- **Frontend:** Hosted on Vercel (Vue/Vite).
- **Live Site:** [fantasy-football-power-rankings-black.vercel.app](https://fantasy-football-power-rankings-black.vercel.app/)
