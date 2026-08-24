import requests


def get_historical_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str
):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "models": "era5"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    daily = data["daily"]

    records = []

    for i in range(len(daily["time"])):

        if daily["temperature_2m_max"][i] is None:
            continue

        records.append({
            "date": daily["time"][i],
            "temperature_max": daily["temperature_2m_max"][i],
            "temperature_min": daily["temperature_2m_min"][i],
            "rainfall": daily["precipitation_sum"][i]
        })

    return {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "records": records
    }
