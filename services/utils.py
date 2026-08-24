from datetime import date, timedelta


def resolve_date(value: str) -> str:
    value = value.lower().strip()

    today = date.today()

    if value == "today":
        return str(today)

    if value == "tomorrow":
        return str(today + timedelta(days=1))

    if value == "yesterday":
        return str(today - timedelta(days=1))

    return value
