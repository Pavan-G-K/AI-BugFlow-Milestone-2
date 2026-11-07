# AI BugFlow — Complete Project (Milestones 1 & 2)

AI-powered issue tracking, severity prediction, collaboration, sprint planning, workflow validation and activity history.

## Stack
- Frontend: React + Vite
- API: Python FastAPI
- Database: SQLite (created automatically; no database server required)
- ML: TF-IDF + Logistic Regression (trained from bundled sample data; safe fallback when scikit-learn is unavailable)
- Authentication: JWT bearer tokens with hashed passwords

> This is a self-contained, locally runnable implementation. SQLite was selected to make setup simple and reproducible on a student laptop. The API/database layers can later be migrated to Spring Boot/PostgreSQL.

## Requirements
- Python 3.10+
- Node.js 18+
- npm

## Run on Windows (VS Code terminal)

### 1. Start the backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
If `py` is unavailable, use `python`.

API docs: http://127.0.0.1:8000/docs

### 2. Start the frontend (new terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite, usually http://localhost:5173.

### Demo login
- Email: `admin@bugflow.local`
- Password: `Admin@123`

A demo account and sample issues are seeded on the first backend start. Change the demo password before using this outside a local demo.

## Features

### Milestone 1 — Core BugFlow
- Register/login with hashed passwords and JWT authentication
- Dashboard statistics
- Create, view, update and delete issues
- Assign issues, modules, descriptions and reproduction steps
- ML-assisted severity prediction from issue title/description
- Search, status/type/severity filters
- Issue detail view

### Milestone 2 — Workflow Automation & Collaboration
- Issue type: Bug, Feature Request, Enhancement, Technical Debt
- Severity: Critical, High, Medium, Low
- Priority: P1, P2, P3, P4
- Affected module field
- Comments with author and timestamp
- Attachment upload and download
- Activity history for important actions
- Create sprints with start/end dates
- Backlog and sprint assignment
- Sprint board: To Do, In Progress, Done
- Validated lifecycle: Open → In Progress → Testing → Resolved → Closed
- Invalid transitions are rejected by the API
- Test cases included in `docs/TEST_CASES.md`

## Data and uploads
- SQLite database: `backend/bugflow.db` (created automatically)
- Attachments: `backend/uploads/`
- ML model: trained at runtime when scikit-learn is installed

## Notes
- This project is intended for local learning/demo use, not production deployment.
- Set a strong `SECRET_KEY` environment variable before deployment.
- For a production release, add HTTPS, rate limiting, malware scanning for uploads, migrations, audit retention and managed secrets.
