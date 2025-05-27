"""
Custom Weather API Service

This module provides a Flask-based REST API for weather data retrieval using the OpenWeatherMap API.
It includes error handling, CORS support, and environment variable configuration.

Features:
    - Current weather data retrieval by location
    - Error handling for API failures
    - CORS support for cross-origin requests
    - Environment variable configuration
    - Detailed error messages

Dependencies:
    - Flask: Web framework
    - requests: HTTP client
    - flask_cors: CORS support
    - python-dotenv: Environment variable management

Environment Variables:
    - CUSTOM_WEATHER_API_PORT: Port for the API server (default: 5000)
    - OPENWEATHER_API_KEY: API key for OpenWeatherMap

Example Usage:
    >>> import requests
    >>> response = requests.get("http://localhost:5000/weather?location=London")
    >>> weather_data = response.json()
    >>> print(f"Temperature: {weather_data['main']['temp']}°C")
"""

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from typing import Dict, Any, Tuple

load_dotenv()  # Load variables from .env

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

API_PORT = int(os.environ.get("CUSTOM_WEATHER_API_PORT", 5000))
API_KEY = os.environ.get("OPENWEATHER_API_KEY")

def get_weather_data(location):
    if not API_KEY:
        return {"error": "OpenWeatherMap API key not found."}
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {'q': location, 'appid': API_KEY, 'units': 'metric'}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        status = response.status_code
        if status == 404:
            return {"error": f"Location '{location}' not found."}
        if status == 401:
            return {"error": "Invalid OpenWeatherMap API key."}
        return {"error": f"HTTP error occurred: {http_err} - {response.text}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request error: {req_err}"}

@app.route('/weather', methods=['GET'])
def weather_endpoint():
    location = request.args.get('location')
    if not location:
        return jsonify({"error": "Location parameter is required."}), 400

    data = get_weather_data(location)
    status_code = 500 if "error" in data else 200
    return jsonify(data), status_code

if __name__ == '__main__':
    if not API_KEY:
        print("!!! ERROR: OPENWEATHER_API_KEY not set in .env file.")
    else:
        print(f"--- Starting Custom Weather API on http://localhost:{API_PORT} ---")
        app.run(port=API_PORT, debug=True)
