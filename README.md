# SprintMate

SprintMate is an AI assistant for engineering managers that investigates sprint risk by correlating Jira-style issues with GitHub pull requests and CI test results.

Risk scoring uses deterministic Python rules rather than LLM guesswork. Google ADK agents investigate anomalies, explain root causes with concrete issue and PR citations, and propose actionable reassignment proposals that require human approval, state re-check, and an immutable audit log.

## Notice on Demo Data
> [!NOTE]
> All DevCore engineering telemetry (teams, developers, issues, pull requests, and CI test logs) is synthetic demo data generated deterministically for testing, evaluation, and portfolio demonstration.

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
├── backend/                    # Python 3.11 + FastAPI backend service
│   ├── pyproject.toml          # Backend package dependencies and tool configuration
│   ├── Dockerfile              # Container specification for Cloud Run deployment
│   ├── migrations/             # SQL schema migrations
│   │   └── 001_initial_schema.sql # Baseline schema for DevCore tables
│   ├── app/                    # FastAPI application code
│   │   ├── main.py             # Application entrypoint and middleware
│   │   ├── config.py           # Typed settings loaded from environment
│   │   ├── db.py               # Async SQLAlchemy engine, session, and ORM models
│   │   ├── auth.py             # Role-based demo authorization (manager, developer)
│   │   ├── schemas/            # Typed Pydantic v2 schemas
│   │   ├── api/                # Thin API route handlers
│   │   │   ├── health.py       # Health check route
│   │   │   ├── sprints.py      # Sprints, kanban issues, risk scores, burndown
│   │   │   ├── pull_requests.py# Pull requests list and CI status
│   │   │   └── team.py         # Developer capacity, workload, and skills
│   │   └── services/           # Core domain services
│   │       ├── adapters/       # Tracker and VCS adapters (Base, Demo, GitHub Live)
│   │       └── risk/           # Deterministic risk engine
│   │           ├── rules.py    # 7 deterministic risk rules
│   │           ├── scoring.py  # Sprint risk score aggregation and breakdown
│   │           └── workload.py # Developer capacity and overload analysis
│   ├── mcp_server/             # Model Context Protocol (MCP) server
│   │   ├── server.py           # MCPServer stdio entrypoint and tool registry
│   │   ├── tools_jira.py       # Jira tools (search, issue, sprint, propose reassignment)
│   │   └── tools_github.py     # GitHub tools (search PRs, PR details, CI runs)
│   └── tests/                  # Automated test suites
│       ├── conftest.py         # Pytest fixtures and connection cleanup
│       └── unit/               # Unit tests
│           ├── test_health.py  # Health route verification
│           ├── test_adapters.py# Demo tracker and GitHub adapter tests
│           ├── test_risk_engine.py # Comprehensive risk engine verification
│           └── test_mcp_tools.py   # MCP tools execution and isolation tests
├── data/                       # Synthetic seed data and ingestion scripts
│   ├── seed/                   # Raw DevCore JSON datasets and past incident notes
│   │   ├── devcore.json        # 60 issues, 12 devs, 3 sprints, 30 PRs
│   │   ├── ground_truth.json   # Seeded anomalies for eval benchmarking
│   │   └── incidents/          # Past incident postmortem markdown files
│   └── scripts/                # Seed generation and database population scripts
│       ├── generate_seed.py    # Deterministic synthetic data generator
│       └── load_seed.py        # Database migration & seed loader
└── docs/                       # Project documentation
    └── discovery.md            # Data dictionary, organization structure, and ground truth
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
