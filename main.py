import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import requests
from fastapi import Depends, FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session, init_db
from services import cache_db
from services.embeddings import embed_text

from services.weather import (
    get_current_weather,
    get_forecast,
    get_7day_forecast,
    get_alerts
)

from services.geocoding import get_coordinates
from services.nwp import get_gfs_forecast
from services.history import get_historical_weather
from services.climate import analyze_climate
from services.ai import ask_weather_gpt


logger = logging.getLogger("weathergpt.main")


# ============================================================
# STARTUP
# ============================================================

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await init_db()
    except Exception as exc:  # noqa: BLE001
        # The API stays usable without the cache - every endpoint below
        # falls back to calling the live providers directly if the
        # database isn't reachable.
        logger.warning("Database unavailable at startup, continuing without cache: %s", exc)
    yield


app = FastAPI(
    title="WeatherGPT API",
    description="Weather intelligence API for SIH 2026",
    version="1.0.0",
    lifespan=lifespan
)

api = APIRouter(prefix="/api/v1")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(requests.RequestException)
async def upstream_service_error(_: Request, __: requests.RequestException):
    return JSONResponse(
        status_code=502,
        content={"detail": "A weather data provider is temporarily unavailable."}
    )


@app.exception_handler(RuntimeError)
async def configuration_error(_: Request, error: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": str(error)})


# ============================================================
# CHAT REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    message: str
    location: str | None = None


# ============================================================
# HELPERS
# ============================================================

async def _resolve_location(session: AsyncSession, city: str):
    """Cache-aware geocoding. Returns a dict shaped like
    `get_coordinates()` (name/country/latitude/longitude) plus
    `_location_id` and `_cached` for the caller, or None if the place
    can't be found. Falls back to a plain live geocoding call if the
    database is unavailable."""

    try:
        cached = await cache_db.get_cached_location(session, city)
        if cached:
            return {
                "name": cached.name,
                "country": cached.country,
                "latitude": cached.latitude,
                "longitude": cached.longitude,
                "_location_id": cached.id,
                "_cached": True,
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Location cache lookup failed, hitting geocoder directly: %s", exc)

    coordinates = get_coordinates(city)
    if coordinates is None:
        return None

    try:
        saved = await cache_db.save_location(session, city, coordinates)
        coordinates["_location_id"] = saved.id
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not cache location %r: %s", city, exc)
        coordinates["_location_id"] = None

    coordinates["_cached"] = False
    return coordinates


def _source(provider: str, cached: bool) -> dict:
    return {
        "provider": provider,
        "data_mode": "live",
        "cached": cached,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():
    return {
        "message": "WeatherGPT API is running"
    }


# ============================================================
# CURRENT WEATHER
# ============================================================

@api.get("/weather/current")
async def current_weather(location: str, session: AsyncSession = Depends(get_session)):
    coordinates = await _resolve_location(session, location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    location_id = coordinates.get("_location_id")
    cached_payload = None

    if location_id is not None:
        try:
            cached_payload = await cache_db.get_cached_weather(session, location_id, "current")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Weather cache read failed: %s", exc)

    if cached_payload is not None:
        weather = cached_payload
        cache_hit = True
    else:
        weather = get_current_weather(
            coordinates["latitude"],
            coordinates["longitude"]
        )
        cache_hit = False

        if location_id is not None:
            try:
                await cache_db.save_weather_cache(session, location_id, "current", weather)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Weather cache write failed: %s", exc)

    return {
        "location": {
            "name": location,
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"]
        },
        "weather": {
            "current": {
                "temperature_2m": weather["temperature"],
                "relative_humidity_2m": weather["humidity"],
                "wind_speed_10m": weather["wind_speed"],
                "apparent_temperature": weather["feels_like"],
                "condition": weather["condition"]
            }
        },
        "source": _source("OpenWeather", cache_hit)
    }


# ============================================================
# WEATHER FORECAST
# ============================================================

@api.get("/weather/forecast")
async def forecast(location: str, session: AsyncSession = Depends(get_session)):

    coordinates = await _resolve_location(session, location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    location_id = coordinates.get("_location_id")
    cached_payload = None

    if location_id is not None:
        try:
            cached_payload = await cache_db.get_cached_weather(session, location_id, "forecast")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Forecast cache read failed: %s", exc)

    if cached_payload is not None:
        data = cached_payload
        cache_hit = True
    else:
        data = get_7day_forecast(
            coordinates["latitude"],
            coordinates["longitude"]
        )
        cache_hit = False

        if location_id is not None:
            try:
                await cache_db.save_weather_cache(session, location_id, "forecast", data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Forecast cache write failed: %s", exc)

    return {
        "location": {
            "name": location,
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"]
        },

        "forecast": data,

        "source": _source("Open-Meteo", cache_hit)
    }

# ============================================================
# GFS / NWP
# ============================================================

@api.get("/weather/nwp")
async def nwp_forecast(
    location: str,
    date: str,
    session: AsyncSession = Depends(get_session)
):
    coordinates = await _resolve_location(session, location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    location_id = coordinates.get("_location_id")
    cached_payload = None

    if location_id is not None:
        try:
            cached_payload = await cache_db.get_cached_weather(
                session, location_id, "nwp", date
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("NWP cache read failed: %s", exc)

    if cached_payload is not None:
        return cached_payload

    data = get_gfs_forecast(
        coordinates["latitude"],
        coordinates["longitude"],
        date
    )

    if location_id is not None:
        try:
            await cache_db.save_weather_cache(session, location_id, "nwp", data, date)
        except Exception as exc:  # noqa: BLE001
            logger.warning("NWP cache write failed: %s", exc)

    return data


# ============================================================
# WEATHER ALERTS
# ============================================================

@api.get("/weather/alerts")
def alerts(city: str):
    return get_alerts(city)


# ============================================================
# GEOCODING
# ============================================================

@api.get("/location")
async def location(city: str, session: AsyncSession = Depends(get_session)):

    coordinates = await _resolve_location(session, city)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    return {
        "name": coordinates["name"],
        "country": coordinates["country"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
    }


# ============================================================
# HISTORICAL WEATHER
# ============================================================

@api.get("/weather/history")
async def historical_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    session: AsyncSession = Depends(get_session)
):
    # Only raw coordinates are given here (no place name), so caching
    # goes through the coordinate-based location lookup instead of the
    # name-alias one used by the other endpoints.
    try:
        location_row = await cache_db.get_or_create_location_by_coords(session, lat, lon)
    except Exception as exc:  # noqa: BLE001
        logger.warning("History cache location lookup failed: %s", exc)
        return get_historical_weather(lat, lon, start_date, end_date)

    params_key = f"{start_date},{end_date}"

    try:
        cached_payload = await cache_db.get_cached_weather(
            session, location_row.id, "history", params_key
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("History cache read failed: %s", exc)
        cached_payload = None

    if cached_payload is not None:
        return cached_payload

    data = get_historical_weather(lat, lon, start_date, end_date)

    try:
        await cache_db.save_weather_cache(session, location_row.id, "history", data, params_key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("History cache write failed: %s", exc)

    return data


# ============================================================
# CLIMATE ANALYSIS
# ============================================================

@api.get("/climate/analyze")
def climate_analysis(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str
):

    history = get_historical_weather(
        lat,
        lon,
        start_date,
        end_date
    )

    return analyze_climate(
        history["records"]
    )


# ============================================================
# CHAT
# ============================================================

@api.post("/chat")
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_session)):

    question = request.message

    # Give Gemini the location as context when available.
    if request.location:
        prompt = (
            f"The user's selected location is {request.location}.\n"
            f"User question: {request.message}"
        )
    else:
        prompt = request.message

    # --- Semantic cache lookup ---------------------------------------
    embedding = None
    cached = None

    try:
        embedding = await embed_text(question)
        cached = await cache_db.find_similar_chat(session, embedding, request.location)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chat cache lookup failed, calling Gemini directly: %s", exc)

    if cached is not None:
        try:
            await cache_db.register_chat_hit(session, cached)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not record chat cache hit: %s", exc)

        return {
            "answer": cached.answer,
            "source": _source("WeatherGPT Cache", True),
        }

    # --- Cache miss: ask Gemini ---------------------------------------
    answer = ask_weather_gpt(prompt)

    if embedding is not None:
        try:
            await cache_db.save_chat(session, question, request.location, answer, embedding)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save chat cache entry: %s", exc)

    return {
        "answer": answer,
        "source": _source("Gemini", False),
    }


# ============================================================
# TEST GFS
# ============================================================

@api.get("/test-gfs")
def test_gfs(
    city: str,
    date: str
):
    from services.ai import get_gfs_forecast_tool

    return get_gfs_forecast_tool(
        city,
        date
    )


# ============================================================
# REGISTER API ROUTER
# ============================================================

app.include_router(api)
