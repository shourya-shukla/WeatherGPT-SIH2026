# WeatherGPT — SIH 2026 MVP

WeatherGPT is a disaster-management weather intelligence dashboard for India. It pairs live data from Open-Meteo with a deterministic weather assistant: every reported weather value is returned by a provider and stamped with its source and retrieval time.

## Run locally

```bash
docker compose up --build
```

Open `http://localhost:5173`. The API is at `http://localhost:8000/docs`.

Without Docker, start the backend with `pip install -r backend/requirements.txt && uvicorn app.main:app --app-dir backend --reload`, then `cd frontend && npm install && npm run dev`.

Copy `.env.example` to `.env` to configure PostgreSQL and an optional `OPENAI_API_KEY`. The product works without an LLM: its safe intent router invokes data tools directly. Any future LLM integration must use `WeatherAssistant` tools and never create weather facts itself.

## Architecture

`frontend/` React + Vite dashboard · `backend/app/providers/` live data adapters · `backend/app/services/` validation, alerts, assistant · `backend/app/api/` routes · `backend/app/models/` SQLAlchemy models.

Open-Meteo is the default adapter; replace or add an IMD adapter behind `WeatherProvider` without changing routes or UI.

## Test

```bash
cd backend
pytest
```
