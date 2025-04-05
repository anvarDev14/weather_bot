from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards.inline.weather_buttons import get_ad_type_keyboard, get_time_keyboard, get_cancel_keyboard, get_confirm_keyboard
from data.config import ADMINS
from utils.advertising import Advertisement, advertisements
from database.db import user_db
import datetime
import asyncio

class ReklamaTuriState(StatesGroup):
    tur = State()
    vaqt = State()
    time_value = State()
    content = State()
    buttons = State()

def setup(dp: Dispatcher):
    print("Setting up admin handlers")

    async def check_admin_permission(telegram_id):
        is_in_admins = telegram_id in ADMINS
        is_db_admin = user_db.check_if_admin(telegram_id)
        is_admin = is_in_admins or is_db_admin
        print(f"Checking admin permission for {telegram_id}: in ADMINS={is_in_admins}, in DB={is_db_admin}, result={is_admin}")
        return is_admin

    @dp.message_handler(commands=["reklama"])
    async def reklama_handler(message: types.Message):
        user_id = message.from_user.id
        print(f"Received /reklama from {user_id}")
        if await check_admin_permission(user_id):
            language = user_db.get_user_language(user_id)
            print(f"Admin check passed for {user_id}, language={language}")
            text = "Reklama turini tanlang:" if language == "uz" else "Выберите тип рекламы:"
            await message.answer(text, reply_markup=get_ad_type_keyboard(language))
            await ReklamaTuriState.tur.set()
        else:
            print(f"Admin check failed for {user_id}")
            language = user_db.get_user_language(user_id)
            await message.reply("Sizda ruxsat yo'q." if language == "uz" else "У вас нет прав.")

    @dp.callback_query_handler(lambda c: c.data in ["ad_type_text", "ad_type_forward", "ad_type_button", "ad_type_any"], state=ReklamaTuriState.tur)
    async def handle_ad_type(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(ad_type=callback.data)
        language = user_db.get_user_language(callback.from_user.id)
        print(f"Ad type selected: {callback.data} by {callback.from_user.id}")
        text = "Reklama yuborish vaqtini tanlang:" if language == "uz" else "Выберите время отправки рекламы:"
        await callback.message.edit_text(text, reply_markup=get_time_keyboard(language))
        await ReklamaTuriState.vaqt.set()

    @dp.callback_query_handler(lambda c: c.data in ["send_now", "send_later"], state=ReklamaTuriState.vaqt)
    async def handle_send_time(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(send_time=callback.data)
        language = user_db.get_user_language(callback.from_user.id)
        print(f"Send time selected: {callback.data} by {callback.from_user.id}")
        if callback.data == "send_later":
            text = "Reklamani yuborish uchun vaqtni kiriting (HH:MM):" if language == "uz" else "Введите время отправки рекламы (HH:MM):"
            await callback.message.edit_text(text)
            await ReklamaTuriState.time_value.set()
        else:
            text = "Reklama kontentini yuboring:" if language == "uz" else "Отправьте контент рекламы:"
            await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(language))
            await ReklamaTuriState.content.set()

    @dp.message_handler(state=ReklamaTuriState.time_value)
    async def handle_time_input(message: types.Message, state: FSMContext):
        time_value = message.text.strip()
        language = user_db.get_user_language(message.from_user.id)
        print(f"Time input received: {time_value} from {message.from_user.id}")
        try:
            send_time = datetime.datetime.strptime(time_value, '%H:%M')
            now = datetime.datetime.now()
            send_time = send_time.replace(year=now.year, month=now.month, day=now.day)
            if send_time < now:
                send_time += datetime.timedelta(days=1)
            await state.update_data(send_time_value=send_time)
            text = "Reklama kontentini yuboring:" if language == "uz" else "Отправьте контент рекламы:"
            await message.reply(text, reply_markup=get_cancel_keyboard(language))
            await ReklamaTuriState.content.set()
        except ValueError:
            await message.reply("❌ Vaqt formati noto'g'ri (HH:MM)." if language == "uz" else "❌ Неверный формат времени (HH:MM).")

    @dp.message_handler(state=ReklamaTuriState.content, content_types=types.ContentType.ANY)
    async def rek_state(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        print(f"Content received from {user_id}")
        if await check_admin_permission(user_id):
            data = await state.get_data()
            ad_type = data.get('ad_type')
            language = user_db.get_user_language(user_id)
            if ad_type == 'ad_type_button':
                await state.update_data(ad_content=message)
                text = "Tugmalarni kiriting (Button1 - URL1, Button2 - URL2):" if language == "uz" else "Введите кнопки (Button1 - URL1, Button2 - URL2):"
                await message.reply(text, reply_markup=get_cancel_keyboard(language))
                await ReklamaTuriState.buttons.set()
            else:
                await state.update_data(ad_content=message)
                text = "Reklamani yuborishni tasdiqlaysizmi?" if language == "uz" else "Подтверждаете отправку рекламы?"
                await message.answer(text, reply_markup=get_confirm_keyboard(language))
        else:
            language = user_db.get_user_language(user_id)
            await message.reply("Sizda ruxsat yo'q." if language == "uz" else "У вас нет прав.")

    @dp.message_handler(state=ReklamaTuriState.buttons)
    async def handle_buttons_input(message: types.Message, state: FSMContext):
        buttons_text = message.text.strip()
        language = user_db.get_user_language(message.from_user.id)
        print(f"Buttons input received: {buttons_text} from {message.from_user.id}")
        buttons = []
        try:
            for button_data in buttons_text.split(','):
                text_url = button_data.strip().split('-')
                if len(text_url) != 2:
                    raise ValueError("Incorrect format")
                text = text_url[0].strip()
                url = text_url[1].strip()
                buttons.append(types.InlineKeyboardButton(text=text, url=url))
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(*buttons)
            await state.update_data(keyboard=keyboard)
            text = "Reklamani yuborishni tasdiqlaysizmi?" if language == "uz" else "Подтверждаете отправку рекламы?"
            await message.answer(text, reply_markup=get_confirm_keyboard(language))
        except Exception:
            await message.reply("❌ Tugmalar formati noto'g'ri." if language == "uz" else "❌ Неверный формат кнопок.")

    @dp.callback_query_handler(lambda c: c.data == "cancel_ad", state='*')
    async def cancel_ad_handler(callback: types.CallbackQuery, state: FSMContext):
        language = user_db.get_user_language(callback.from_user.id)
        print(f"Ad cancelled by {callback.from_user.id}")
        await state.finish()
        await callback.message.edit_text("Reklama bekor qilindi 🤖❌" if language == "uz" else "Реклама отменена 🤖❌")

    @dp.callback_query_handler(lambda c: c.data == "confirm_ad", state='*')
    async def confirm_ad_handler(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        ad_type = data.get('ad_type')
        ad_content = data.get('ad_content')
        keyboard = data.get('keyboard')
        send_time = data.get('send_time_value') if data.get('send_time') == 'send_later' else None
        ad_id = len(advertisements) + 1
        advertisement = Advertisement(
            ad_id=ad_id,
            message=ad_content,
            ad_type=ad_type,
            bot=dp.bot,
            keyboard=keyboard,
            send_time=send_time,
            creator_id=callback.from_user.id
        )
        advertisements.append(advertisement)
        language = user_db.get_user_language(callback.from_user.id)
        print(f"Advertisement #{ad_id} added to list by {callback.from_user.id}, starting task")
        await state.finish()
        await callback.message.edit_text(f"Reklama #{ad_id} jadvalga qo'shildi." if language == "uz" else f"Реклама #{ad_id} добавлена в расписание.")
        advertisement.task = asyncio.create_task(advertisement.start())

    @dp.callback_query_handler(lambda c: c.data.startswith("pause_ad_"))
    async def pause_ad_handler(callback: types.CallbackQuery):
        ad_id = int(callback.data.split("_")[-1])
        advertisement = next((ad for ad in advertisements if ad.ad_id == ad_id), None)
        language = user_db.get_user_language(callback.from_user.id)
        if advertisement:
            await advertisement.pause()
            await callback.answer(f"Reklama #{ad_id} pauza holatiga o'tkazildi." if language == "uz" else f"Реклама #{ad_id} приостановлена.")
        else:
            await callback.answer("Reklama topilmadi." if language == "uz" else "Реклама не найдена.", show_alert=True)

    @dp.callback_query_handler(lambda c: c.data.startswith("resume_ad_"))
    async def resume_ad_handler(callback: types.CallbackQuery):
        ad_id = int(callback.data.split("_")[-1])
        advertisement = next((ad for ad in advertisements if ad.ad_id == ad_id), None)
        language = user_db.get_user_language(callback.from_user.id)
        if advertisement:
            await advertisement.resume()
            await callback.answer(f"Reklama #{ad_id} davom ettirildi." if language == "uz" else f"Реклама #{ad_id} возобновлена.")
        else:
            await callback.answer("Reklama topilmadi." if language == "uz" else "Реклама не найдена.", show_alert=True)

    @dp.callback_query_handler(lambda c: c.data.startswith("stop_ad_"))
    async def stop_ad_handler(callback: types.CallbackQuery):
        ad_id = int(callback.data.split("_")[-1])
        advertisement = next((ad for ad in advertisements if ad.ad_id == ad_id), None)
        language = user_db.get_user_language(callback.from_user.id)
        if advertisement:
            await advertisement.stop()
            await callback.answer(f"Reklama #{ad_id} to'xtatildi." if language == "uz" else f"Реклама #{ad_id} остановлена.")
        else:
            await callback.answer("Reklama topilmadi." if language == "uz" else "Реклама не найдена.", show_alert=True)