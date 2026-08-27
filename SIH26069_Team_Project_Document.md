# SIH26069 — 6–7 Hour Internal Hackathon Prototype
## Team Roles, Scope, Architecture & Execution Guide

**Problem Statement ID:** SIH26069
**Problem Statement:** National Weather Big Data Analytics Platform
**Format:** Internal hackathon — 6 members, 6–7 hours
**Rule #1:** *One complete working prototype is better than ten unfinished technologies.*

---

## 1. Project Overview

We are building a **National Weather Intelligence Platform prototype** — a system that takes messy, scattered weather signals (citizen reports, social/hashtag chatter, historical weather data) and turns them into **structured, verified, map-ready weather events**.

This is a 6–7 hour internal hackathon. The goal is **one working end-to-end slice**, not a finished product.

---

## 2. Problem Understanding

Weather-related information today is scattered across many sources — citizens, social media, news, and official feeds — and it comes in different formats, at different reliability levels, often duplicated, and sometimes unstructured or misleading.

**Why this is hard:**
- No common format across sources
- Same event gets reported many times (duplication)
- No way to tell a real report from a false/misleading one at a glance
- No central place where an authority can see verified, geo-located events

**Why a centralized platform helps:** it collects reports, standardizes them, uses AI to understand and de-duplicate them, scores their reliability, and shows verified events on a live map for quick decision-making.

**Role of AI/ML:** classify what kind of weather event a report describes, detect when multiple reports are about the same event, and produce an explainable trust score for each report.

**Role of the dashboard:** give an admin/authority a map + filters + verification workflow to review and confirm events quickly.

> **We are building a NATIONAL WEATHER INTELLIGENCE PLATFORM — not a weather forecasting platform.** We are not predicting the weather or replacing IMD. We are structuring and verifying reports about weather that is already happening or has happened.

**Core flow:**

```
Weather / Social / Citizen Data
        ↓
   Data Ingestion
        ↓
  Data Normalization
        ↓
    AI/ML Processing
        ↓
  Event Classification
        ↓
  Duplicate Detection
        ↓
  Reliability Scoring
        ↓
      Database
        ↓
      FastAPI
        ↓
  React Dashboard + India Map
        ↓
  Admin Verification
```

---

## 3. Prototype Goal

Prove this single sentence works, end to end, with real running code:

> **"We transform fragmented and noisy weather reports into structured, deduplicated, reliability-scored, and geographically actionable weather events."**

Everything built in the 6–7 hours should serve that sentence. Nothing else.

---

## 4. What We Are Building (Scope)

### A. MUST BUILD

| # | Feature |
|---|---------|
| 1 | Prepared weather/social/citizen data ingestion |
| 2 | Common data schema |
| 3 | Database |
| 4 | FastAPI backend |
| 5 | AI weather-event classification |
| 6 | Duplicate detection |
| 7 | Explainable reliability score |
| 8 | React dashboard |
| 9 | India map |
| 10 | Event markers |
| 11 | Filters |
| 12 | Admin verification |
| 13 | One complete end-to-end demo workflow |

### B. SHOULD BUILD IF TIME PERMITS

- Citizen report submission form
- Charts/analytics visuals
- Simulated live streaming
- DBSCAN event clustering
- Image upload on reports
- UI polish
- Docker packaging

### C. DO NOT BUILD (this hackathon)

Hadoop, Spark cluster, TensorFlow, PyTorch, deep learning, BERT fine-tuning, Kubernetes, complex AWS architecture, complex microservices, Elasticsearch, Redis, Airflow, Flink, satellite image processing, video AI, full-scale social-media scraping, complex authentication, production deployment.

**Why excluded:** none of these are needed to prove the core idea in 6–7 hours. They add setup time, learning curve, and failure points without changing whether the demo works. They belong to a *future, scaled* version of this system — see Section 13.

---

## 5. Six Team Roles

| Member | Role | Level |
|---|---|---|
| 1 | Frontend Lead | Experienced |
| 2 | Backend Lead | Experienced |
| 3 | AI/ML + Data Lead (you) | Experienced (learning scikit-learn) |
| 4 | Data Ingestion Lead | Beginner |
| 5 | Database & Streaming Lead | Beginner |
| 6 | QA + Integration + Analytics Lead | Beginner |

**Mentorship pairing:**
- Member 1 (Frontend) mentors no one directly but works closely with Member 6 on dashboard analytics/integration.
- Member 2 (Backend) mentors Member 5 (Database) — API and schema decisions flow from backend needs.
- Member 3 (AI/ML) mentors Member 4 (Data Ingestion) — the ML model's input format depends entirely on how ingestion normalizes data.
- Member 6 (QA/Integration) works across all pairs, so effectively everyone briefly supports Member 6 at integration checkpoints.

---

## 6. Individual Responsibilities

**Member 1 — Frontend Lead**
React dashboard, India map, React-Leaflet, charts, filters, report detail view, admin panel UI.

**Member 2 — Backend Lead**
FastAPI, REST APIs, database integration, ML API integration, admin/verification APIs, analytics endpoint. Authentication only if time permits.

**Member 3 — AI/ML + Data Lead**
Data preprocessing, NLP preprocessing, TF-IDF, Logistic Regression, event classification, confidence scoring, duplicate detection (cosine similarity), reliability score, analytics support. DBSCAN only if time permits.

> **Build incrementally — do not build the whole ML system before integrating:**
> - **Phase 1:** Event Classification
> - **Phase 2:** Duplicate Detection
> - **Phase 3:** Reliability Score
> - **Phase 4:** DBSCAN clustering (only if time remains)
>
> Hand off a working Phase 1 to backend as early as possible so integration isn't blocked waiting for the "complete" ML pipeline.

**Member 4 — Data Ingestion Lead (Beginner)**
Prepare CSV/JSON datasets, normalize different sources into the common schema, prepare hashtag/social-weather sample data, optional public API connector, simulated data stream if needed.

**Member 5 — Database & Streaming Lead (Beginner)**
SQLite/PostgreSQL setup, table design, SQL queries, database seeding. Basic PostGIS only if already comfortable. Kafka only after the MVP already works.

**Member 6 — QA + Integration + Analytics Lead (Beginner)**
Testing, data validation, dashboard analytics support, integration checklist tracking, documentation, architecture diagram, demo preparation, presentation support.

---

## 7. Required Knowledge Per Role

| Role | Already needs to know | Learn before hackathon | Do NOT learn | Max learning time |
|---|---|---|---|---|
| Frontend Lead | React, JS, HTML/CSS | React-Leaflet basics, Chart.js/Recharts basics | Redux, Next.js, animation libraries | 1–2 hrs |
| Backend Lead | Python, REST basics | FastAPI routing + Pydantic models | Full auth systems, microservices | 1–2 hrs |
| AI/ML Lead (you) | Python, Pandas, NumPy | TF-IDF + LogisticRegression in scikit-learn, cosine similarity | Deep learning, transformers | 1–2 hrs |
| Data Ingestion (Beginner) | Basic Python, CSV/JSON | pandas.read_csv/json basics, dict-to-schema mapping | Web scraping, real APIs | 30–45 min |
| Database Lead (Beginner) | Basic SQL | SQLite in Python (`sqlite3` or SQLAlchemy) | PostGIS, Kafka | 30–45 min |
| QA/Integration (Beginner) | None required | Postman basics, basic checklist/test-case writing | Automated test frameworks | 30 min |

**Principle:** teach only the minimum needed for this prototype — not the whole technology.

---

## 8. Technology Stack

### Required

| Layer | Tools |
|---|---|
| Frontend | React, JavaScript, HTML/CSS, React-Leaflet, Axios |
| Backend | Python, FastAPI, Pydantic |
| Data | Pandas, NumPy, CSV, JSON |
| AI/ML | scikit-learn, TF-IDF, Logistic Regression, Cosine Similarity |
| Database | SQLite (default) or PostgreSQL |
| Dev tools | Git, GitHub, Postman |

### Optional (only if core MVP is done)

Chart.js/Recharts, DBSCAN, PostGIS, Docker, Kafka, PySpark.

### Do Not Use

Hadoop, TensorFlow, PyTorch, Kubernetes, Elasticsearch, Redis, Airflow, Flink, complex AWS infrastructure, complex microservices.

**Why:** Big Data tools like Kafka/Spark belong to a **future, scalable production architecture** — they are not required to prove the concept in an MVP, and attempting them in 6–7 hours creates a high risk of running out of time with nothing working.

---

## 9. Data Collection Strategy

We demonstrate multi-source ingestion in one day using a **hybrid** approach:

1. Public/historical weather data
2. Prepared social/weather sample data
3. #IMD-style sample records
4. Citizen reports (collected live through the app)
5. Synthetic/simulated records (for volume/demo purposes)

**Always label the source honestly** using a `data_origin` field:

`real_live` · `real_historical` · `citizen` · `public_dataset` · `synthetic` · `historical_simulated`

**Never claim fabricated records are real social-media posts.**

**On #IMD / social data:** the prototype uses prepared/historical/public records tagged with hashtags such as `#IMD`, `#WeatherAlert`, `#HeavyRain`, `#Flood`, `#Thunderstorm`, `#Heatwave`, `#Fog`, `#DustStorm`, `#StrongWind`. If a legitimate API is available it can be connected — but live social-media access is **optional** and must never become a blocker. Live access is treated as a nice-to-have, not a dependency.

---

## 10. Common Data Schema

All incoming records, regardless of source, are normalized into:

```json
{
  "id": "R001",
  "source": "citizen",
  "data_origin": "citizen",
  "source_id": "CIT001",
  "timestamp": "2026-08-27T10:30:00",
  "text": "Heavy rainfall causing waterlogging in Gomti Nagar",
  "hashtag": "#IMD",
  "city": "Lucknow",
  "state": "Uttar Pradesh",
  "latitude": 26.85,
  "longitude": 80.95,
  "image_url": null,
  "event_type": null,
  "ai_confidence": null,
  "duplicate_score": null,
  "reliability_score": null,
  "verification_status": "unverified"
}
```

**Why `data_origin` matters:** it's the single field that keeps the team honest with judges — it lets anyone instantly tell which records are real, historical, citizen-submitted, or synthetic, without digging through code.

---

## 11. AI/ML Scope

### A. Event Classification
**Method:** TF-IDF + Logistic Regression
**Classes:** rainfall, flood, thunderstorm, heatwave, fog, dust_storm, strong_wind, hailstorm, cyclone, other

Example — Input: *"Heavy rainfall has caused flooding in Lucknow."* → Output: `Flood — 94%`

### B. Duplicate Detection
**Method:** TF-IDF + Cosine Similarity, combined with location and timestamp proximity — two reports describing the same event nearby in place/time are flagged as likely duplicates.

### C. Reliability Score
Call this an **"Explainable Report Reliability Score"** — not a fake-news detector. A weighted, transparent formula using signals such as: source type, AI confidence, agreement with reference weather data, number of nearby supporting reports, location validity, timestamp consistency, duplicate probability.

Output format:
```
Reliability Score: 91/100
Status: Likely Reliable
```
Always show *why* — which signals pushed the score up or down.

### D. DBSCAN Clustering (optional)
Only attempted if A–C are working. Groups geographically/temporally concentrated reports into a single event cluster (e.g., "20 reports → Flood Event Cluster, Lucknow").

---

## 12. System Architecture

**What we build (6–7 hour prototype):**

```
DATA SOURCES
   ↓
INGESTION
   ↓
NORMALIZATION
   ↓
AI/ML
   ↓
DATABASE
   ↓
FASTAPI
   ↓
REACT
   ↓
MAP + DASHBOARD
   ↓
ADMIN VERIFICATION
```

**Future scalable architecture (NOT built now — for the pitch/roadmap slide only):**

```
DATA SOURCES
   ↓
 Kafka
   ↓
Spark / PySpark
   ↓
Scalable Storage
   ↓
 AI/ML
   ↓
Dashboard
```

Make it explicit in the presentation that the second diagram is the **roadmap**, not what was implemented today.

---

## 13. Backend API Contract

| Method & Path | Purpose |
|---|---|
| `GET /reports` | List all ingested reports (with filters) |
| `GET /events` | List classified/clustered weather events |
| `POST /reports` | Submit a new citizen report |
| `POST /predict` | Run classification/duplicate/reliability pipeline on a report |
| `PUT /reports/{id}/verify` | Admin verifies, rejects, or marks a report duplicate |
| `GET /analytics/summary` | KPI numbers for dashboard cards |

Keep the API surface exactly this small — no extra endpoints "just in case."

---

## 14. Dashboard Requirements

**KPI cards:** Total Reports · Verified Reports · Suspicious Reports · Weather Events · Duplicate Reports

**India map markers by event type:** Flood (red) · Rainfall (blue) · Thunderstorm (yellow) · Heatwave (orange) · Fog (white) · others as needed

**Filters:** Date · State · City · Event · Verification Status · Source

**Event detail popup:** Event type · Location · Number of reports · AI confidence · Reliability score · Duplicate count · Source · Verification status

**Admin actions:** Verify · Reject · Mark Duplicate

---

## 15. 6–7 Hour Timeline

| Time | Focus |
|---|---|
| 0:00–0:30 | Setup — Git, environment, database, schema |
| 0:30–2:00 | Parallel development across all 6 modules |
| 2:00–3:00 | First frontend + backend + database integration |
| 3:00–4:00 | AI/ML integration (classification → duplicate → reliability) |
| 4:00–5:00 | End-to-end workflow: citizen report → processing → map → admin verification |
| 5:00–6:00 | Testing, filters, charts, bug fixing |
| 6:00–7:00 | Feature freeze, critical bug fixes, demo rehearsal |

> **At the 3-hour mark: STOP adding major features.** From that point on, integration takes priority over anything new.

---

## 16. What We Should Say to Judges/Faculty

- "Our prototype demonstrates the core intelligence pipeline for transforming fragmented weather reports into structured weather events."
- "Our current prototype uses prepared/public/historical data and simulated streams where live feeds are not available."
- "Our architecture is designed to support authorized live social/API connectors."
- "The AI component classifies weather events, identifies potential duplicates, and produces an explainable reliability score."
- "Our production architecture can scale the ingestion and processing layer using technologies such as Kafka and Spark."

## 17. What We Should NOT Say

- "We are scraping all social media."
- "We have real-time access to all #IMD posts."
- "Our AI detects fake news with 100% accuracy."
- "We built a national-scale Big Data system."
- "We implemented Kafka/Spark" (if we didn't).
- "Our synthetic posts are real citizen reports."
- "Our ML model is production-ready."
- "We predict the weather."

Say what the prototype **actually** demonstrates — no more, no less.

---

## 18. Demo Story (2–3 minutes)

A report arrives: *"Heavy rainfall causing severe waterlogging in Gomti Nagar, Lucknow."*

1. System receives the report
2. Report is normalized into the common schema
3. AI classifies it — **Flood, 94% confidence**
4. System finds similar reports — **7 similar reports detected**
5. Reliability score is calculated — **91/100, Likely Reliable**
6. System creates a **Flood Event — Lucknow**
7. Event appears on the India map
8. Admin opens the event, reviews the evidence
9. Admin clicks **Verify**
10. Dashboard updates — **Verified Flood Event**

This end-to-end flow is the centerpiece of the presentation — rehearse it until it's smooth.

---

## 19. Failure / Fallback Plan

| If this fails... | ...fall back to |
|---|---|
| Social API | Prepared hashtag dataset |
| PostgreSQL | SQLite |
| Kafka | Python-simulated stream |
| Live data unavailable | Historical/public data |
| ML integration breaks | Run ML module locally, expose output via prepared API data |
| Map API issue | Leaflet + OpenStreetMap |
| Image upload fails | Text-only report |

**Rule:** the team must never be blocked by a single external service.

---

## 20. Environment Setup — Every Laptop

Do this in the **0:00–0:30 setup window**. Everyone runs the common steps; each role adds their own extras.

### 20.1 Common setup (all 6 members)

**Install once, before the hackathon if possible:**
- Python 3.10+ (`python --version` to check)
- Node.js 18+ and npm (`node --version`)
- Git (`git --version`)
- A code editor (VS Code recommended)
- Postman (Backend + QA especially)

**GitHub repo (one person creates it, e.g. Backend Lead or you):**
1. Create a new repo on GitHub, e.g. `sih26069-weather-intel`.
2. Add a `.gitignore` for Python + Node (GitHub's template dropdown has one — pick "Python" then add `node_modules/`, `.env`, `venv/` manually if not included).
3. Add all 6 members as collaborators (Settings → Collaborators), or have everyone fork if that's easier to manage.
4. Everyone clones it locally:
   ```bash
   git clone https://github.com/<org-or-user>/sih26069-weather-intel.git
   cd sih26069-weather-intel
   ```
5. Agree on a branching rule for the day — simplest for 6–7 hours: everyone commits to `main` in short, frequent commits, OR one branch per module (`frontend`, `backend`, `ml`, `data`, `db`) merged into `main` at each integration checkpoint (2:00, 4:00, 6:00). For a time-boxed hackathon, **frequent small commits to `main`** is usually safer than managing merge conflicts across branches.
6. Suggested repo structure:
   ```
   sih26069-weather-intel/
   ├── backend/          # FastAPI app (Member 2)
   ├── frontend/         # React app (Member 1)
   ├── ml/                # classification, dedup, reliability (Member 3 — you)
   ├── data/              # datasets, ingestion scripts (Member 4)
   ├── db/                # schema, seed scripts (Member 5)
   ├── docs/              # architecture diagram, checklist, this document (Member 6)
   └── README.md
   ```

### 20.2 Python virtual environment (Members 2, 3, 4, 5 — anyone touching Python)

Each person creates **their own venv locally** (venvs are never committed to Git):

```bash
# from inside the repo, or inside your module folder e.g. backend/ or ml/
python -m venv venv

# activate it:
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (cmd)
venv\Scripts\activate.bat
# macOS/Linux
source venv/bin/activate

# confirm it's active — prompt should show (venv)
```

Install shared Python dependencies:
```bash
pip install fastapi uvicorn pydantic pandas numpy scikit-learn python-multipart
```

Freeze them so everyone stays in sync:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "add requirements.txt"
git push
```

Everyone else then just runs:
```bash
python -m venv venv
source venv/bin/activate   # or the Windows equivalent
pip install -r requirements.txt
```

Add `venv/` to `.gitignore` if it isn't already there — never push the venv folder itself.

### 20.3 Frontend setup (Member 1, and anyone helping on dashboard)

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios react-leaflet leaflet recharts
npm run dev
```

### 20.4 Database setup (Member 5)

SQLite needs no install — it's file-based and works out of the box with Python's built-in `sqlite3` module, or via SQLAlchemy:
```bash
pip install sqlalchemy
```
Create the schema/seed script early (`db/init_db.py`) and commit it so anyone can rebuild the database from scratch with one command.

### 20.5 Backend run check (Member 2)

```bash
cd backend
uvicorn main:app --reload
# visit http://127.0.0.1:8000/docs to confirm FastAPI's auto-generated API docs load
```

### 20.6 Quick per-role checklist for the first 30 minutes

| Member | Must have working before 0:30 |
|---|---|
| 1 — Frontend | `npm run dev` shows the default Vite/React page |
| 2 — Backend | `uvicorn main:app --reload` runs, `/docs` loads |
| 3 — AI/ML (you) | venv active, `import sklearn, pandas, numpy` runs with no errors |
| 4 — Data Ingestion | Can read a sample CSV/JSON into a pandas DataFrame |
| 5 — Database | SQLite file created, one test table created and queryable |
| 6 — QA/Integration | Repo cloned, Postman installed, checklist doc (Section 21) open and ready to track |

If anyone gets stuck on setup past 0:30, don't let it block the group — that person pairs with whoever finishes first while continuing setup in parallel.

---

## 21. Final Team Checklist

- [ ] Environment set up for all 6 members
- [ ] GitHub repo created, everyone has access
- [ ] Datasets prepared (real/historical/citizen/synthetic, all tagged)
- [ ] Database schema created and seeded
- [ ] Backend APIs implemented and tested in Postman
- [ ] Frontend dashboard connected to backend
- [ ] ML classification model working and integrated
- [ ] Duplicate detection working and integrated
- [ ] Reliability scoring working and integrated
- [ ] India map rendering with correct markers
- [ ] Filters working
- [ ] Admin verification flow working
- [ ] Full end-to-end integration test passed
- [ ] Testing/bug fixes complete
- [ ] Demo script rehearsed
- [ ] Presentation/slides ready

---

## 22. Closing Principle

> **One complete working prototype is better than ten unfinished technologies.**

Every decision in the next 6–7 hours should be checked against this. If a feature doesn't move the team closer to the working end-to-end demo in Section 18, it waits.
