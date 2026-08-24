import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from services.geocoding import get_coordinates
from services.weather import get_current_weather, get_forecast
from services.nwp import get_gfs_forecast
from services.utils import resolve_date
from services.climate import analyze_climate
from services.history import get_historical_weather


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_forecast_tool(city: str, date: str):
    """Gets the weather forecast for a city and date.

    Args:
        city: Name of the city, for example Lucknow.
        date: Date for the forecast, such as tomorrow or 2026-08-25.

    Returns:
        Weather forecast for the requested date.
    """
    date = resolve_date(date);
    location = get_coordinates(city)

    if location is None:
        return {
            "error": "Location not found"
        }

    return get_forecast(
        location["latitude"],
        location["longitude"],
        date
    )

def get_gfs_forecast_tool(city: str, date: str):
    """Get NOAA GFS numerical weather prediction for a city.

    Automatically converts the city name into coordinates.

    Args:
        city: City name.
        date: Date in YYYY-MM-DD format.

    Returns:
        A summary of the GFS forecast.
    """


    date = resolve_date(date)
    location = get_coordinates(city)

    if location is None:
        return {
            "error": "Location not found"
        }

    data = get_gfs_forecast(
        location["latitude"],
        location["longitude"],
        date
    )

    forecast = data.get("forecast", [])

    if not forecast:
        return {
            "error": f"No GFS forecast data available for {city} on {date}"
        }

    temperatures = [
        item["temperature"]
        for item in forecast
        if item["temperature"] is not None
    ]

    precipitation = [
        item["precipitation"]
        for item in forecast
        if item["precipitation"] is not None
    ]

    return {
        "city": city,
        "date": date,
        "model": "NOAA GFS",
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "minimum_temperature": min(temperatures),
        "maximum_temperature": max(temperatures),
        "total_precipitation": round(sum(precipitation), 2),
        "hourly_forecast": forecast
    }

def analyze_climate_tool(
    city: str,
    start_date: str,
    end_date: str
):
    """Analyze historical weather and climate data for a city.

    Args:
        city: City name, for example Lucknow.
        start_date: Beginning of the period, such as 2026-07-01 or yesterday.
        end_date: End of the period, such as 2026-08-01 or today.

    Returns:
        Climate statistics for the requested period.
    """

    start_date = resolve_date(start_date)
    end_date = resolve_date(end_date)

    location = get_coordinates(city)

    if location is None:
        return {
            "error": "Location not found"
        }

    history = get_historical_weather(
        location["latitude"],
        location["longitude"],
        start_date,
        end_date
    )

    return analyze_climate(history["records"])

def get_weather(city: str):
    """Gets the current weather for a city.

    Args:
        city: Name of the city, for example Lucknow.

    Returns:
        Current weather information for the city.
    """

    location = get_coordinates(city)

    if location is None:
        return {
            "error": "Location not found"
        }

    return get_current_weather(
        location["latitude"],
        location["longitude"]
    )


def ask_weather_gpt(question: str):

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction="""
You are WeatherGPT, an expert weather assistant.

Rules:

1. Never invent weather information.
2. Use tools whenever actual weather or climate data is requested.
3. Use get_weather for current conditions.
4. Use get_forecast_tool for normal forecasts.
5. Use get_gfs_forecast_tool for GFS or numerical weather prediction.
6. Use analyze_climate_tool for historical climate analysis.
7. Weather tools accept city names and automatically resolve coordinates.
8. For relative dates such as today, tomorrow, and yesterday, pass the
   relative date expression to the tool. The application will resolve it.
9. Never ask the user for latitude or longitude when a recognizable
   city name is provided.
10. GFS results are model predictions and must not be presented as
    guaranteed weather.
11. Use Celsius and metric units.
12. Use get_forecast_tool for normal forecasts for today or future dates.
13. Use get_gfs_forecast_tool only for current/future GFS model forecasts.
14. Use analyze_climate_tool for historical weather and climate analysis.
15. Do not use GFS to retrieve historical weather.
16. Do not dump the complete hourly forecast unless the user explicitly
    asks for hourly details.
17. For general questions, summarize important weather information.
18. Do not describe precipitation amount as precipitation probability.
    Values such as 1.3 mm represent predicted precipitation amount,
    not percentage probability.
""",
            tools=[
                get_weather,
                get_forecast_tool,
                get_gfs_forecast_tool,
                analyze_climate_tool
                   ]
        )
    )

    return response.text
