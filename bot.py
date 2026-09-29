import os
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# =====================================================================
# 1. КОНФИГУРАЦИЯ (ВАШИ ДАННЫЕ ВШИТЫ)
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8698519060:AAFMCj3zZHAjxrANyC4al0pM-TAblht-s_M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5014057300"))

# Координаты базы отдыха «Русалочка»
GEO_LATITUDE = 44.821360
GEO_LONGITUDE = 37.498864

# Каталог категорий номеров
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "description": (
            "Уютный просторный номер-студия с собственной оборудованной кухней. "
            "Идеально подходит для пары или семьи с одним ребенком."
        ),
        "details": (
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место (кресло-кровать / диван)\n"
            "• Оборудованная мини-кухня (плита, СВЧ, чайник, холодильник, посуда)\n"
            "• Сплит-система, ЖК-телевизор\n"
            "• Собственный санузел с душем и туалетно-косметическими наборами\n"
            "• Балкон/терраса с летней мебелью"
        ),
        "image_url": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "description": (
            "Комфортабельный семейный апартамент увеличенной площади с кухней "
            "и полноценной спальной зоной для 3–4 гостей."
        ),
        "details": (
            "<b>В номере:</b>\n"
            "• Двуспальная и односпальная кровати + раскладное доп. место\n"
            "• Полный кухонный блок: холодильник, варочная панель, СВЧ, обеденная группа\n"
            "• Сплит-система, кабельное ТВ, Wi-Fi\n"
            "• Просторная ванная комната\n"
            "• Индивидуальная веранда/балкон для отдыха"
        ),
        "image_url": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1000&q=80",
    },
    "eco_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "description": (
            "Отдельно стоящий домик из экологически чистого бруса с ароматом натурального дерева "
            "и отдельной верандой среди зелени."
        ),
        "details": (
            "<b>В домике:</b>\n"
            "• Ортопедическая двуспальная кровать + кресло-кровать\n"
            "• Экологичная отделка из массива дерева\n"
            "• Сплит-система, холодильник, электрочайник, телевизор\n"
            "• Санузел с душевой кабиной\n"
            "• Собственная терраса со столом и стульями"
        ),
        "image_url": "https://images.unsplash.com/photo-1587061949409-02df41d5e562?auto=format&fit=crop&w=1000&q=80",
    },
}

# =====================================================================
# 2. FSM (МАШИНА СОСТОЯНИЙ)
# =====================================================================
class BookingState(StatesGroup):
    choosing_room = State()
    waiting_dates = State()
    waiting_guests = State()
    waiting_name = State()
    waiting_phone = State()

# =====================================================================
# 3. КЛАВИАТУРЫ
# =====================================================================
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🏡 Наши номера"), KeyboardButton(text="📝 Забронировать")],
        [KeyboardButton(text="🏊‍♂️ Бассейн"), KeyboardButton(text="🌴 О базе")],
        [KeyboardButton(text="🎡 Инфраструктура и развлечения")],
        [KeyboardButton(text="❓ Вопросы и ответы (FAQ)"), KeyboardButton(text="📞 Контакты и локация")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить бронирование")]],
        resize_keyboard=True
    )

def get_phone_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📱 Отправить контакт", request_contact=True)],
        [KeyboardButton(text="❌ Отменить бронирование")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_room_card_keyboard(room_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"room_info:{room_key}"),
                InlineKeyboardButton(text="🛎 Забронировать этот номер", callback_data=f"book_direct:{room_key}")
            ]
        ]
    )

def get_room_selection_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"select_room:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking_inline")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_faq_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Время заезда и выезда", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="🐾 Можно ли с питомцами?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="💳 Оплата и предоплата", callback_data="faq:payment")],
            [InlineKeyboardButton(text="📍 Как к вам добраться?", callback_data="faq:route")],
        ]
    )

def get_faq_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️️ Назад в FAQ", callback_data="faq:back")]
        ]
    )

# =====================================================================
# 4. РОУТЕР И ОБРАБОТЧИКИ
# =====================================================================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "<b>Добро пожаловать в базу отдыха «Русалочка»! 🌊</b>\n\n"
        "Здесь вас ждет комфортный отдых, чистый морской воздух, уютные эко-номера "
        "и атмосфера абсолютного релакса.\n\n"
        "Выберите интересующий раздел в меню ниже ⬇️"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

@router.message(F.text == "❌ Отменить бронирование")
async def cancel_booking_text(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("Процесс бронирования отменен.", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())

@router.message(F.text == "🏡 Наши номера")
async def show_rooms(message: Message):
    await message.answer("<b>Категории номеров базы отдыха «Русалочка»:</b>")
    for key, room in ROOMS_CATALOG.items():
        caption = f"<b>{room['title']}</b>\n\n{room['description']}"
        await message.answer_photo(
            photo=room["image_url"],
            caption=caption,
            reply_markup=get_room_card_keyboard(key)
        )

@router.callback_query(F.data.startswith("room_info:"))
async def handle_room_info(callback: CallbackQuery):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        await callback.answer("Номер не найден.", show_alert=True)
        return

    text = f"<b>Детальная информация:</b>\n<i>{room['title']}</i>\n\n{room['details']}"
    await callback.message.reply(text)
    await callback.answer()

@router.message(F.text == "🏊‍♂️ Бассейн")
async def show_pool(message: Message):
    pool_photo = "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1000&q=80"
    caption = (
        "<b>🏊‍♂️ Зона отдыха с открытым бассейном</b>\n\n"
        "На территории «Русалочки» работает просторный бассейн под открытым небом:\n"
        "• Чистейшая вода с современной системой фильтрации\n"
        "• Зона для безопасного купания детей\n"
        "• Шезлонги и теневые навесы для комфортного загара\n"
        "• Время работы: с 08:00 до 22:00\n\n"
        "Пользование бассейном и шезлонгами входит в стоимость проживания!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛎 Забронировать отдых", callback_data="start_booking_from_pool")]
        ]
    )
    await message.answer_photo(photo=pool_photo, caption=caption, reply_markup=kb)

@router.message(F.text == "🌴 О базе")
async def show_about(message: Message):
    about_text = (
        "<b>🌴 База отдыха «Русалочка»</b>\n\n"
        "Мы создали пространство для идеального семейного и романтического отпуска:\n"
        "• Зеленая, благоустроенная закрытая территория\n"
        "• Шаговая доступность до песчаного морского побережья\n"
        "• Тихая локация без громких ночных заведений\n"
        "• Просторные номера и эко-домики с продуманным оснащением\n\n"
        "Узнайте больше и посмотрите фотогалерею на нашем официальном сайте:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Перейти на сайт rusalo4ka.com", url="https://rusalo4ka.com/")]
        ]
    )
    await message.answer(about_text, reply_markup=kb)

@router.message(F.text == "🎡 Инфраструктура и развлечения")
async def show_infrastructure(message: Message):
    infra_text = (
        "<b>🎡 Инфраструктура базы отдыха:</b>\n\n"
        "🥩 <b>Мангальные зоны:</b> оборудованные площадки с мангалами, шампурами и беседками.\n"
        "🛝 <b>Детская площадка:</b> качели, горки и безопасный игровой комплекс.\n"
        "📶 <b>Бесплатный Wi-Fi:</b> доступен на всей территории и в номерах.\n"
        "🅿️️ <b>Парковка:</b> охраняемая стоянка под видеонаблюдением для гостей.\n"
        "🎲 <b>Зоны отдыха:</b> столы для настольного тенниса, настольные игры для всей семьи."
    )
    await message.answer(infra_text)

@router.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def show_faq(message: Message):
    await message.answer(
        "<b>Часто задаваемые вопросы (FAQ):</b>\nНажмите на интересующий вопрос для получения ответа:",
        reply_markup=get_faq_inline_keyboard()
    )

@router.callback_query(F.data.startswith("faq:"))
async def handle_faq_item(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    faq_answers = {
        "checkin": (
            "<b>🕒 Время заезда и выезда:</b>\n\n"
            "• Стандартный <b>заезд</b> — с <b>14:00</b>\n"
            "• Стандартный <b>выезд</b> — до <b>12:00</b>\n\n"
            "Ранний заезд и поздний выезд обсуждаются индивидуально с администратором при наличии свободных номеров."
        ),
        "pets": (
            "<b>🐾 Размещение с домашними животными:</b>\n\n"
            "Мы любим животных, однако пребывание с питомцами возможно строго по предварительному "
            "согласованию с администрацией (зависит от породы и размера животного)."
        ),
        "payment": (
            "<b>💳 Оплата и бронирование:</b>\n\n"
            "• Для фиксации брони вносится предоплата в размере одних суток проживания.\n"
            "• Оставшаяся сумма оплачивается при заселении наличными или банковским переводом.\n"
            "• Бесплатная отмена возможна за 14 дней до даты заезда."
        ),
        "route": (
            "<b>📍 Как к вам добраться:</b>\n\n"
            "База отдыха расположена в курортной зоне на побережье.\n"
            "Вы можете добраться на автомобиле по навигатору, либо на такси/трансфере от ближайшего ж/д вокзала и аэропорта. "
            "Точную локацию можно открыть через меню «Контакты и локация»."
        )
    }

    if action == "back":
        await callback.message.edit_text(
            "<b>Часто задаваемые вопросы (FAQ):</b>\nНажмите на интересующий вопрос для получения ответа:",
            reply_markup=get_faq_inline_keyboard()
        )
    else:
        text = faq_answers.get(action, "Информация уточняется.")
        await callback.message.edit_text(text, reply_markup=get_faq_back_keyboard())

    await callback.answer()

@router.message(F.text == "📞 Контакты и локация")
async def show_contacts(message: Message):
    contacts_text = (
        "<b>📞 Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Курортная зона, б/о «Русалочка»\n"
        "📞 <b>Телефон отдела бронирования:</b> +7 (900) 000-00-00\n"
        "💬 <b>WhatsApp / Telegram:</b> @rusalo4ka_manager\n"
        "🌐 <b>Официальный сайт:</b> https://rusalo4ka.com/\n\n"
        "Ниже отправляем точку на карте для навигатора 📍"
    )
    await message.answer(contacts_text)
    await message.answer_location(latitude=GEO_LATITUDE, longitude=GEO_LONGITUDE)

# --- FSM СЦЕНАРИЙ БРОНИРОВАНИЯ ---
@router.message(F.text == "📝 Забронировать")
@router.callback_query(F.data == "start_booking_from_pool")
async def start_booking_flow(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = "<b>Шаг 1 из 5:</b> Выберите категорию номера, которую хотите забронировать:"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_room_selection_inline_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_room_selection_inline_keyboard())
    await state.set_state(BookingState.choosing_room)

@router.callback_query(F.data.startswith("book_direct:"))
async def start_booking_direct(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)

    await state.update_data(room_name=room["title"] if room else "Номер выбран")
    await callback.message.answer(
        f"Вы выбрали: <b>{room['title']}</b>\n\n"
        "<b>Шаг 2 из 5:</b> Укажите желаемые <b>даты заезда и выезда</b>.\n"
        "<i>Пример: 15.07 - 25.07</i>",
        reply_markup=get_cancel_reply_keyboard()
    )
    await callback.answer()
    await state.set_state(BookingState.waiting_dates)

@router.callback_query(BookingState.choosing_room, F.data.startswith("select_room:"))
async def process_room_choice(callback: CallbackQuery, state: FSMContext):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    room_title = room["title"] if room else "Номер выбран"

    await state.update_data(room_name=room_title)
    await callback.message.edit_text(f"Выбран номер: <b>{room_title}</b>")
    await callback.message.answer(
        "<b>Шаг 2 из 5:</b> Введите желаемые <b>даты заезда и выезда</b>.\n"
        "<i>Пример: 01.08 - 10.08</i>",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_dates)
    await callback.answer()

@router.callback_query(BookingState.choosing_room, F.data == "cancel_booking_inline")
async def cancel_booking_inline_btn(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.message(BookingState.waiting_dates, F.text)
async def process_dates(message: Message, state: FSMContext):
    await state.update_data(dates=message.text.strip())
    await message.answer(
        "<b>Шаг 3 из 5:</b> Сколько человек планирует отдыхать?\n"
        "<i>(Укажите количество взрослых и возраст детей, например: 2 взрослых + ребенок 6 лет)</i>",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_guests)

@router.message(BookingState.waiting_guests, F.text)
async def process_guests(message: Message, state: FSMContext):
    await state.update_data(guests=message.text.strip())
    await message.answer(
        "<b>Шаг 4 из 5:</b> Как к вам обращаться? (Ваше Имя и Фамилия):",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_name)

@router.message(BookingState.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "<b>Шаг 5 из 5:</b> Укажите контактный номер телефона для подтверждения бронирования.\n"
        "Вы можете нажать кнопку ниже или ввести номер вручную:",
        reply_markup=get_phone_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_phone)

@router.message(BookingState.waiting_phone, F.contact | F.text)
async def process_phone_and_finish(message: Message, state: FSMContext, bot: Bot):
    phone = message.contact.phone_number if message.contact else message.text.strip()

    data = await state.get_data()
    room_name = data.get("room_name", "Не указан")
    dates = data.get("dates", "Не указаны")
    guests = data.get("guests", "Не указано")
    guest_name = data.get("name", "Гость")

    order_id = datetime.now().strftime("%d%m-%H%M%S")

    # 1. Ответ клиенту
    user_confirm_text = (
        f"🎉 <b>Спасибо, {guest_name}!</b>\n\n"
        f"Ваша заявка на бронирование <b>№{order_id}</b> успешно принята.\n\n"
        "<b>Параметры брони:</b>\n"
        f"• Номер: {room_name}\n"
        f"• Даты: {dates}\n"
        f"• Состав гостей: {guests}\n"
        f"• Телефон: {phone}\n\n"
        "Администратор свяжется с вами в ближайшее время для подтверждения и внесения предоплаты."
    )
    await message.answer(user_confirm_text, reply_markup=get_main_menu_keyboard())

    # 2. Мгновенная заявка в чат администратора (ID: 5014057300)
    username = f"@{message.from_user.username}" if message.from_user.username else "Отсутствует"
    user_id = message.from_user.id

    admin_notification = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА БРОНЬ (№{order_id}):</b>\n\n"
        f"• <b>Категория:</b> {room_name}\n"
        f"• <b>Даты:</b> {dates}\n"
        f"• <b>Гости:</b> {guests}\n"
        f"• <b>Имя:</b> {guest_name}\n"
        f"• <b>Телефон:</b> <code>{phone}</code>\n"
        f"• <b>Telegram:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"• <b>Время заявки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification)
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление администратору: {e}")

    await state.clear()

# =====================================================================
# 5. ЗАПУСК
# =====================================================================
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот базы отдыха «Русалочка» запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
