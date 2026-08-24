import asyncio
from app.services.weather import weather_service
from app.providers.open_meteo import ProviderUnavailable

def test_known_demo_location_when_geocoder_unavailable(monkeypatch):
    async def down(_): raise ProviderUnavailable("offline")
    monkeypatch.setattr(weather_service.provider, "geocode", down)
    location = asyncio.run(weather_service.locate("Mumbai"))
    assert location.name == "Mumbai"
