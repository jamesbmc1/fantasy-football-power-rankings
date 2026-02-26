# Sleeper Fantasy Football Power Rankings

## Project Overview

This platform is a full-stack data analytics application designed to provide objective, statistically normalized power rankings for fantasy football leagues. By integrating directly with the Sleeper API, the system bypasses the limitations of standard win-loss records—which are often skewed by schedule luck—and provides a "Power Index" based on scoring consistency, all-play records, and roster strength.

The architecture follows a cloud-native approach, utilizing a FastAPI backend for asynchronous data orchestration and a Pandas-driven statistical engine to calculate performance metrics.

---

## Technical Architecture

The project is divided into three primary layers:

#### 1. Backend Orchestration (FastAPI)**

The backend serves as a high-performance middleware that manages the complex lifecycle of league data retrieval.

- **Asynchronous Data Fetching:** Utilizes asyncio.gather and httpx to concurrently fetch up to 17 weeks of matchup and projection data. This reduces total request latency by processing external API calls in parallel rather than sequentially.

- **Traffic Control:** Implements an asyncio.Semaphore to throttle concurrent requests to external services, ensuring the application remains stable and avoids rate-limiting under high load.

- **CORS Middleware:** Configured to secure communication between the Render-hosted Python backend and the Vercel-hosted frontend.


#### 2. Statistical Logic Engine (Pandas)

The core of the application is a data science pipeline that transforms raw JSON responses into a normalized Power Index.

- **Z-Score Normalization:** To account for weekly scoring volatility, the engine calculates the Z-score for every team on a per-week basis. This identifies how many standard deviations a team is from the league mean, ensuring a "high-scoring week" across the league is weighted fairly against "low-scoring defensive weeks."

- **All-Play Record Calculation:** The system ranks every team's score within each week to determine their "All-Play" record—the theoretical record if a team had played every other manager in the league that week.

- **Weighted Composite Formula:** Final rankings are derived from a weighted average of three key pillars:

- Season-Long Points (50%): Measures raw scoring output.

- Actual Wins (30%): Acknowledges head-to-head success.

- Roster Projections (20%): Incorporates predictive data based on current starters and league scoring settings.


#### 3. Frontend Integration (TypeScript)

The client-side application consumes the API via a typed interface.

- **Type Safety:** Utilizes TypeScript interfaces to ensure data integrity between the Python backend's dictionary structures and the frontend's state management.

- **Environment-Aware:** Configured with dynamic base URLs to switch seamlessly between development and production environments.


## Statistical Methodology: The Power Index

The final output of the platform is the **Power Index**, which is mathematically defined as a T-Score.

#### Calculation Process

1. **Weekly Normalization:** Weekly points are converted to Z-scores using the league's mean and standard deviation for that specific week.
2. **Aggregation:** Weekly Z-scores, total points, and wins are summed to create a season-long profile.
3. **Composite Z-Score:** The weighted composite Z-score is transformed into a T-score using the formula:

$$Power Index = 50 + (Composite Z-Score \times 10)$$

This results in a distribution where 50 represents the league average. A score of 60 indicates a team is one standard deviation above average, while a 40 indicates one standard deviation below.


## Environment and Deployment
- **Runtime:** Python 3.11.4
- **Backend Infrastructure:** Render (Web Service)
- **Frontend Infrastructure:** Vercel
- **API Client:** Custom asynchronous Sleeper API wrapper


## How to Use the Platform
You can access the live deployment to analyze your own Sleeper league performance.

#### 1. Retrieve Your League ID
Navigate to your league on Sleeper.com. Your League ID is the long string of numbers found in the URL.

- **Example URL:** https://sleeper.com/leagues/1332124519619371008/matchup
- **League ID:** 1332124519619371008


#### 2. Access the Application: 
Navigate to the live site: https://fantasy-football-power-rankings-black.vercel.app/

> **Note**: Because the backend is hosted on Render's free tier, the server may need 30-60 seconds to "wake up" during the initial data load. Subsequent requests will be significantly faster.


#### 3. Analyze League Rankings
Once the data loads, the dashboard displays a comprehensive leaderboard.

**Power Index**: The primary metric for overall team strength, centered at 50.
**Z-Points & Z-Wins**: These represent Standard Deviations from the league average. 
  - **Positive Scores (+1.0 to +3.0)**: Indicate the manager is performing above the league average. A +2.0 means they are in the top 2.5% of historical performances for that metric.
  - **Zero (0.0)**: Represents exactly average performance.
  - **Negative Scores (-1.0 to -3.0)**: Indicate the manager is struggling relative to the field. A -2.0 suggests they are performing worse than 97.5% of the league.

  #### 4. Explore Individual Trends
  Click on any **Manager's Name** in the table to view their Season Trends. This provides a week-by-week visualization of their Power Index and League Rank, allowing you to track momentum and statistical consistency throughout the season.