"""
Day 9 — Custom MCP Tool
MCP Server with a custom web_status_checker tool
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional

import requests


class MCPServer:
    def __init__(self) -> None:
        self.initialized: bool = False
        self.tools = [
            {
                "name": "web_status_checker",
                "description": "Check a website's HTTP status and response time",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to check (e.g. https://google.com)",
                        }
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "get_weather",
                "description": "Get current weather for a city (uses free Open-Meteo API)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name (e.g. London, New York, Tokyo)",
                        }
                    },
                    "required": ["city"],
                },
            },
        ]

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "day9-mcp-server", "version": "1.0.0"},
        }

    async def handle_tools_list(self) -> Dict[str, Any]:
        return {"tools": self.tools}

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "web_status_checker":
            url = args.get("url", "")
            if not url:
                result = {"ok": False, "error": "Missing URL"}
            else:
                try:
                    start = time.time()
                    response = requests.get(url, timeout=10, allow_redirects=True)
                    elapsed = round((time.time() - start) * 1000, 2)
                    result = {
                        "ok": True,
                        "url": url,
                        "status": response.status_code,
                        "time_ms": elapsed,
                    }
                except requests.exceptions.Timeout:
                    result = {"ok": False, "url": url, "error": "Request timeout"}
                except requests.exceptions.RequestException as e:
                    result = {"ok": False, "url": url, "error": str(e)}
                except Exception as e:
                    result = {"ok": False, "url": url, "error": str(e)}
        elif name == "get_weather":
            city = args.get("city", "")
            if not city:
                result = {"ok": False, "error": "Missing city name"}
            else:
                try:
                    # First, get coordinates for the city using geocoding API
                    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search"
                    geocode_params = {"name": city, "count": 1, "language": "en", "format": "json"}
                    geo_response = requests.get(geocode_url, params=geocode_params, timeout=10)
                    geo_data = geo_response.json()
                    
                    if not geo_data.get("results") or len(geo_data["results"]) == 0:
                        result = {"ok": False, "error": f"City '{city}' not found"}
                    else:
                        location = geo_data["results"][0]
                        latitude = location["latitude"]
                        longitude = location["longitude"]
                        city_name = location.get("name", city)
                        country = location.get("country", "")
                        
                        # Get weather data
                        weather_url = "https://api.open-meteo.com/v1/forecast"
                        weather_params = {
                            "latitude": latitude,
                            "longitude": longitude,
                            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                            "timezone": "auto"
                        }
                        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
                        weather_data = weather_response.json()
                        
                        if "current" in weather_data:
                            current = weather_data["current"]
                            # Weather code mapping (simplified)
                            weather_codes = {
                                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
                                3: "Overcast", 45: "Foggy", 48: "Depositing rime fog",
                                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                                85: "Slight snow showers", 86: "Heavy snow showers",
                                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
                            }
                            weather_desc = weather_codes.get(current.get("weather_code", 0), "Unknown")
                            
                            result = {
                                "ok": True,
                                "city": city_name,
                                "country": country,
                                "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
                                "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
                                "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
                                "condition": weather_desc,
                            }
                        else:
                            result = {"ok": False, "error": "Weather data not available"}
                except requests.exceptions.RequestException as e:
                    result = {"ok": False, "error": f"API error: {str(e)}"}
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
        else:
            result = {"ok": False, "error": f"Unknown tool: {name}"}

        # Wrap result in MCP text content
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result),
                }
            ]
        }


async def main() -> None:
    server = MCPServer()
    loop = asyncio.get_event_loop()

    def read_stdin():
        try:
            return sys.stdin.readline()
        except Exception:
            return None

    while True:
        line = await loop.run_in_executor(None, read_stdin)
        if not line:
            await asyncio.sleep(0.05)
            continue

        try:
            request = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params", {})

        response: Optional[Dict[str, Any]] = None

        try:
            if method == "initialize":
                result = await server.handle_initialize(params)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "tools/list":
                if not server.initialized:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32002, "message": "Server not initialized"},
                    }
                else:
                    result = await server.handle_tools_list()
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "tools/call":
                if not server.initialized:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32002, "message": "Server not initialized"},
                    }
                else:
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await server.call_tool(tool_name, arguments)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

        if response:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

