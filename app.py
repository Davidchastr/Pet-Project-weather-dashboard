import requests
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__)

# API-ключи
OPENWEATHER_API_KEY = "95f537e554a64a3600353cb8c3b3958e"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# Настройка Matplotlib
plt.switch_backend('agg')

def get_current_weather(lat=None, lon=None, city=None):
    if city:
        url = f"{BASE_URL}weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    elif lat and lon:
        url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    else:
        return None
    try:
        response = requests.get(url)
        print(f"Запрос текущей погоды: {url}")
        print(f"Статус запроса текущей погоды: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка OpenWeatherMap: {response.text}")
            return None
    except Exception as e:
        print(f"Исключение при запросе текущей погоды: {e}")
        return None

def get_forecast(lat=None, lon=None, city=None):
    if city:
        url = f"{BASE_URL}forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    elif lat and lon:
        url = f"{BASE_URL}forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    else:
        return None
    try:
        response = requests.get(url)
        print(f"Запрос прогноза: {url}")
        print(f"Статус запроса прогноза: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка OpenWeatherMap прогноза: {response.text}")
            return None
    except Exception as e:
        print(f"Исключение при запросе прогноза: {e}")
        return None

def get_air_quality(lat, lon):
    url = f"{BASE_URL}air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url)
        print(f"Запрос качества воздуха: {url}")
        print(f"Статус запроса качества воздуха: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            aqi = data['list'][0]['main']['aqi']  # Индекс качества воздуха (1-5)
            return aqi
        else:
            print(f"Ошибка OpenWeatherMap (качество воздуха): {response.text}")
            return None
    except Exception as e:
        print(f"Исключение при запросе качества воздуха: {e}")
        return None

def generate_temperature_graph(forecast_data):
    daily_temps = {}
    for entry in forecast_data['list'][:40]:
        date = datetime.fromtimestamp(entry['dt']).date()
        temp = entry['main']['temp']
        if date in daily_temps:
            daily_temps[date].append(temp)
        else:
            daily_temps[date] = [temp]

    dates = []
    avg_temps = []
    for date, temps in daily_temps.items():
        dates.append(date)
        avg_temps.append(sum(temps) / len(temps))

    plt.figure(figsize=(10, 6), facecolor='#f0f4f8')
    plt.plot(dates, avg_temps, marker='o', linestyle='-', color='#1e90ff', label='Температура', linewidth=2)
    plt.title('Прогноз температуры на 5 дней', fontsize=16, color='#2c3e50', pad=15)
    plt.xlabel('Дата', fontsize=12, color='#2c3e50')
    plt.ylabel('Температура (°C)', fontsize=12, color='#2c3e50')
    plt.grid(True, linestyle='--', alpha=0.7, color='#d1d1d1')
    plt.legend(fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.gca().set_facecolor('#e8f0fe')
    plt.tight_layout()

    graph_path = os.path.join('static', 'temp_graph.png')
    print(f"Сохранение графика в: {graph_path}")
    try:
        plt.savefig(graph_path, bbox_inches='tight')
        print(f"График успешно сохранен: {graph_path}")
    except Exception as e:
        print(f"Ошибка при сохранении графика: {e}")
    finally:
        plt.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    city = request.form.get('city') if request.method == 'POST' else None
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if city:
        current_weather = get_current_weather(city=city)
        forecast = get_forecast(city=city)
        city_name = city
    elif lat and lon:
        current_weather = get_current_weather(lat=lat, lon=lon)
        forecast = get_forecast(lat=lat, lon=lon)
        city_name = current_weather['name'] if current_weather else "Неизвестный город"
    else:
        current_weather = get_current_weather(lat=53.6304, lon=55.9308)  # Стерлитамак по умолчанию
        forecast = get_forecast(lat=53.6304, lon=55.9308)
        city_name = current_weather['name'] if current_weather else "Стерлитамак"

    if not current_weather or not forecast:
        print(f"Ошибка: Не удалось получить данные для города {city if city else 'по координатам'}")
        return render_template('index.html', error="Не удалось получить данные о погоде. Проверьте название города или подключение к интернету.")

    current_temp = current_weather['main']['temp']
    feels_like = current_weather['main']['feels_like']
    humidity = current_weather['main']['humidity']
    wind_speed = current_weather['wind']['speed']
    description = current_weather['weather'][0]['description'].capitalize()
    icon = current_weather['weather'][0]['icon']
    # Новые данные
    sunrise = datetime.fromtimestamp(current_weather['sys']['sunrise']).strftime('%H:%M')
    sunset = datetime.fromtimestamp(current_weather['sys']['sunset']).strftime('%H:%M')
    pressure = current_weather['main']['pressure']
    # Получаем координаты для запроса качества воздуха
    lat = current_weather['coord']['lat']
    lon = current_weather['coord']['lon']
    aqi = get_air_quality(lat, lon)

    forecast_data = []
    for entry in forecast['list'][:5]:
        time = datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d %H:%M')
        temp = entry['main']['temp']
        feels = entry['main']['feels_like']
        icon = entry['weather'][0]['icon']
        forecast_data.append((time, temp, feels, icon))

    generate_temperature_graph(forecast)

    return render_template('index.html',
                           city=city_name,
                           current_temp=current_temp,
                           feels_like=feels_like,
                           humidity=humidity,
                           wind_speed=wind_speed,
                           description=description,
                           icon=icon,
                           sunrise=sunrise,
                           sunset=sunset,
                           pressure=pressure,
                           aqi=aqi,
                           forecast=forecast_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render использует PORT, по умолчанию 5000 для локального теста
    app.run(host='0.0.0.0', port=port, debug=True)