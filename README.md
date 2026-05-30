# SAFEGUARD - Access, Logging & Cloud Control Review Workbook

SAFEGUARD is a Flask + SQLite security control review workbench. It upgrades an Excel-style review workbook into a web application for reviewing access, SSO/MFA, user permissions, encryption references, log evidence, configuration exports, AWS-style cloud service review notes, risk themes, remediation owners, evidence requests, policy references, and management-ready summaries.

## Problem Statement

Security assessors often collect evidence across many systems, owners, policies, and remediation tickets. The work can become scattered across spreadsheets, screenshots, exports, and emails. SAFEGUARD keeps the review workflow in one place while still treating Excel as a first-class import and export format.

## Why It Matters

The project demonstrates how technical evidence becomes audit-ready reporting: control status, evidence health, risk scoring, owner accountability, remediation aging, policy mapping, and executive summaries.

## Features

- System inventory with sensitive-data, cloud, AWS service, and review-date tracking.
- Technical control review across access, SSO/MFA, user permissions, privileged access, encryption, logging, cloud configuration, baselines, change management, vulnerabilities, and secrets.
- Evidence repository with aging buckets, evidence request notes, missing/outdated/expired evidence flags, and printable request lists.
- Observations with likelihood x impact scoring, risk ratings, and a 5x5 matrix.
- Remediation tracker with overdue logic, days open, days overdue, blocked status, validation fields, and burn-down style status chart.
- Policy mapping and framework coverage heatmap for Internal Security Policy, NIST SP 800-53, CIS Controls, ISO 27001, SOC 2, HIPAA, PCI DSS, and AWS Well-Architected Security Pillar.
- Consolidated risk register joining observations and remediation.
- Activity log for create, update, and status-change events.
- Excel workbook export with Cover/Executive Summary, Systems, Controls, Evidence, Observations, Remediation, Policy Mapping, Dashboard Summary, and Risk Register sheets.
- Markdown management report export for tickets, emails, or interview walkthroughs.
- CSV import templates for systems, controls, evidence, observations, and policy mappings.

## Tech Stack

Python, Flask, SQLite, SQLAlchemy, Bootstrap 5, Jinja2, pandas, openpyxl, Chart.js, and Bootstrap Icons.

## Architecture

```text
Browser
  -> Flask routes in app.py
  -> SQLAlchemy models in models.py
  -> SQLite database in data/safeguard.db
  -> calculations.py for risk, evidence, flags, and readiness scoring
  -> imports.py / exports.py / reports.py for CSV, Excel, and Markdown workflows
```

## Deploy Online (Render — recommended)

Flask + SQLite + Gunicorn works reliably on [Render](https://render.com). The repo includes a `render.yaml` Blueprint.

### Option A — Blueprint (fastest)

1. Push the latest code to https://github.com/mehulnikumbh19/SAFEGUARD
2. Sign in at https://dashboard.render.com with GitHub
3. Click **New +** → **Blueprint**
4. Connect the **SAFEGUARD** repository
5. Render reads `render.yaml` and creates the `safeguard` web service
6. Click **Apply** and wait ~3–5 minutes
7. Open your live URL (for example `https://safeguard.onrender.com`)

### Option B — Manual web service

1. **New +** → **Web Service** → connect **SAFEGUARD**
2. Settings:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app`
   - **Health check path:** `/health`
3. Add env var `SECRET_KEY` (or let Render generate one)
4. Deploy

### Hosted demo notes (Render free tier)

- First request after ~15 min idle can take **30–60 seconds** (service spins up)
- SQLite lives in `data/safeguard.db` on the instance (resets on redeploy; seed data reloads automatically)
- Health check: `GET /health` → `{"status":"ok","service":"SAFEGUARD","systems":10}`

## Deploy Online (Railway — alternative)

[Railway](https://railway.app) also works with the included `railway.toml`.

1. Sign in at https://railway.app with GitHub
2. **New Project** → **Deploy from GitHub repo** → **SAFEGUARD**
3. Railway auto-detects Python; confirm start command uses Gunicorn (see `railway.toml`)
4. Deploy and open the generated URL

## Deploy Online (Vercel — not recommended for this app)

Vercel serverless is a poor fit for Flask + SQLite + pandas exports. Use Render or Railway instead. Vercel config remains in the repo if you want to experiment later.

## Screenshots

Add screenshots of the dashboard, risk register, evidence page, and Excel export here after running the app.

## How To Run Locally

1. Open a terminal in the `safeguard` folder.
2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Turn it on:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install the required packages:

```powershell
pip install -r requirements.txt
```

5. Start the app:

```powershell
python app.py
```

6. Open this address in your browser:

```text
http://127.0.0.1:5000
```

## Reset The Database

From the `safeguard` folder, run:

```powershell
flask --app app reset-db
```

This recreates the database and reloads the sample systems, controls, evidence, observations, remediations, policy mappings, and activity-log entries.

## Load Seed Data

The seed data loads automatically the first time you run `python app.py` if the database is empty. You can also reload it with:

```powershell
flask --app app reset-db
```

## Import CSV Files

1. Start the app.
2. Open the Import page.
3. Download the matching CSV template.
4. Fill in the rows.
5. Upload the CSV.
6. SAFEGUARD validates required headers, enum values, and references to existing systems or controls.
7. Valid rows are imported; rejected rows are shown with row-level errors.

## Export Reports

- Use the Reports page to export the full Excel workbook or Markdown report.
- Use a System Detail page to export a per-system Excel workbook or Markdown report.
- Use the Risk Register page to export the consolidated risk register as CSV.
- Use the Systems page to export the current filtered system inventory as CSV.

## Sample Workflow

1. Review the dashboard readiness score and top risks.
2. Open Systems and choose a production or restricted-data system.
3. Check the system flags panel for missing logging, encryption, MFA, and evidence gaps.
4. Review evidence status and add evidence request notes.
5. Open Observations and review risk score, severity, owner, and due date.
6. Update remediation status after validation evidence is available.
7. Export the Excel workbook and Markdown management summary.

## Security/GRC Concepts Demonstrated

Access control, SSO/MFA, user permissions, privileged access, encryption at rest, encryption in transit, logging and monitoring, AWS-style cloud configuration review, evidence review, remediation tracking, risk scoring, control ownership, policy mapping, framework coverage, audit trail, and management reporting.

## Resume Alignment

SAFEGUARD - Access, Logging & Cloud Control Review Workbook (Mar 2025 - May 2025)

Created an Excel review workbook for technical controls covering SSO/MFA, user permissions, encryption references, log evidence, configuration exports, and AWS-style cloud service review notes.

Mapped control observations to risk themes, remediation owners, evidence requests, policy references, and management-ready summaries for clear security assessment reporting.

Resume bullet suggestions:

- Built a Flask + SQLite security control review platform for assessing access, logging, encryption, and AWS-style cloud controls.
- Developed evidence review workflows to track missing, outdated, and incomplete audit artifacts across technical control domains.
- Implemented automated risk flagging for missing MFA evidence, incomplete logging evidence, PHI/payment encryption gaps, and overdue remediation.
- Created management-ready dashboards and Excel reports summarizing control health, evidence gaps, risk themes, and remediation status.

## Interview Talking Points

"I built SAFEGUARD to simulate how a security assessor reviews technical controls for systems handling sensitive data. The tool focuses on access control, SSO/MFA, user permissions, encryption, logging, cloud configuration, evidence review, and remediation tracking. It helped me practice translating technical observations into risk themes, evidence requests, remediation actions, and management-ready summaries."

## Future Improvements

- Add role-based access for assessor, control owner, and manager views.
- Add attachment storage for screenshots and exports.
- Add optional API connectors for cloud evidence collection.
- Add approval workflow for risk acceptance.
- Add trend history for readiness score and remediation burn-down.
