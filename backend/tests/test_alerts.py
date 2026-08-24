from app.services.alerts import advisories, weather_label
def test_rain_advisory():
    result=advisories({"daily":{"precipitation_probability_max":[75],"wind_speed_10m_max":[10]}})
    assert result[0]["severity"] == "warning"
def test_weather_label(): assert weather_label(61) == "Rain"
