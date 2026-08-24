def analyze_climate(records):

    if not records:
        return {
            "total_rainfall": 0,
            "average_max_temperature": None,
            "average_min_temperature": None
        }

    total_rainfall = sum(
        record["rainfall"]
        for record in records
        if record["rainfall"] is not None
    )

    max_temperatures = [
        record["temperature_max"]
        for record in records
        if record["temperature_max"] is not None
    ]

    min_temperatures = [
        record["temperature_min"]
        for record in records
        if record["temperature_min"] is not None
    ]

    return {
        "total_rainfall": round(total_rainfall, 2),
        "average_max_temperature": round(
            sum(max_temperatures) / len(max_temperatures), 2
        ),
        "average_min_temperature": round(
            sum(min_temperatures) / len(min_temperatures), 2
        )
    }
