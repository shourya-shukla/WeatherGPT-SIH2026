import requests


def get_gfs_forecast(lat: float, lon: float, date: str):

    url = "https://api.open-meteo.com/v1/gfs"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "forecast_days": 3,
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()

    times = data["hourly"]["time"]
    temperatures = data["hourly"]["temperature_2m"]
    humidity = data["hourly"]["relative_humidity_2m"]
    precipitation = data["hourly"]["precipitation"]
    wind = data["hourly"]["wind_speed_10m"]

    forecast = []

    for i in range(len(times)):

        if times[i].split("T")[0] == date:

            forecast.append({
                "time": times[i].split("T")[1],
                "temperature": temperatures[i],
                "humidity": humidity[i],
                "precipitation": precipitation[i],
                "wind_speed": wind[i]
            })

    return {
        "latitude": lat,
        "longitude": lon,
        "model": "Open-Meteo GFS",
        "date": date,
        "forecast": forecast
    }
