from aiogram import Bot
from data.config import ADMINS
from database.db import user_db


async def notify_admin_new_user(bot: Bot, user_id: int, username: str):
    for admin in ADMINS:
        await bot.send_message(admin, f"Yangi foydalanuvchi: @{username} (ID: {user_id})" if user_db.get_user_language(admin) == "uz" else f"Новый пользователь: @{username} (ID: {user_id})")