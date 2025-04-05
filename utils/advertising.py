import asyncio
import datetime
from aiogram import types
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, RetryAfter, Unauthorized
from data.config import ADMINS
from database.db import user_db
from keyboards.inline.weather_buttons import get_status_keyboard

advertisements = []


class Advertisement:
    def __init__(self, ad_id, message, ad_type, bot, keyboard=None, send_time=None, creator_id=None):
        self.ad_id = ad_id
        self.message = message
        self.ad_type = ad_type
        self.bot = bot
        self.keyboard = keyboard
        self.send_time = send_time
        self.creator_id = creator_id
        self.running = False
        self.paused = False
        self.sent_count = 0
        self.failed_count = 0
        self.total_users = 0
        self.current_message = None
        self.task = None

    async def start(self):
        print(f"Starting advertisement #{self.ad_id} for creator {self.creator_id}")
        self.running = True
        try:
            if self.send_time:
                delay = (self.send_time - datetime.datetime.now()).total_seconds()
                print(f"Scheduled delay for ad #{self.ad_id}: {delay} seconds")
                if delay > 0:
                    await asyncio.sleep(delay)

            print(f"Fetching users for ad #{self.ad_id}")
            users = user_db.select_all_users()
            self.total_users = len(users)
            print(f"Total users to send ad #{self.ad_id}: {self.total_users}, users: {users}")

            if self.total_users == 0:
                print(f"No users found for ad #{self.ad_id}, aborting")
                self.running = False
                await self.bot.send_message(self.creator_id,
                                            f"Реклама #{self.ad_id} не отправлена: нет пользователей в базе.")
                return

            language = user_db.get_user_language(self.creator_id)
            print(f"Creator language for ad #{self.ad_id}: {language}")
            self.current_message = await self.bot.send_message(
                chat_id=self.creator_id,
                text=f"Reklama #{self.ad_id} boshlandi.\nYuborilgan: {self.sent_count}\nYuborilmagan: {self.failed_count}\nUmumiy: {self.sent_count + self.failed_count}/{self.total_users}\n\nStatus: Davom etmoqda" if language == "uz" else f"Реклама #{self.ad_id} началась.\nОтправлено: {self.sent_count}\nНе отправлено: {self.failed_count}\nВсего: {self.sent_count + self.failed_count}/{self.total_users}\n\nСтатус: В процессе",
                reply_markup=get_status_keyboard(self.ad_id, language=language)
            )
            print(f"Sent initial status message for ad #{self.ad_id} to {self.creator_id}")

            for user in users:
                if not self.running:
                    print(f"Ad #{self.ad_id} stopped before sending")
                    break
                while self.paused:
                    await asyncio.sleep(1)
                    if not self.running:
                        print(f"Ad #{self.ad_id} stopped while paused")
                        break
                user_id = user[1]  # Предполагается, что user[1] — это user_id
                print(f"Attempting to send ad #{self.ad_id} to user {user_id}")
                try:
                    await send_advertisement_to_user(user_id, self)
                    self.sent_count += 1
                    print(f"Successfully sent ad #{self.ad_id} to {user_id}")
                except (BotBlocked, ChatNotFound, Unauthorized):
                    self.failed_count += 1
                    print(f"Failed to send ad #{self.ad_id} to {user_id}: user blocked or chat not found")
                except RetryAfter as e:
                    await asyncio.sleep(e.timeout)
                    print(f"RetryAfter delay for ad #{self.ad_id} to {user_id}: {e.timeout} seconds")
                except Exception as e:
                    self.failed_count += 1
                    print(f"Unexpected error sending ad #{self.ad_id} to {user_id}: {e}")
                await asyncio.sleep(0.1)  # Задержка для соблюдения лимитов Telegram
                if (self.sent_count + self.failed_count) % 10 == 0:
                    await self.update_status_message()

            self.running = False
            self.paused = False
            await self.update_status_message(finished=True)
            print(f"Ad #{self.ad_id} completed: sent={self.sent_count}, failed={self.failed_count}")

        except Exception as e:
            print(f"Error in start() for ad #{self.ad_id}: {e}")
            self.running = False
            await self.bot.send_message(self.creator_id, f"Ошибка при запуске рекламы #{self.ad_id}: {str(e)}")

    async def pause(self):
        self.paused = True
        await self.update_status_message()
        print(f"Ad #{self.ad_id} paused")

    async def resume(self):
        self.paused = False
        await self.update_status_message()
        print(f"Ad #{self.ad_id} resumed")

    async def stop(self):
        self.running = False
        await self.update_status_message(stopped=True)
        print(f"Ad #{self.ad_id} stopped")

    async def update_status_message(self, finished=False, stopped=False):
        language = user_db.get_user_language(self.creator_id)
        status = "Yakunlandi" if finished else (
            "To'xtatildi" if stopped else ("Pauza holatida" if self.paused else "Davom etmoqda"))
        status_ru = "Завершено" if finished else (
            "Остановлено" if stopped else ("На паузе" if self.paused else "В процессе"))
        if self.current_message:
            try:
                await self.current_message.edit_text(
                    text=f"Reklama #{self.ad_id}\nYuborilgan: {self.sent_count}\nYuborilmagan: {self.failed_count}\nUmumiy: {self.sent_count + self.failed_count}/{self.total_users}\n\nStatus: {status}" if language == "uz" else f"Реклама #{self.ad_id}\nОтправлено: {self.sent_count}\nНе отправлено: {self.failed_count}\nВсего: {self.sent_count + self.failed_count}/{self.total_users}\n\nСтатус: {status_ru}",
                    reply_markup=None if finished or stopped else get_status_keyboard(self.ad_id, self.paused, language)
                )
                print(f"Updated status message for ad #{self.ad_id}")
            except Exception as e:
                print(f"Failed to update status message for ad #{self.ad_id}: {e}")


async def send_advertisement_to_user(chat_id, advertisement: Advertisement):
    message = advertisement.message
    ad_type = advertisement.ad_type
    keyboard = advertisement.keyboard
    caption = message.caption or message.text or "Matn mavjud emas." if user_db.get_user_language(
        chat_id) == "uz" else "Текст отсутствует."
    print(f"Sending ad type {ad_type} to {chat_id}")
    try:
        if ad_type == 'ad_type_text':
            await advertisement.bot.send_message(chat_id=chat_id, text=caption)
        elif ad_type == 'ad_type_button':
            await handle_content_with_keyboard(chat_id, message, keyboard, caption, advertisement.bot)
        elif ad_type == 'ad_type_forward':
            await advertisement.bot.forward_message(chat_id=chat_id, from_chat_id=message.chat.id,
                                                    message_id=message.message_id)
        elif ad_type == 'ad_type_any':
            await handle_non_text_content(chat_id, message, advertisement.bot)
        else:
            await handle_non_text_content(chat_id, message, advertisement.bot)
    except Exception as e:
        raise e  # Передаем исключение выше для обработки в start()


async def handle_content_with_keyboard(chat_id, message, keyboard, caption, bot):
    print(f"Handling content with keyboard for {chat_id}, type: {message.content_type}")
    if message.content_type == types.ContentType.TEXT:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)
    elif message.content_type == types.ContentType.PHOTO:
        await bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
    elif message.content_type == types.ContentType.VIDEO:
        await bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=caption, reply_markup=keyboard)
    elif message.content_type == types.ContentType.DOCUMENT:
        await bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=caption,
                                reply_markup=keyboard)
    elif message.content_type == types.ContentType.AUDIO:
        await bot.send_audio(chat_id=chat_id, audio=message.audio.file_id, caption=caption, reply_markup=keyboard)
    elif message.content_type == types.ContentType.ANIMATION:
        await bot.send_animation(chat_id=chat_id, animation=message.animation.file_id, caption=caption,
                                 reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)


async def handle_non_text_content(chat_id, message, bot):
    print(f"Handling non-text content for {chat_id}, type: {message.content_type}")
    if message.content_type == types.ContentType.TEXT:
        text = message.text or "Matn mavjud emas." if user_db.get_user_language(
            chat_id) == "uz" else "Текст отсутствует."
        await bot.send_message(chat_id=chat_id, text=text)
    elif message.content_type == types.ContentType.PHOTO:
        await bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=message.caption)
    elif message.content_type == types.ContentType.VIDEO:
        await bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=message.caption)
    elif message.content_type == types.ContentType.DOCUMENT:
        await bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=message.caption)
    elif message.content_type == types.ContentType.AUDIO:
        await bot.send_audio(chat_id=chat_id, audio=message.audio.file_id, caption=message.caption)
    elif message.content_type == types.ContentType.ANIMATION:
        await bot.send_animation(chat_id=chat_id, animation=message.animation.file_id, caption=message.caption)
    else:
        await bot.send_message(chat_id=chat_id,
                               text="Yuboriladigan kontent turi qo'llab-quvvatlanmaydi." if user_db.get_user_language(
                                   chat_id) == "uz" else "Тип отправляемого контента не поддерживается.")