from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


app = FastAPI(
    title="WeatherGPT API",
    description="Weather intelligence API for SIH 2026",
    version="1.0.0"
)

api = APIRouter(prefix="/api/v1")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CHAT REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    message: str
    location: str | None = None


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
def current_weather(location: str):
    coordinates = get_coordinates(location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    weather = get_current_weather(
    coordinates["latitude"],
    coordinates["longitude"]
)

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
                "apparent_temperature": weather["temperature"],
                "condition": weather["condition"]
            }
        },
        "source": {
            "provider": "OpenWeather",
            "data_mode": "live"
        }
    }


# ============================================================
# WEATHER FORECAST
# ============================================================

@api.get("/weather/forecast")
def forecast(location: str):

    coordinates = get_coordinates(location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    data = get_7day_forecast(
        coordinates["latitude"],
        coordinates["longitude"]
    )

    return {
        "location": {
            "name": location,
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"]
        },

        "forecast": data,

        "source": {
            "provider": "Open-Meteo",
            "data_mode": "live"
        }
    }

# ============================================================
# GFS / NWP
# ============================================================

@api.get("/weather/nwp")
def nwp_forecast(
    location: str,
    date: str
):
    coordinates = get_coordinates(location)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    return get_gfs_forecast(
        coordinates["latitude"],
        coordinates["longitude"],
        date
    )


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
def location(city: str):

    coordinates = get_coordinates(city)

    if coordinates is None:
        return {
            "error": "Location not found"
        }

    return coordinates


# ============================================================
# HISTORICAL WEATHER
# ============================================================

@api.get("/weather/history")
def historical_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str
):
    return get_historical_weather(
        lat,
        lon,
        start_date,
        end_date
    )


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
def chat(request: ChatRequest):

    question = request.message

    # Give Gemini the location as context when available.
    if request.location:
        question = (
            f"The user's selected location is {request.location}.\n"
            f"User question: {request.message}"
        )

    response = ask_weather_gpt(question)

    return {
        "answer": response
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
