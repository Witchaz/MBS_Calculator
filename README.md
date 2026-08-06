# MBS Game Manager

A Streamlit + Firebase decision-support tool built for the Macro Business Simulation (MBS) 2026 competition. It centralizes every team's round-by-round simulation data, automates the tedious manual data entry/cleanup between rounds, and layers econometric analysis on top to estimate what's actually driving market share.

This was a self-initiated, optional tool — not a required part of the competition — built to give the team faster, evidence-based decisions each round instead of relying on manual spreadsheet work and intuition.

## What it does

### 🎮 Game & Round Management (`app.py`)
- Create/load simulation "games," each with its own seasonal demand indicators (spring/summer/autumn/winter)
- Paste raw, copy-pasted simulation output (market tables, net profit, production/inventory, potential demand) directly from the MonsoonSim/MBS platform — the app parses and structures it automatically instead of requiring manual re-entry into spreadsheets
- All round data persisted to Firebase Firestore, so the whole team works from one shared, always-up-to-date source of truth

### 📥 Data Parsing (`domain/parsers.py`)
Robust text parsers that take raw, inconsistently-formatted pasted tables (tabs, commas, currency symbols, parentheses for negatives, multi-market blocks) and convert them into clean structured data — handling the messy reality of copy-pasted simulation output.

### 📈 Market Share Econometrics (`domain/econimetrics.py`, `feature_engineering.py`) — Experimental
An attempt to quantify what drives market share: converts price, product quality, and marketing/image scores into log-transformed features, then estimates market share elasticity using:
- **Cross-sectional OLS regression** per round
- **Pooled OLS** across all rounds
- **Panel fixed-effects regression** (entity effects across companies/rounds) once enough rounds exist

In practice, prediction accuracy wasn't reliable enough to inform actual in-competition decisions, so this module was not used live — it remains in the codebase as an explored approach rather than a production feature.

### 📦 Inventory & Demand Dashboard (`pages/3_inventory_management_page.py`)
Round-by-round view of production volume, finished goods inventory (per market), raw material inventory, potential demand vs. actual sales, and unsatisfied demand per market.

### 🏆 Team Performance Dashboard (`pages/4_team_performance_page.py`)
Cross-team comparison view with sales-volume-weighted statistics (weighted mean/standard deviation) to benchmark performance against competitors, visualized with Altair charts.

## Tech Stack
- **Frontend/App:** Streamlit
- **Database:** Firebase Firestore
- **Data processing:** pandas, numpy
- **Statistics/Econometrics:** statsmodels (OLS), linearmodels (Panel OLS)
- **Visualization:** Altair
- **Architecture:** layered (domain / application / infrastructure) separating parsing & econometrics logic from Firebase access and Streamlit UI

## Project Structure
```
app.py                              # Entry point — game creation/selection
domain/
├── parsers.py                      # Raw pasted-text → structured DataFrame
├── feature_engineering.py           # Log-transforms for econometric modeling
└── econimetrics.py                  # OLS / panel fixed-effects market share models
application/
├── round_service.py                 # Round save/load orchestration
├── performance_service.py           # Team performance calculations
├── inventory_planning_service.py
└── potential_demand_service.py
infrastructure/
├── firebase_client.py               # Firebase auth/init (local key or Streamlit secrets)
└── firestore_repository.py          # Firestore read/write layer
pages/
├── 0_input_page.py                  # Paste & save round data
├── 3_inventory_management_page.py    # Inventory/demand dashboard
└── 4_team_performance_page.py        # Cross-team performance comparison
core/datastore.py                     # In-session game/round state management
```

## Getting Started
```bash
pip install -r requirements.txt
streamlit run app.py
```
Requires a Firebase service account key (local JSON file or Streamlit secrets) with Firestore access — not included in this repo.

## Background
Built during the Macro Business Simulation (MBS) 2026 competition to replace manual, round-by-round spreadsheet work with a shared, automated, and analytically-grounded decision-support tool — helping the team shift from intuition-based decisions to data-backed ones.

## License
MIT License — see [LICENSE](./LICENSE) for details.
