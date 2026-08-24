from ..providers.open_meteo import OpenMeteoProvider, ProviderUnavailable, source
from ..schemas import Location

DEMO_LOCATIONS = {
    "new delhi": Location(name="New Delhi", latitude=28.6139, longitude=77.2090, admin1="Delhi"),
    "delhi": Location(name="New Delhi", latitude=28.6139, longitude=77.2090, admin1="Delhi"),
    "mumbai": Location(name="Mumbai", latitude=19.0760, longitude=72.8777, admin1="Maharashtra"),
    "kolkata": Location(name="Kolkata", latitude=22.5726, longitude=88.3639, admin1="West Bengal"),
    "chennai": Location(name="Chennai", latitude=13.0827, longitude=80.2707, admin1="Tamil Nadu"),
    "bengaluru": Location(name="Bengaluru", latitude=12.9716, longitude=77.5946, admin1="Karnataka"),
    "bangalore": Location(name="Bengaluru", latitude=12.9716, longitude=77.5946, admin1="Karnataka"),
}

class WeatherService:
    def __init__(self): self.provider = OpenMeteoProvider()
    async def locate(self, query):
        try:
            return await self.provider.geocode(query)
        except ProviderUnavailable:
            fallback = DEMO_LOCATIONS.get(query.strip().lower())
            if fallback: return fallback
            raise ValueError("Location service is unavailable. Try New Delhi, Mumbai, Kolkata, Chennai, or Bengaluru in demo mode.")
    async def current(self, loc):
        try: return await self.provider.current(loc), source()
        except ProviderUnavailable: return self._demo_current(), source("demo_fallback")
    async def forecast(self, loc):
        try: return await self.provider.forecast(loc), source()
        except ProviderUnavailable: return self._demo_forecast(), source("demo_fallback")
    async def historical(self, loc):
        try: return await self.provider.historical(loc), source()
        except ProviderUnavailable: return {"monthly":{}}, source("unavailable")
    def _demo_current(self): return {"current":{"time":"2026-08-24T12:00","temperature_2m":29.4,"apparent_temperature":33.1,"relative_humidity_2m":74,"precipitation":0.2,"weather_code":2,"wind_speed_10m":14.2}}
    def _demo_forecast(self): return {"daily":{"time":["2026-08-24","2026-08-25","2026-08-26"],"weather_code":[2,61,3],"temperature_2m_max":[32,30,33],"temperature_2m_min":[26,25,26],"precipitation_probability_max":[30,72,20],"wind_speed_10m_max":[18,25,16]},"hourly":{"time":[],"temperature_2m":[],"precipitation_probability":[]}}

weather_service = WeatherService()
