# SkillPulse India

**From Labour Market Signals to Actionable Skill Planning** — Smart India Hackathon 2026 prototype.

> **Prototype/Demo Data — Not official statistics.** Every number in this project comes from a fictional demo dataset
> (Maharashtra pilot). Nothing is sourced from PLFS, NCS, e-Shram, MSDE, NSQF or any other official dataset.
> Forecasts are *Prototype Forecast*, recommendations are *Prototype Decision Support*, and everything requires
> validation with official datasets before real use.

SkillPulse is a labour-market intelligence and skill-planning platform (not a job portal). It combines demand, training
capacity and industry signals to show where skills are short or in surplus, forecast demand, support workers moving from
declining to growing industries, and give planners what-if and early-warning tools.

---

## 1. Run it (Windows)

Prerequisites: **Python 3.10+** and **Node.js 18+** on PATH, plus an internet connection for `pip`/`npm` and for the
OpenStreetMap tiles.

**Easiest — two scripts**

```bat
setup.bat        :: one-time: venv + pip install + npm install
run_all.bat      :: opens the backend and frontend in two windows
```

Then open **http://localhost:5173** and sign in with **planner / demo123** (a browser-side demo gate, not real authentication).

**Or step by step**

Backend (terminal 1):

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Frontend (terminal 2):

```bat
cd frontend
npm install
npm run dev
```

macOS / Linux: `./run_all.sh`, or use the same commands with `source venv/bin/activate`.

The demo data is already in `data/`. To regenerate it: `python scripts/generate_demo_data.py` (needs pandas + numpy).

---

## 2. Demo walkthrough (3–5 minutes)

| Step | Where | What to show |
|---|---|---|
| 1 | Dashboard | Maharashtra pilot overview, KPIs, six charts, filters |
| 2 | Skill Gap GIS | Skill **EV Technician**, click **Pune**: demand 1,000 > capacity 700 → **SHORTAGE** |
| 3 | Skill Gap GIS | **Find Nearby Surplus Capacity** → **Nashik** (about 164 km, 240 surplus seats), then Kolhapur |
| 4 | Industry Radar | Traditional ICE Automotive = declining, EV / Battery = growing, and the transition flow |
| 5 | Workforce Transition | ICE Technician → EV Technician → **Analyze Transition**: fit score, matched / missing skills, bridge training |
| 5b | Workforce Transition tab | Job Description Skill Extractor on the example text |
| 6 | What-If Planner | Pune EV: demand +20% → demand 1,200, gap 500; then capacity +30% → gap shrinks |
| 7 | Early Warning | EV Technician: 2026 LOW → 2027 GROWING → 2028 CRITICAL (prototype classes) |
| 8 | Recommendations | Geographic balancing (Pune ← Nashik), bridge training, extra seats, declining occupations |

The landing page (`/`) links to each step. These numbers are asserted by the tests, so regenerating the data cannot silently break the demo.

---

## 3. Project structure

```
skillpulse-india/
├── README.md  requirements.txt  .env.example  setup.bat  run_all.bat  run_backend.bat  run_frontend.bat
├── data/                       # DEMO dataset (CSV + JSON), every row source_type = DEMO
│   ├── districts.csv  skills.csv  occupations.csv  industries.csv
│   ├── jobs.csv  training_centres.csv  historical_demand.csv  training_capacity.csv
│   └── taxonomy.json  transition_skills.json
├── scripts/generate_demo_data.py
├── backend/                    # FastAPI + pandas + scikit-learn
│   ├── requirements.txt  tests/
│   └── app/
│       ├── main.py             # app, CORS, error handlers, start-up ingestion
│       ├── config.py           # thresholds and paths (env-overridable)
│       ├── db.py               # SQLite default, PostgreSQL/PostGIS-ready
│       ├── api/routes.py       # all /api endpoints
│       ├── models/schemas.py   # Pydantic models
│       ├── services/           # ingestion.py, engine.py (gap/GIS/forecast), planning.py
│       ├── ml/                 # forecast.py, nlp.py, transition.py, taxonomy.py
│       ├── utils/              # geo.py (haversine), clean.py
│       └── data/data_sources.json   # data-source configuration layer
└── frontend/                   # React + Vite + Tailwind + Recharts + Leaflet
    └── src/ pages/ components/ charts/ maps/ services/ hooks/ utils/
```

---

## 4. Architecture

```
Job Market Data + Training Data + Industry Signals
  → Data Ingestion (services/ingestion.py, source adapters)
  → Cleaning & Normalization (trim, dedupe, numeric coercion, alias → canonical skill)
  → NLP Skill / Occupation Mapping (ml/nlp.py + taxonomy)
  → Demand + Supply Engine (services/engine.py)
  → Forecasting (ml/forecast.py)
  → Skill Gap Engine (gap = forecast demand − training capacity)
  → GIS + Industry Radar + Transition Engine
  → What-If + Early Warning
  → Planner Dashboard → Decision Support (services/planning.py)
```

On start-up the backend reads `data/`, cleans it, writes it into a database (SQLite by default) and builds the engine
(one forecast per district × skill). Requests are answered from memory, so the UI is fast. The same diagram is shown inside the app (Methodology page).

---

## 5. The demo dataset

Generated by `scripts/generate_demo_data.py` (fixed random seed, so it is reproducible).

| File | Rows | Notes |
|---|---|---|
| districts.csv | 10 | Mumbai, Thane, Navi Mumbai, Pune, Nashik, Nagpur, Chhatrapati Sambhajinagar, Kolhapur, Satara, Solapur. Current official naming is used consistently (no "Aurangabad"). Navi Mumbai is a municipal area, treated as a demo planning zone and flagged in `notes`. |
| industries.csv | 8 | EV / Battery, Electronics, Renewable Energy, Healthcare Technology, Traditional ICE Automotive, Textiles & Garments, IT Services, General Manufacturing, with demo outlook labels |
| skills.csv | 15 | Demand-bearing skill tracks (EV Technician, Battery Assembly, ICE Automotive Service, …) |
| occupations.csv | 19 | Mapped to a skill and industry; `nco_mapping` is `PENDING` (future NCO-2015 mapping) |
| historical_demand.csv | 600 | District × skill × 2023–2026 |
| training_capacity.csv | 600 | District × skill × 2023–2026 (seats per year) |
| training_centres.csv | 40 | Name, district, lat/lon, skills offered, total / available seats, utilisation, certification |
| jobs.csv | 247 | Demo postings used to exercise the NLP extractor |
| taxonomy.json | 42 skills | Canonical competencies with aliases (BMS → Battery Management System …) |
| transition_skills.json | | Occupation skill requirements with importance weights, similarity pairs, bridge programmes |

The EV Technician numbers are hand-set so the storyline is exact: Pune 1,000 demand vs 700 capacity; Nashik 380 vs 620.
All other skills are generated from district weights and coverage ratios with small seeded noise.

---

## 6. Modules

**Dashboard** — KPIs (districts, skills, shortage / surplus skills, growing industries, transition opportunities), charts A–F, filters for district, industry, occupation, skill and year (2023–2028). Everything recalculates server-side.

**Skill Gap GIS** — Leaflet + OpenStreetMap bubble map at demo district coordinates (not boundary polygons). Click a district for demand, capacity, gap, status, forecast demand and gap, confidence, the exact calculation, and nearby training centres. *Find Nearby Surplus Capacity* ranks SURPLUS districts by straight-line (haversine) distance. Thresholds are editable in the UI.

**Industry Transition Radar** — GROWING / STABLE / DECLINING board, computed demand trend, required skills, related occupations, skill tracks, and the flow *Declining industry → Transferable skills → Growing industry → Bridge training → Target occupation* for real occupation pairs.

**Workforce Transition Engine** — Transfer Fit Score:
`credit = 1` if the skill is held, `= similarity` for a related held skill, else `0`;
`Fit = 100 × Σ(weight × credit) / Σ(weight)`. Also shown: basic overlap (`matched / target × 100`), skill distance (`100 − Fit`), matched / partial / missing skills, a bridge programme with duration, and a per-skill breakdown table. The worker's skills can be edited. For ICE Technician → EV Technician: 3 of 7 target skills match (43% basic overlap), 58% weighted fit.

**Job Description Skill Extractor** — rule-based phrase matching against the taxonomy, then occupation scoring. It is **not** an ML/LLM model and says so in the UI. `SkillExtractor` is an interface so a real model can replace `KeywordSkillExtractor`.

**What-If Scenario Planner** — sliders for demand growth and capacity change (−50% to +100%) plus skill, district and year; live recalculation (debounced API call), before/after chart, gap-over-time chart, and preset scenarios A–D.

**Early Warning System** — per skill, 2026 / 2027 / 2028 classified LOW / GROWING / CRITICAL on `gap ratio = (demand − capacity) / demand` (≤10%, ≤25%, above), warning cards, all-skills table. Labelled *Prototype Early Warning*.

**Data Explorer** — all eight tables with search, filters, sorting and paging; `source_type` is highlighted.

**Recommendations** — rule-based *Prototype Decision Support*: geographic balancing, extra seats, redirect capacity, bridge training, curriculum review, monitor emerging skills, investigate declining occupations, each with its evidence.

**Methodology** — the 14-step pipeline, architecture diagram, formulas, limitations, and *proposed official data sources* kept visibly separate from *current prototype demo data*.

### Forecasting method
OLS linear regression of demand on year (2023–2026, scikit-learn) with an 80% prediction interval from the residual error and Student's t. Four points cannot justify anything more complex, so no accuracy is claimed. Confidence is `1 − half-interval / forecast`, capped at 0.95, shown as HIGH / MEDIUM / LOW. Training capacity is held at the 2026 level in forecast years (set `CAPACITY_GROWTH_PCT` to change). XGBoost / Random Forest were deliberately not used.

### Gap classification
`gap = forecast demand − capacity`, `ratio = gap / demand`. SHORTAGE above `+10%`, SURPLUS below `−10%`, otherwise BALANCED. Configurable via `.env` (`SHORTAGE_THRESHOLD`, `SURPLUS_THRESHOLD`) or per request.

---

## 7. API

Interactive docs at http://localhost:8000/docs. All responses are JSON; errors look like `{"error": "...", "detail": "..."}`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/dashboard?district_id&industry_id&occupation_id&skill_id&year` | KPIs and chart data |
| GET | `/api/districts` `/api/skills` `/api/occupations` `/api/industries` | Reference data (industries include radar and transition pathways) |
| GET | `/api/training-centres?district_id&skill_id` | Centres |
| GET | `/api/skill-gap?skill_id&year&forecast_year` | District gap map data |
| GET | `/api/skill-gap/district?skill_id&district_id` | One district incl. nearby centres |
| GET | `/api/skill-gap/nearby-surplus?skill_id&district_id` | Nearest surplus capacity |
| GET | `/api/forecast?skill_id&district_id` | History + Prototype Forecast + model info |
| POST | `/api/transition` | Transfer Fit Score |
| GET | `/api/transition/opportunities` | Declining → growing occupation pairs |
| POST | `/api/nlp/extract-skills` | Skill extraction and occupation mapping |
| POST | `/api/what-if` | Scenario calculation |
| GET | `/api/early-warning?skill_id&district_id` | Prototype Early Warning |
| GET | `/api/recommendations?year&district_id` | Prototype Decision Support |
| GET | `/api/data-sources` | Source configuration and ingestion log |
| GET | `/api/data/{table}?search&sort_by&order&page&page_size` | Data Explorer |
| GET | `/api/health` `/api/config` | Status and thresholds |

Sample requests (PowerShell on Windows; use `curl.exe` or Invoke-RestMethod):

```powershell
Invoke-RestMethod "http://localhost:8000/api/skill-gap?skill_id=S01&year=2026&forecast_year=2028"

Invoke-RestMethod http://localhost:8000/api/transition -Method Post -ContentType "application/json" `
  -Body '{"current_occupation":"ICE Technician","target_occupation":"EV Technician"}'

Invoke-RestMethod http://localhost:8000/api/what-if -Method Post -ContentType "application/json" `
  -Body '{"skill_id":"S01","district_id":"D04","year":2026,"demand_growth_pct":20,"capacity_change_pct":0}'

Invoke-RestMethod http://localhost:8000/api/nlp/extract-skills -Method Post -ContentType "application/json" `
  -Body '{"text":"Looking for an EV technician with experience in battery management systems, vehicle diagnostics, electrical systems and high-voltage safety."}'
```

```bash
curl "http://localhost:8000/api/early-warning?skill_id=S01"
curl "http://localhost:8000/api/skill-gap/nearby-surplus?skill_id=S01&district_id=D04"
```

---

## 8. Configuration

Copy `.env.example` to `.env` (optional). Everything has a working default.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | SQLite file `backend/skillpulse.db` | `postgresql+psycopg2://user:pw@host/db` for PostgreSQL |
| `SKILLPULSE_DATA_DIR` | `data/` | Folder with the dataset |
| `SHORTAGE_THRESHOLD` / `SURPLUS_THRESHOLD` | `0.10` / `-0.10` | Gap-ratio classification |
| `EW_LOW_MAX` / `EW_GROWING_MAX` | `0.10` / `0.25` | Early-warning classes |
| `CAPACITY_GROWTH_PCT` | `0` | Assumed yearly capacity growth in forecast years |
| `TRANSITION_MIN_FIT` | `40` | Minimum fit to count as a transition opportunity |

Environment variables are read from the process environment; load a `.env` with your shell or tooling (the app does not bundle a dotenv loader).

### PostgreSQL / PostGIS later
`app/db.py` is the only module that knows the database. Install `sqlalchemy psycopg2-binary`, set `DATABASE_URL`, and the same ingestion writes to PostgreSQL. `districts` and `training_centres` carry `latitude` / `longitude` — add PostGIS geometry columns there and replace the Python haversine in `app/utils/geo.py` with `ST_DWithin` queries. The PostgreSQL path is written but **not tested** in this prototype.

### Connecting official data later
`app/services/ingestion.py` defines the `DataSourceAdapter` interface. `LocalDemoCSVAdapter` is the only working adapter. `PLFSAdapter`, `NCSAdapter`, `EShramAdapter`, `NCOTaxonomyAdapter`, `HiringSignalsAdapter` and `TrainingNSQFAdapter` are documented stubs that raise `NotImplementedError`, with comments on where each would plug in. `backend/app/data/data_sources.json` is the configuration layer. No scraping is done; integration should use agreed files or APIs. NCO / NSQF mapping belongs in `app/ml/taxonomy.py`.

---

## 9. Tests

```bat
cd backend
venv\Scripts\activate
python -m pytest -q          :: engine tests + HTTP tests
python tests\run_all.py      :: engine tests only, no pytest needed
```

`tests/test_engine.py` (14 tests) covers the storyline: Pune shortage, Nashik nearest surplus, early-warning LOW→GROWING→CRITICAL, what-if 1,000 → 1,200 / gap 500, transition matched / missing skills, NLP extraction, forecast, thresholds, dashboard filters, recommendations, data explorer. `tests/test_api.py` exercises every endpoint over HTTP.

---

## 10. Verification status (what was and was not run)

Built in a sandbox that could not reach PyPI or npm, so FastAPI and the React packages could not be installed there.

| Part | Status |
|---|---|
| Demo data generation | **Run.** Files produced and checked |
| Ingestion, SQLite layer, forecasting, gap engine, GIS distances, transition, NLP, what-if, early warning, recommendations, data explorer | **Run.** All 14 engine tests pass; every endpoint payload was serialised to strict JSON for all skills and years |
| FastAPI app, routes, Pydantic models, error handlers | **Written and compiled, not executed.** Pydantic models were imported and validated. Needs a first run: `pytest backend/tests/test_api.py` |
| React frontend | **Written; all files parse and bundle under esbuild** (local imports resolve; `react`, `recharts`, `leaflet`, `react-router-dom` were treated as external). **Not rendered in a browser.** Needs `npm install && npm run dev` and a click-through |
| Leaflet map, charts, Tailwind styling | **Not run** (depend on the packages above) |
| PostgreSQL / PostGIS path | **Not run** |

If something fails on first start, the most likely places are the FastAPI wiring and small UI details; the calculation layer is covered by tests.

## 11. Honest limitations

- All data is fictional; results illustrate the method, not the real labour market.
- Forecasts use four yearly points and a linear trend, are unvalidated, and ignore structural change.
- The skill extractor is dictionary matching, not a trained NLP model or an LLM.
- Fit scores, similarity weights and bridge hours are illustrative placeholders.
- Distances are straight-line between district centre points, not road distances; the map shows bubbles at district points, not boundaries.
- Recommendations are rule-based Prototype Decision Support, not official recommendations.
- The sign-in is a client-side demo gate.
- Pilot-first: Maharashtra pilot → validation with official datasets → scaling.
