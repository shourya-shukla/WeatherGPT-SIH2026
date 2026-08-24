import re
from .weather import weather_service
from .alerts import weather_label, advisories

class WeatherAssistant:
    async def respond(self, message, location=None):
        place = location or self._extract_place(message) or "New Delhi"
        loc = await weather_service.locate(place)
        m = message.lower()
        if any(x in m for x in ["alert", "warning", "advis", "rain", "storm"]):
            data, src = await weather_service.forecast(loc); alerts=advisories(data)
            return f"For {loc.name}: {alerts[0]['title']}. {alerts[0]['body']}", "weather_alerts", {"location":loc.model_dump(),"alerts":alerts,"forecast":data}, src
        if any(x in m for x in ["history", "climate", "trend"]):
            data, src = await weather_service.historical(loc)
            return f"Climate data for {loc.name} is available from the linked source. Values are modelled historical climate data, not a near-term forecast.", "climate_trend", {"location":loc.model_dump(),"climate":data}, src
        if any(x in m for x in ["forecast", "tomorrow", "week", "hour"]):
            data, src = await weather_service.forecast(loc)
            return f"Here is the seven-day forecast for {loc.name}. Rain chances and temperatures below are provider data retrieved just now.", "forecast", {"location":loc.model_dump(),"forecast":data}, src
        data, src = await weather_service.current(loc); c=data.get("current",{})
        return f"{loc.name}: {c.get('temperature_2m','—')}°C, feels like {c.get('apparent_temperature','—')}°C, {weather_label(c.get('weather_code'))}. Wind {c.get('wind_speed_10m','—')} km/h.", "current_weather", {"location":loc.model_dump(),"weather":data}, src
    def _extract_place(self, text):
        match=re.search(r"(?:in|at|for)\s+([A-Za-z ]{2,40})(?:\?|$|\s+today|\s+tomorrow)", text, re.I)
        return match.group(1).strip() if match else None

assistant_service = WeatherAssistant()
