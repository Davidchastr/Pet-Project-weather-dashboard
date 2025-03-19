import requests
from flask import Flask, render_template, request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
import pytz
import time
from timezonefinder import TimezoneFinder

app = Flask(__name__)

# API-ключи
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "95f537e554a64a3600353cb8c3b3958e")
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# Словарь месяцев на русском
MONTHS_RU = {
    'January': 'января',
    'February': 'февраля',
    'March': 'марта',
    'April': 'апреля',
    'May': 'мая',
    'June': 'июня',
    'July': 'июля',
    'August': 'августа',
    'September': 'сентября',
    'October': 'октября',
    'November': 'ноября',
    'December': 'декабря'
}

WEATHER_ICON_MAP = {
    "01d": "wi-day-sunny",
    "01n": "wi-night-clear",
    "02d": "wi-day-cloudy",
    "02n": "wi-night-alt-cloudy",
    "03d": "wi-cloud",
    "03n": "wi-cloud",
    "04d": "wi-cloudy",
    "04n": "wi-cloudy",
    "09d": "wi-showers",
    "09n": "wi-showers",
    "10d": "wi-day-rain",
    "10n": "wi-night-alt-rain",
    "11d": "wi-thunderstorm",
    "11n": "wi-thunderstorm",
    "13d": "wi-snow",
    "13n": "wi-snow",
    "50d": "wi-fog",
    "50n": "wi-fog",
}

def get_wind_direction(degrees):
    directions = ["Север", "Северо-восток", "Восток", "Юго-восток", "Юг", "Юго-запад", "Запад", "Северо-запад"]
    index = round(degrees / 45) % 8
    return directions[index]

def get_current_weather(lat=None, lon=None, city=None):
    if city:
        url = f"{BASE_URL}weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    elif lat and lon:
        url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    else:
        return None
    try:
        response = requests.get(url, timeout=10)
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
        response = requests.get(url, timeout=10)
        print(f"Запрос прогноза: {url}")
        print(f"Статус запроса прогноза: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Исключение при запросе прогноза: {e}")
        return None

def get_air_quality(lat, lon):
    url = f"{BASE_URL}air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        print(f"Запрос качества воздуха: {url}")
        print(f"Статус запроса качества воздуха: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            aqi = data['list'][0]['main']['aqi']
            print(f"Полученный AQI: {aqi}")
            return aqi
        else:
            print(f"Ошибка OpenWeatherMap (качество воздуха): {response.text}")
            return None
    except Exception as e:
        print(f"Исключение при запросе качества воздуха: {e}")
        return None

def generate_temperature_graph(forecast_data):
    if not forecast_data or 'list' not in forecast_data or not forecast_data['list']:
        print("Ошибка: Нет данных для построения графика.")
        return False
    daily_temps = {}
    tz = pytz.timezone('Europe/Moscow')
    for entry in forecast_data['list'][:40]:
        date = datetime.fromtimestamp(entry['dt'], tz).date()
        temp = entry['main']['temp']
        if date not in daily_temps:
            daily_temps[date] = []
        daily_temps[date].append(temp)

    dates = []
    avg_temps = []
    for date, temps in daily_temps.items():
        dates.append(date)
        avg_temps.append(sum(temps) / len(temps))

    plt.figure(figsize=(12, 5), facecolor='#f0f4f8')
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
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    try:
        plt.savefig(graph_path, bbox_inches='tight', dpi=100)
        print(f"График успешно сохранен: {graph_path}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении графика: {e}")
        return False
    finally:
        plt.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    city = request.form.get('city') if request.method == 'POST' else None
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if city:
        # Баг 3: Город отображается с маленькой буквы, если введен с маленькой
        city_name = city  # Убрали .capitalize(), чтобы сохранить регистр ввода
        current_weather = get_current_weather(city=city)
        forecast = get_forecast(city=city)
    elif lat and lon:
        current_weather = get_current_weather(lat=lat, lon=lon)
        forecast = get_forecast(lat=lat, lon=lon)
        city_name = current_weather['name'] if current_weather else "Неизвестный город"
    else:
        current_weather = get_current_weather(lat=53.6304, lon=55.9308)
        forecast = get_forecast(lat=53.6304, lon=55.9308)
        city_name = current_weather['name'] if current_weather else "Стерлитамак"

    if not current_weather or not forecast:
        print(f"Ошибка: Не удалось получить данные для города {city if city else 'по координатам'}")
        return render_template('index.html', error="Не удалось получить данные о погоде. Проверьте название города или подключение к интернету.")

    # Баг 1: Температура всегда 0°C
    current_temp = 0  # Вместо current_weather.get('main', {}).get('temp', 0)
    feels_like = current_weather.get('main', {}).get('feels_like', 0)
    humidity = current_weather.get('main', {}).get('humidity', 0)
    wind_speed = current_weather.get('wind', {}).get('speed', 0)
    wind_direction = get_wind_direction(current_weather.get('wind', {}).get('deg', 0))
    visibility = current_weather.get('visibility', 0) / 1000 if current_weather.get('visibility') else 0
    cloudiness = current_weather.get('clouds', {}).get('all', 0)
    description = current_weather.get('weather', [{}])[0].get('description', 'Нет данных').capitalize()
    icon = current_weather.get('weather', [{}])[0].get('icon', '04d')
    icon_class = WEATHER_ICON_MAP.get(icon, "wi-day-cloudy")
    tz = pytz.timezone('Europe/Moscow')
    sunrise = datetime.fromtimestamp(current_weather.get('sys', {}).get('sunrise', 0), tz).strftime('%H:%M')
    sunset = datetime.fromtimestamp(current_weather.get('sys', {}).get('sunset', 0), tz).strftime('%H:%M')
    pressure = current_weather.get('main', {}).get('pressure', 0)
    lat = current_weather.get('coord', {}).get('lat', 53.6304)
    lon = current_weather.get('coord', {}).get('lon', 55.9308)
    aqi = get_air_quality(lat, lon)
    last_updated = datetime.fromtimestamp(current_weather.get('dt', 0), tz).strftime('%H:%M, %d %B %Y')

    daily_forecast = {}
    for entry in forecast.get('list', [])[:40]:
        if not entry or 'dt' not in entry or 'main' not in entry:
            continue
        date = datetime.fromtimestamp(entry['dt'], tz).date()
        if date not in daily_forecast:
            daily_forecast[date] = {'temps': [], 'feels': [], 'icons': []}
        daily_forecast[date]['temps'].append(entry['main'].get('temp', 0))
        daily_forecast[date]['feels'].append(entry['main'].get('feels_like', 0))
        daily_forecast[date]['icons'].append(entry.get('weather', [{}])[0].get('icon', '04d'))

    forecast_data = []
    for date, data in list(daily_forecast.items())[:5]:
        avg_temp = sum(data['temps']) / len(data['temps']) if data['temps'] else 0
        avg_feels = sum(data['feels']) / len(data['feels']) if data['feels'] else 0
        icon_counts = {}
        for icon_code in data['icons']:
            icon_counts[icon_code] = icon_counts.get(icon_code, 0) + 1
        dominant_icon = max(icon_counts.items(), key=lambda x: x[1])[0] if icon_counts else "04d"
        icon_class = WEATHER_ICON_MAP.get(dominant_icon, "wi-day-cloudy")
        formatted_date = f"{int(date.day)} {MONTHS_RU.get(date.strftime('%B'), date.strftime('%B'))}"
        forecast_data.append((formatted_date, round(avg_temp, 1), round(avg_feels, 1), icon_class))

    # Баг 2: Прогноз на 5 дней показывает только 3 дня
    forecast_data = forecast_data[:3]

    graph_generated = generate_temperature_graph(forecast)

    return render_template('index.html',
                           city=city_name,
                           current_temp=current_temp,
                           feels_like=feels_like,
                           humidity=humidity,
                           wind_speed=wind_speed,
                           wind_direction=wind_direction,
                           visibility=visibility,
                           cloudiness=cloudiness,
                           description=description,
                           icon_class=icon_class,
                           sunrise=sunrise,
                           sunset=sunset,
                           pressure=pressure,
                           aqi=aqi,
                           forecast=forecast_data,
                           graph_exists=graph_generated,
                           timestamp=int(time.time()),
                           last_updated=last_updated)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)