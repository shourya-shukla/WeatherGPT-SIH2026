import os
import requests

from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


# ============================================================
# CURRENT WEATHER
# ============================================================

def get_current_weather(lat: float, lon: float):

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    return {
        "city": data["name"],
        "latitude": lat,
        "longitude": lon,
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"]
    }


# ============================================================
# FORECAST
# ============================================================

def get_forecast(lat: float, lon: float, date: str):

    # Resolve relative dates
    today = datetime.now().date()

    if date.lower() == "today":
        date = today.strftime("%Y-%m-%d")

    elif date.lower() == "tomorrow":
        date = (
            today + timedelta(days=1)
        ).strftime("%Y-%m-%d")

    elif date.lower() == "yesterday":
        date = (
            today - timedelta(days=1)
        ).strftime("%Y-%m-%d")


    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(
        url,
        params=params
    )

    response.raise_for_status()

    data = response.json()


    forecasts = []


    for item in data["list"]:

        forecast_date = item["dt_txt"].split(" ")[0]

        if forecast_date == date:

            forecasts.append({
                "time": item["dt_txt"],
                "temperature": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "condition": item["weather"][0]["description"],
                "rain_probability": round(
                    item["pop"] * 100
                )
            })


    return {
        "latitude": lat,
        "longitude": lon,
        "date": date,
        "forecasts": forecasts
    }

def get_7day_forecast(lat: float, lon: float):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum"
        ]),
        "forecast_days": 7,
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    return {
        "daily": data.get("daily", {})
    }

# ============================================================
# WEATHER ALERTS
# ============================================================

def get_alerts(city: str):

    return {
        "city": city,
        "alerts": [],
        "source": "IMD",
        "status": "unavailable"
    }
