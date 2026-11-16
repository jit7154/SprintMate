# SprintMate

SprintMate is an AI assistant for engineering managers that investigates sprint risk by correlating Jira-style issues with GitHub pull requests and CI test results.

Risk scoring uses deterministic Python rules rather than LLM guesswork. Google ADK agents investigate anomalies, explain root causes with concrete issue and PR citations, and propose actionable reassignment proposals that require human approval, state re-check, and an immutable audit log.

## Project Structure

```
SprintMate/
├── README.md                   # Project overview, architecture, and setup instructions
├── .gitignore                  # Git ignore rules for Python, Node, and local credentials
├── .env.example                # Example environment configuration template
├── docker-compose.yml          # PostgreSQL 16 container definition on port 5433
├── Makefile                    # Developer commands (up, dev, test, eval, lint)
├── .github/                    # CI/CD workflows
│   └── workflows/ci.yml        # GitHub Actions lint and test pipeline
└── backend/                    # Python 3.11 + FastAPI backend service
    ├── pyproject.toml          # Backend package dependencies and tool configuration
    ├── Dockerfile              # Container specification for Cloud Run deployment
    ├── app/                    # FastAPI application code
    │   ├── main.py             # Application entrypoint and middleware
    │   ├── config.py           # Typed settings loaded from environment
    │   └── api/                # Thin API route handlers
    │       └── health.py       # Health check route
    └── tests/                  # Automated test suites
        └── unit/               # Unit tests
            └── test_health.py  # Health route verification
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Node.js 20+ (for frontend)
- Gemini API Key

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY
```

### 2. Start PostgreSQL
```bash
make up
# Starts PostgreSQL 16 on port 5433
```

### 3. Install Backend Dependencies & Run Tests
```bash
python3.11 -m pip install -e backend/
pytest backend/tests
```

### 4. Run Backend Server
```bash
make dev
# API running at http://localhost:8001
```
