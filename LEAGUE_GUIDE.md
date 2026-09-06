# 🏆 Manager's Guide: Understanding the Power Index

Welcome to the league's analytics dashboard! This tool is designed to look past "schedule luck" and determine who actually has the strongest team in the league using data science.

## 📈 What is the "Power Index"?
Think of the **Power Index** as your team's "Overall Rating" (like a Madden or 2K rating). 

*   **Average is 50.00:** A perfectly average team will have a score of 50.
*   **The Scale:** Most teams fall between **30 and 70**.
*   **What it means:** 
    *   **60+**: You are a juggernaut. You are significantly better than the league average.
    *   **40-60**: You are in the hunt. Most of the league lives here.
    *   **Below 40**: You might need to look at the waiver wire (or start praying).

---

## 🧪 How is it Calculated?
The site uses a weighted formula to ensure that one "lucky" week doesn't skew your ranking too much. We look at three main pillars:

### 1. Scoring Consistency (45% of score)
We use **Z-Scores** (Statistical Normalization) to measure your points. 
*   **The Problem:** Scoring 120 points in a week where the league average is 100 is great. Scoring 120 points when the average is 130 is actually bad.
*   **The Solution:** A Z-Score tells us how many "steps" (standard deviations) you are above or below the league average for *that specific week*. This removes the impact of high-scoring or low-scoring weeks across the NFL.

### 2. All-Play Record (40% of score)
Your win-loss record often depends on who you happened to play. 
*   **All-Play** calculates your record if you had played **every other manager every single week**. 
*   If you had the 2nd highest score in a 12-team league, you went 10-1 that week in "All-Play," even if you lost your actual head-to-head matchup.

### 3. Roster Potential (15% of score)
We pull live projections from Sleeper for your current starters. This gives a small "boost" or "penalty" based on how your team is expected to perform in the upcoming week.

---

## 📊 Understanding the Dashboard

### Z-Score Points & All-Play Wins
On the main table, you'll see green (+) and red (-) numbers:
*   **Z-Score Points:** A `+1.2` means you scored 1.2 standard deviations *above* the average. Anything above 0 is "Above Average."
*   **Z-Score All Play:** This measures how consistently you beat the rest of the league.

### Season Trends
Click on your name! The chart shows your **Power Index** (the solid green line) vs. your **League Rank** (the dashed blue line) over the whole season. This helps you see if your team is heating up or cooling down.

---

## ⚔️ The Rivalry Simulator (Standings Page)
The "Standings" page includes a **Rivalry Simulator**. 
*   Select your team and a rival.
*   The tool simulates a matchup between you two for **every single week** of the season.
*   It shows who *would* have won more often if you played each other every week, helping settle those "I only lost because of your lucky kicker" arguments.

---

**Note:** The backend server sleeps when not in use. If the site takes a few seconds to load initially, it’s just "waking up." Once it's up, it's lightning fast!
