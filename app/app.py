from flask import Flask, jsonify, request, render_template
import requests
import os
import redis
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/weather', methods=['GET'])
def get_weather():
    city_name = request.args.get('city')  # Şehir adını sorgu parametrelerinden al
    api_key = os.getenv('WEATHER_API_KEY')  # API anahtarını .env dosyasından al

    if not city_name:
        return jsonify({"error": "City name is required"}), 400

    # API isteğini oluştur (Celsius için unitGroup=metric ekleyin)
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city_name}?key={api_key}&unitGroup=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()  # İstek hatalıysa hata fırlat
        weather_data = response.json()  # JSON yanıtı al

        # Şu anki hava durumu bilgileri
        temperature = weather_data['currentConditions']['temp']  # Celsius cinsinden sıcaklık
        current_condition = weather_data['currentConditions']['conditions']

        # 5 günlük tahmin verisi
        forecast = weather_data['days'][:5]  # İlk 5 günü al
        forecast_data = []

        for day in forecast:
            forecast_data.append({
                "date": day['datetime'],  # Değişiklik burada
                "temperature_max": round(day['tempmax'], 2),
                "temperature_min": round(day['tempmin'], 2),
                "condition": day['conditions']
            })

        simplified_data = {
            "city": weather_data['resolvedAddress'],
            "temperature": round(temperature, 2),  # İki ondalık basamağa yuvarla
            "condition": current_condition,
            "forecast": forecast_data  # Tahmin verilerini ekle
        }

        return jsonify(simplified_data)  # Sade hava verilerini döndür
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
