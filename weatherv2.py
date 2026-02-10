import requests
import asciichartpy as ac

# ---- CITIES (name: (lat, lon)) ----
cities = {
    "Berlin": (52.52, 13.41),
    "Paris": (48.85, 2.35),
    "Rome": (41.90, 12.49),
}

url = "https://api.open-meteo.com/v1/forecast"

for city, (lat, lon) in cities.items():
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m",
        "forecast_days": 1,
        "timezone": "auto"
    }

    data = requests.get(url, params=params).json()

    temps = data["hourly"]["temperature_2m"][:24]
    humidity = data["hourly"]["relative_humidity_2m"][:24]

    print("\n" + "=" * 40)
    print(f"{city} — Temperature (°C)")
    print(ac.plot(temps))

    print(f"{city} — Humidity (%)")
    print(ac.plot(humidity))