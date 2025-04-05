import aiohttp
from data.config import WEATHER_API_KEY

async def get_weather(city: str, language="uz"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang={language}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                desc = data["weather"][0]["description"]
                if language == "uz":
                    return f"{city}da ob-havo: {temp}°C (his qilinadi {feels_like}°C), {desc}"
                else:  # ru
                    return f"Погода в {city}: {temp}°C (ощущается как {feels_like}°C), {desc}"
            return "Shaharni topib bo'lmadi." if language == "uz" else "Не удалось найти город."

async def get_weather_by_location(lat: float, lon: float, language="uz"):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang={language}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                desc = data["weather"][0]["description"]
                city = data["name"]
                if language == "uz":
                    return f"{city}da ob-havo: {temp}°C (his qilinadi {feels_like}°C), {desc}"
                else:  # ru
                    return f"Погода в {city}: {temp}°C (ощущается как {feels_like}°C), {desc}"
            return "Lokatsiya bo'yicha ob-havo topilmadi." if language == "uz" else "Погода по локации не найдена."

async def get_weekly_forecast(city: str, language="uz"):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang={language}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                forecast = []
                for item in data["list"][::8]:  # Каждые 24 часа
                    date = item["dt_txt"].split(" ")[0]
                    temp = item["main"]["temp"]
                    desc = item["weather"][0]["description"]
                    forecast.append(f"{date}: {temp}°C, {desc}")
                header = f"{city} uchun haftalik prognoz:\n" if language == "uz" else f"Прогноз на неделю для {city}:\n"
                return header + "\n".join(forecast)
            return "Prognoz topilmadi." if language == "uz" else "Прогноз не найден."