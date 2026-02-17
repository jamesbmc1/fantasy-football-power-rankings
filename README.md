# Sleeper Fantasy Football Power Rankings 🏈 📊

## 📖 Overview

This project is a Python-based data engineering tool that automates the generation of "Power Rankings" for Fantasy Football leagues. By interfacing with the **Sleeper API**, the application ingests raw matchup data, normalizes performance metrics using statistical Z-scores, and generates interactive visualizations to quantify "Luck vs. Skill."

The goal of this project was to move beyond simple Win/Loss records and create a **Power Index** that accurately reflects the strength of a roster regardless of weekly matchup variance.

---

## ⚙️ Key Features

- **Automated Data Fetching**: Retrieves and processes league data from the Sleeper API.
- **Smart Caching**: Implements a local JSON caching system to minimize API calls and latency during development and repeated runs.
- **Statistical Normalization**: Uses Z-scores to standardize disparate metrics (Points, Wins, Projections) onto a single scale.
- **Interactive Visualization**: Generates HTML-based charts using **Plotly** for analysis.
- **Unit Testing**: Comprehensive test suite using `pytest` to ensure calculation accuracy and API response handling.

---

## 🧮 The Math: How It Works

Fantasy football is high-variance. A team might score the second-highest points in the league but lose because they played the highest-scoring team. To account for this, I calculate a **Composite Power Index**.

### 1. Z-Score Calculation
For every metric (Points Scored, Wins, Projected Points), I calculate the Z-score for each team. This measures how many standard deviations a team is from the league average.

$$Z = \frac{x - \mu}{\sigma}$$

*Where $x$ is the team's value, $\mu$ is the league mean, and $\sigma$ is the standard deviation.*

### 2. Weighted Aggregation
The Composite Score is a weighted sum of the Z-scores based on the following distribution:

- **Points Scored (50%)**: The strongest indicator of actual team performance.
- **True Record (30%)**: Results still matter; winning contributes to the score.
- **Projected Points (20%)**: Accounts for roster potential and strength on paper.

### 3. The Power Index (0-100)
To make the data digestible, the raw composite score is transformed into a **T-Score** distribution (Mean = 50, Std Dev = 10) and clipped between 0 and 100.

---

## 📊 Visualizations Explained

The program generates three specific charts to help analyze the league:

### 1. Luck vs. Skill Scatter Plot
This plot compares a team's **Point Production (Skill)** against their **Win Record (Results)**.

- **Top-Right (Contenders):** High Points, High Wins. The best teams.
- **Bottom-Right (Unlucky):** High Points, Low Wins. These teams are playing well but facing tough opponents.
- **Top-Left (Frauds):** Low Points, High Wins. These teams are winning despite poor performance.
- **Bottom-Left (Bad):** Low Points, Low Wins. The worst overall teams.

### 2. League Standings Bar Chart
A sorted view of the league based on the calculated **Power Index**, colored by intensity. This often differs significantly from the official NFL standings.

### 3. Seasonal Trend Lines
A line graph tracking a specific owner's Power Index week-over-week. This is useful for identifying teams that are "getting hot" toward the playoffs or teams that are collapsing.

---

## 📂 Project Structure

```text
├── data/                   # Cached JSON responses (Auto-generated)
├── src/
│   ├── api_clients/        # Modules for External API interaction
│   │   └── sleeper.py      
│   ├── utils/              # Core logic and helper functions
│   │   ├── calculations.py 
│   │   └── visualizer.py   
├── tests/                  # Unit and integration tests
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

---

## 🛠️ Installation & Setup

Follow these steps to run the project locally.

### Prerequisites

- Python 3.8 or higher
- `pip` (Python Package Installer)

### 1. Clone the Repository

```bash
git clone https://github.com/jamesbmc1/fantasy-football-power-rankings.git
cd fantasy-football-power-rankings
```

### 2. Install Dependencies

It is recommended to use a virtual environment to keep your global Python setup clean.

```bash
# Create and activate a virtual environment (Windows)
python -m venv venv
# Activate It
.\venv\Scripts\activate
# Install required packages
pip install -r requirements.txt


# Create and activate virtual environment (Mac)
python3 -m venv venv
# Activate It
source venv/bin/activate
# Install required packages
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory. You will need your Sleeper League ID (found in the URL of your league on the Sleeper web app).

**File: .env**

```env
SLEEPER_LEAGUE_ID=1234567890
SEASON=2024
```

### 🚀 Running the Application

The script uses `argparse` to handle dynamic inputs. You can trigger the calculation and visualization directly from your terminal.

#### Command Syntax

```bash
# Windows
python -m src.main <week_number> "<owner_name>"

# Mac
python3 -m src.main <week_number> "<owner_name>"
```

**Arguments**

- `current_week` (Integer): The week number you want to calculate rankings for (e.g., 10). The script pulls data from Week 1 through this week.
- `owner_name` (String): The display name of the specific team owner you want to highlight in the "Trend" visualization.

> **Note**: If the name contains spaces, it must be enclosed in quotes.

#### Example Execution

To generate rankings for Week 12 and highlight Team Smith:

```bash
python main.py 12 "Team Smith"
```

### 📊 Expected Output

- **Console**: The script will print the calculated Power Rankings DataFrame directly to your terminal for a quick data check.
- **Browser**: Plotly will automatically launch your default web browser to display interactive charts, including:
  - Scatter Plot: Efficiency vs. Luck.
  - Bar Chart: Overall Power Score ranking.
  - Trend Line: Performance trajectory for the specified owner.

---

## 🧪 Running Tests

To verify the mathematical logic and Sleeper API integration, run the test suite using `python3 -m pytest`:

```bash
python3 -m pytest
```

