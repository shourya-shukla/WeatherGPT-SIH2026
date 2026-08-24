import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_coordinates(city: str):

    url = "https://api.openweathermap.org/geo/1.0/direct"

    params = {
        "q": city,
        "limit": 1,
        "appid": API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    return {
        "name": data[0]["name"],
        "country": data[0]["country"],
        "latitude": data[0]["lat"],
        "longitude": data[0]["lon"]
    }
