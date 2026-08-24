def weather_label(code: int | None):
    if code is None: return "Unknown"
    if code in (0, 1): return "Clear"
    if code in (2, 3): return "Partly cloudy"
    if 51 <= code <= 67: return "Rain"
    if 80 <= code <= 82: return "Rain showers"
    if code >= 95: return "Thunderstorm"
    return "Cloudy"

def advisories(forecast: dict):
    d = forecast.get("daily", {}); rain = max(d.get("precipitation_probability_max", [0]) or [0]); wind = max(d.get("wind_speed_10m_max", [0]) or [0])
    items=[]
    if rain >= 70: items.append({"severity":"warning","title":"Heavy-rain readiness","body":"High rain probability: clear drains, avoid waterlogged routes and monitor local authority alerts."})
    if wind >= 40: items.append({"severity":"warning","title":"Strong-wind precaution","body":"Secure loose outdoor objects and avoid exposed areas."})
    if not items: items.append({"severity":"info","title":"Routine monitoring","body":"No threshold-based hazard detected in this forecast. Check official IMD bulletins for operational decisions."})
    return items
