import httpx
from datetime import datetime, timezone
from .base import WeatherProvider
from ..config import settings
from ..schemas import Location

class ProviderUnavailable(Exception): pass

class OpenMeteoProvider(WeatherProvider):
    base = "https://api.open-meteo.com/v1"
    geo = "https://geocoding-api.open-meteo.com/v1/search"
    async def _get(self, url, params):
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as c:
                r = await c.get(url, params=params); r.raise_for_status(); return r.json()
        except (httpx.HTTPError, ValueError) as e: raise ProviderUnavailable(str(e))
    async def geocode(self, query):
        data = await self._get(self.geo, {"name": query, "count": 1, "language": "en", "format": "json"})
        rows = data.get("results", [])
        if not rows: raise ValueError(f"Location '{query}' was not found")
        x = rows[0]
        return Location(name=x["name"], latitude=x["latitude"], longitude=x["longitude"], country=x.get("country", "India"), admin1=x.get("admin1"))
    async def current(self, loc):
        return await self._get(f"{self.base}/forecast", {"latitude":loc.latitude,"longitude":loc.longitude,"current":"temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m","timezone":"auto"})
    async def forecast(self, loc):
        return await self._get(f"{self.base}/forecast", {"latitude":loc.latitude,"longitude":loc.longitude,"hourly":"temperature_2m,precipitation_probability,weather_code","daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max","forecast_days":7,"timezone":"auto"})
    async def historical(self, loc):
        # Climate endpoint exposes historical monthly modelled climatology.
        return await self._get("https://climate-api.open-meteo.com/v1/climate", {"latitude":loc.latitude,"longitude":loc.longitude,"start_date":"1991-01-01","end_date":"2020-12-31","models":"MRI_AGCM3_2_S","monthly":"temperature_2m_mean,precipitation_sum"})

def source(mode="live"):
    return {"provider":"Open-Meteo", "retrieved_at":datetime.now(timezone.utc).isoformat(), "data_mode":mode}
