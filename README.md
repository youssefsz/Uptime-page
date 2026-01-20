# Uptime Monitoring System

A lightweight, self-hosted uptime monitoring system built with FastAPI.

## Features

- Public status page with live updates
- Private dashboard (login protected)
- Add/remove servers to monitor
- Automatic pinging every 30 seconds (configurable)
- Response time tracking and history
- PostgreSQL database for data persistence

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Setup PostgreSQL

Create a database:

```sql
CREATE DATABASE uptime_db;
```

### 3. Configure Environment

Edit `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/uptime_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-super-secret-key
```

### 4. Run the Server

```bash
uv run uvicorn app.main:app --reload
```

Visit:
- Public Status: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- Login: http://localhost:8000/login

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/servers | No | List all servers with status |
| POST | /api/servers | Yes | Add a new server |
| PUT | /api/servers/{id} | Yes | Update a server |
| DELETE | /api/servers/{id} | Yes | Delete a server |
| GET | /api/servers/{id}/history | No | Get uptime history |
| POST | /api/servers/{id}/ping | Yes | Manual ping |
| POST | /api/auth/login | No | Login |

## Project Structure

```
uptime-page/
├── app/
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings
│   ├── database.py      # Database setup
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # Authentication
│   ├── routers/
│   │   ├── auth.py      # Auth routes
│   │   └── servers.py   # Server routes
│   └── services/
│       ├── server_service.py  # CRUD operations
│       └── ping_service.py    # Background pinger
├── templates/           # HTML templates
├── static/              # CSS/JS files
├── .env                 # Configuration
└── pyproject.toml       # Dependencies
```
