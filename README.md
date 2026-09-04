# Agentic URL Shortener

A production-style URL shortener and agentic software engineering prototype built to demonstrate end-to-end SDLC orchestration with controlled agent autonomy.

## Overview

The project contains two major parts:

1. A working URL shortener service.
2. An agentic software engineering orchestration system.

The URL shortener supports:

- URL validation
- Short-code generation
- Persistent SQLite storage
- URL redirection
- Click analytics
- Health checks
- Automated API tests

The orchestration system demonstrates:

- Explicit dependency graphs
- Sequential execution
- Parallel execution paths
- Synchronization gates
- Human approval checkpoints
- Bounded retries
- Fallback handling
- Safe-stop behavior
- Rollback support
- Dynamic replanning
- Audit logging
- Reliability metrics
- Controlled agent autonomy

---

## Technology Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest
- Uvicorn

---

## Project Structure

```text
agentic-url-shortener/
│
├── app/
│   ├── __init__.py
│   ├── agents.py
│   ├── database.py
│   ├── demo.py
│   ├── main.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── scenarios.py
│   │
│   └── tests/
│       ├── test_api.py
│       └── test_orchestrator.py
│
├── .gitignore
├── README.md
└── requirements.txt