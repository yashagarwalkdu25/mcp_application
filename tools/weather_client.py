import os
import requests

API_PORT = int(os.environ.get("CUSTOM_WEATHER_API_PORT", 5000))
API_URL = f"http://localhost:{API_PORT}/weather"

def get_current_weather(location):
    """Calls our *custom* weather API."""
    try:
        response = requests.get(API_URL, params={'location': location})
        response.raise_for_status()
        data = response.json()

        if "error" in data: return data

        main = data.get('main', {})
        weather_desc = data.get('weather', [{}])[0].get('description', 'N/A')
        return {
            "location": data.get('name', location),
            "conditions": weather_desc.capitalize(),
            "temperature_c": main.get('temp', 'N/A'),
            "humidity_percent": main.get('humidity', 'N/A')
        }
    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to custom weather API at {API_URL}. Is it running?"}
    except Exception as e:
        return {"error": f"Error calling custom weather API: {e}"}
    
print(get_current_weather("New York"))