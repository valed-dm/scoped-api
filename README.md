# Scoped API

FastAPI template with **JWT authentication** and **role-based scopes**.

## Features
✅ OAuth2 JWT token flow
✅ Scope/role-based route protection
✅ Pre-configured SQLAlchemy/Pydantic models

## Setup
1. Clone repo
2. `cp .env.example .env` and edit secrets
3. `poetry install --no-root`
4. `uvicorn app.main:app --reload`

## Usage
- `POST /auth/login` → Get JWT
- `GET /protected-route` (Requires `admin` scope)
