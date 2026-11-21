import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from mcp.server import MCPServer


mcp = MCPServer(
    "portfolio-time-weather",
    instructions="Provides current local time and current weather information.",
)


@mcp.tool()
def get_current_time(timezone: str = "Asia/Dhaka") -> dict[str, str]:
    """Get the current date and time in an IANA timezone."""
    try:
        local_time = datetime.now(ZoneInfo(timezone))
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError(f"Unknown IANA timezone: {timezone}") from error

    return {
        "timezone": timezone,
        "datetime": local_time.isoformat(timespec="seconds"),
        "formatted": local_time.strftime("%A, %B %-d, %Y at %-I:%M %p"),
    }


@mcp.tool()
async def get_current_weather(city: str = "Dhaka") -> dict[str, str | float | int]:
    """Get current weather conditions for a city using Open-Meteo."""
    city = city.strip()
    if not city or len(city) > 100:
        raise ValueError("City must contain between 1 and 100 characters.")

    async with httpx.AsyncClient(timeout=10) as client:
        geocoding_response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geocoding_response.raise_for_status()
        results = geocoding_response.json().get("results", [])
        if not results:
            raise ValueError(f"Could not find a location named {city}.")

        location = results[0]
        weather_response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,weather_code,wind_speed_10m"
                ),
                "timezone": "auto",
            },
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data["current"]

    weather_descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    weather_code = current["weather_code"]
    return {
        "city": location["name"],
        "country": location.get("country", ""),
        "timezone": weather_data.get("timezone", ""),
        "observed_at": current["time"],
        "temperature_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "relative_humidity_pct": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "conditions": weather_descriptions.get(weather_code, f"Weather code {weather_code}"),
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.environ.get("MCP_SERVER_HOST", "127.0.0.1"),
        port=int(os.environ.get("MCP_SERVER_PORT", "8001")),
        stateless_http=True,
        json_response=True,
    )
