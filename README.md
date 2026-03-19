# TestWatch

Track and optimize your end-to-end testing sessions. Built for teams running joint E2E testing where multiple workstreams coordinate through Jira test scenarios.

## Problem

Joint E2E testing sessions involve many people, and time is often wasted waiting — for testers to join, for environments to be ready, for blocking defects to be resolved. TestWatch makes this visible so teams can improve.

## How It Works

During a testing session, you follow the ranks of your Jira test scenario. For each rank, you track time spent on different activities using a stopwatch interface. After the session, statistics and recommendations show where time was wasted and which workstreams can improve.

## Features

### Stopwatch View
- One-click "Next Activity" button starts the timer and logs the previous activity
- Select activity type and rank while the timer is already running
- Jump back to earlier ranks to finish them
- Colored boxes represent activity types, width indicates duration
- Real-time timeline and rank overview table
- **Time-of-day clock** displayed alongside the stopwatch timer
- **Persistent session bar** — the running timer and current activity are visible on all pages (Admin, Preparation, Statistics), so you can navigate freely without losing your stopwatch

### Statistics View
- Time breakdown by activity type (pie + bar charts)
- Time by workstream and by rank
- Waste analysis: non-execution time stacked by workstream
- Productive vs. waiting time ratio
- Auto-generated recommendations per workstream

### Scenario Preparation
- **Import from Jira CSV** — upload a semicolon-separated test execution export; scenario name is derived from the filename, workstreams are auto-created from Jira project prefixes
- Rank IDs link directly to Jira issues
- Create scenarios manually (e.g., "94.0 Remarketing", "91.5 YUC Sale")
- Define ranks with IDs, descriptions, and assigned workstreams
- Scenario names are editable after import

### Admin
- Manage activity types (name + color), fully customizable
- Manage workstreams (e.g., "ITCA", "YAL")
- Manage scenarios and sessions

## Default Activity Types

| Activity | Color |
|---|---|
| Waiting for tester to join | Red |
| Waiting for tester to be ready | Light salmon |
| Test execution | Green |
| Creating a defect | Orange |
| Getting an expert | Purple |
| Waiting for blocking defect | Dark red |
| Planned break | Blue |
| Unplanned break | Grey |

Activity types can be added, edited, and removed by the admin.

## Setup

### Requirements
- Python 3.10+
- pip

### Quick Start (Windows)

Double-click `start_server.bat` or run:

```
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5050** in your browser.

### Setup Order

1. **Admin** — Create workstreams and scenarios
2. **Preparation** — Add ranks to scenarios, assign workstreams
3. **Stopwatch** — Run a testing session
4. **Statistics** — Analyze where time was spent

## Tech Stack

- **Backend:** Python / Flask
- **Database:** SQLite (zero config, file-based)
- **Frontend:** Vanilla JS, Chart.js
- **No build step required**

## Data

All data is stored in `testwatch.db` (SQLite) in the project directory. Back up this file to preserve your session data.
