from flask import Flask, jsonify, request, render_template
import requests
import os
import redis
from dotenv import load_dotenv
from flask_redis import FlaskRedis
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Redis setup
app.config['REDIS_URL'] = "redis://localhost:6379/0"  # Redis URL
redis_client = FlaskRedis(app)

# Cache expiration time in seconds (12 hours)
CACHE_EXPIRATION = 180  # 3 min's

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/weather', methods=['GET'])
def get_weather():
    city_name = request.args.get('city')  # Get the city name from query parameters
    api_key = os.getenv('WEATHER_API_KEY')  # Get the API key from .env file

    if not city_name:
        return jsonify({"error": "City name is required"}), 400

    # Check Redis cache for the city's weather data
    cached_data = redis_client.get(city_name)

    if cached_data:
        # Return cached data if available, decode and load as Python dict
        weather_data = json.loads(cached_data.decode('utf-8'))
    else:
        # If not cached, make API request (unitGroup=metric for Celsius)
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city_name}?key={api_key}&unitGroup=metric"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise error if request failed
            weather_data = response.json()  # Get the JSON response

            # Cache the response for future requests (expire in 12 hours)
            redis_client.setex(city_name, CACHE_EXPIRATION, json.dumps(weather_data))

        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

    # Current weather information
    temperature = weather_data['currentConditions']['temp']  # Temperature in Celsius
    current_condition = weather_data['currentConditions']['conditions']

    # 5-day forecast data
    forecast = weather_data['days'][:5]  # Take the first 5 days
    forecast_data = []

    for day in forecast:
        forecast_data.append({
            "date": day['datetime'],
            "temperature_max": round(day['tempmax'], 2),
            "temperature_min": round(day['tempmin'], 2),
            "condition": day['conditions']
        })

    simplified_data = {
        "city": weather_data['resolvedAddress'],
        "temperature": round(temperature, 2),
        "condition": current_condition,
        "forecast": forecast_data
    }

    return jsonify(simplified_data)


if __name__ == '__main__':
    app.run(debug=True)
