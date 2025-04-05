from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from handlers import users, admin, notifications, userss

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключаем обработчики
userss.setup(dp)
admin.setup(dp)

async def on_startup(_):
    print("Бот запущен!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)