from pydantic import BaseModel


class CurrentWeather(BaseModel):
    city: str
    latitude: float
    longitude: float
    temperature: float
    humidity: int
    condition: str
    wind_speed: float


class ForecastItem(BaseModel):
    time: str
    temperature: float
    humidity: int
    condition: str
    rain_probability: int


class Forecast(BaseModel):
    latitude: float
    longitude: float
    date: str
    forecasts: list[ForecastItem]

class ClimateRecord(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    rainfall: float
