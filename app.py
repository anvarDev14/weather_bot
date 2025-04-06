import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from flask import Flask, render_template, request, redirect, url_for
import threading
from handlers import users, admin, notifications  # Подключаем обработчики
from database.db import user_db

# Токен бота
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на ваш токен

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация Flask
app = Flask(__name__)

# Регистрация обработчиков
users.setup(dp)
admin.setup(dp)
notifications.setup(dp)

# Веб-интерфейс
@app.route('/')
def index():
    users_list = user_db.select_all_users()
    return render_template('index.html', users=users_list)

@app.route('/send_ad', methods=['GET', 'POST'])
def send_ad():
    if request.method == 'POST':
        ad_text = request.form['ad_text']
        creator_id = 6369838846  # Используем ваш ID как админа
        from utils.advertising import Advertisement
        ad_id = len([ad for ad in dir() if "advertisement" in ad.lower()]) + 1
        advertisement = Advertisement(ad_id=ad_id, message=ad_text, ad_type="ad_type_text", bot=bot, creator_id=creator_id)
        asyncio.run_coroutine_threadsafe(advertisement.start(), dp.loop)
        return redirect(url_for('index'))
    return render_template('send_ad.html')

# Шаблоны Flask
if not os.path.exists('templates'):
    os.makedirs('templates')

with open('templates/index.html', 'w') as f:
    f.write('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weather Bot Admin</title>
    </head>
    <body>
        <h1>Управление ботом</h1>
        <h2>Список пользователей</h2>
        <ul>
        {% for user in users %}
            <li>ID: {{ user[1] }}, Username: {{ user[2] }}</li>
        {% endfor %}
        </ul>
        <a href="/send_ad">Отправить рекламу</a>
    </body>
    </html>
    ''')

with open('templates/send_ad.html', 'w') as f:
    f.write('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Отправить рекламу</title>
    </head>
    <body>
        <h1>Отправить рекламу</h1>
        <form method="post">
            <label for="ad_text">Текст рекламы:</label><br>
            <textarea id="ad_text" name="ad_text" rows="4" cols="50"></textarea><br>
            <input type="submit" value="Отправить">
        </form>
        <a href="/">Назад</a>
    </body>
    </html>
    ''')

# Запуск Flask в отдельном потоке
def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

# Запуск бота и веб-сервера
async def on_startup(_):
    print("Бот и веб-сервер запущены!")
    threading.Thread(target=run_flask, daemon=True).start()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)