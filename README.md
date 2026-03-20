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
- Rank picklist shows rank number, Jira key, workstream, and description
- Jump back to earlier ranks to finish them
- Colored boxes represent activity types, width indicates duration
- Real-time timeline and rank overview table with rank numbers and Jira keys
- **Time-of-day clock** displayed alongside the stopwatch timer
- **Persistent stopwatch** — the running timer and current activity survive navigation to other pages (Admin, Preparation, Statistics). Come back to the stopwatch and everything is exactly as you left it.

### Statistics View
- Time breakdown by activity type (pie + bar charts)
- Time by workstream and by rank
- Waste analysis: non-execution time stacked by workstream
- Productive vs. waiting time ratio
- Auto-generated recommendations per workstream

### Scenario Preparation
- **Import from Jira CSV** — upload a semicolon-separated test execution export (Xray format); scenario name is derived from the filename, workstreams are auto-created from Jira project prefixes
- **Re-import safe** — importing the same CSV again updates existing ranks instead of duplicating them
- Rank IDs link directly to Jira issues
- Create scenarios manually or via import
- Define ranks with IDs, descriptions, and assigned workstreams

### Admin
- Manage activity types (name + color), fully customizable
- Manage workstreams (e.g., "ITCA", "YAL")
- Manage scenarios with **display names** — imported scenarios keep their Jira ID (e.g., "FSMTEST-57421") but can be given a readable display name (e.g., "91.5 YUC Sale")
- Manage sessions

### Server Health
- `/api/health` endpoint shows version, source hash, uptime, PID, and database status
- Server version polling — browser shows a banner if the server restarts or goes down

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

The batch file automatically kills any existing process on port 5050 and clears Python cache before starting.

### Setup Order

1. **Preparation** — Import a Jira CSV test execution export
2. **Admin** — Set display names for imported scenarios, manage activity types and workstreams
3. **Stopwatch** — Run a testing session
4. **Statistics** — Analyze where time was spent

## Tech Stack

- **Backend:** Python / Flask / Waitress (production WSGI server)
- **Database:** SQLite (zero config, file-based)
- **Frontend:** Vanilla JS, Chart.js
- **No build step required**

## Data

All data is stored in `testwatch.db` (SQLite) in the project directory. Back up this file to preserve your session data.
