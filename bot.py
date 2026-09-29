import os
import re
import asyncio
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

import aiohttp
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# =====================================================================
# 1. КОНФИГУРАЦИЯ И ДАННЫЕ
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8698519060:AAFMCj3zZHAjxrANyC4al0pM-TAblht-s_M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5014057300"))

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "max_guests": 3,
        "price_per_night": 4500,
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 2-х местный + доп.место</b>\n\n"
            "Уютный семейный апартамент с индивидуальной кухонной зоной.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место (диван/кресло-кровать)\n"
            "• Оборудованная кухня: плита, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi\n"
            "• Санузел с душевой кабиной\n"
            "• Индивидуальная веранда/балкон\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/c3c/600_400_1/c3c97d74db5e26b8cb7974531be32717.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "max_guests": 4,
        "price_per_night": 5500,
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 3-х местный + доп.место</b>\n\n"
            "Просторный апартамент для семейного отпуска.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать, 1-спальная кровать + доп. место\n"
            "• Кухонный модуль: варочная панель, СВЧ, холодильник, посуда\n"
            "• Сплит-система, кабельное ТВ, Wi-Fi\n"
            "• Ванная комната с душем\n"
            "• Летняя зона отдыха на веранде\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/d3c/600_400_1/d3c92df78508e92fba8933e146eb4a05.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1000&q=80",
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "max_guests": 3,
        "price_per_night": 4000,
        "description": (
            "🏡 <b>Эко-домик 1-комнатный 2-х местный + доп.место</b>\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "<b>В домике:</b>\n"
            "• Двуспальная кровать + кресло-кровать\n"
            "• Сплит-система, холодильник, чайник, телевизор\n"
            "• Санузел с душем\n"
            "• Собственная терраса со столом и стульями\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/e7a/600_400_1/e7a6d8feea4cb804da6c39a3f9e9cf24.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1587061949409-02df41d5e562?auto=format&fit=crop&w=1000&q=80",
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "max_guests": 4,
        "price_per_night": 6000,
        "description": (
            "🏡 <b>Эко-домик 2-комнатный 3-х местный + доп.место</b>\n\n"
            "Двухкомнатный коттедж из бруса для семьи до 4 человек.\n\n"
            "<b>В домике:</b>\n"
            "• 2 изолированные комнаты из эко-бруса\n"
            "• 3 основных спальных места + евро-раскладушка\n"
            "• Кондиционер, холодильник, ТВ, чайник\n"
            "• Санузел с душевой кабиной\n"
            "• Деревянная веранда для отдыха\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/f8d/600_400_1/f8dbb24b89ebc90539fbeceae47c87c9.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1000&q=80",
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "max_guests": 3,
        "price_per_night": 3500,
        "description": (
            "🏡 <b>СТАНДАРТ кирпичный домик 3-х местный</b>\n\n"
            "Капитальный прохладный домик для комфортного отдыха 3 гостей.\n\n"
            "<b>В домике:</b>\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Индивидуальная веранда перед домиком"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/b3b/600_400_1/b3b8dfa2e6fca78e1189c4908051a8eb.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=1000&q=80",
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "max_guests": 2,
        "price_per_night": 2800,
        "description": (
            "🏡 <b>СТАНДАРТ Деревянный домик 2-х местный</b>\n\n"
            "Уютный деревянный домик для двоих в тени лаванды и роз.\n\n"
            "<b>В домике:</b>\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Открытая терраса со столиком"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/a9f/600_400_1/a9fc2ce6fe7a77b81b8979c3f0b2fcf7.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1000&q=80",
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "max_guests": 3,
        "price_per_night": 3200,
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный + доп.место</b>\n\n"
            "Классический светлый номер стандарт.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, ТВ, холодильник, чайник\n"
            "• Санузел и душевая\n"
            "• Терраса для отдыха"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/17a/600_400_1/17ae86be4efb702ec8c6cceee69a8bfe.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80",
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный + доп.место",
        "max_guests": 4,
        "price_per_night": 3800,
        "description": (
            "🏡 <b>СТАНДАРТ 3-х местный + доп.место</b>\n\n"
            "Удобный номер для семьи из 3-4 человек.\n\n"
            "<b>В номере:</b>\n"
            "• 3 основных спальных места + евро-раскладушка\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Веранда для вечернего чаепития"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/28a/600_400_1/28a47eb38cbf917c093498877bc9ec7e.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1000&q=80",
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "max_guests": 5,
        "price_per_night": 4600,
        "description": (
            "🏡 <b>СТАНДАРТ 4-х местный + доп.место</b>\n\n"
            "Просторный семейный номер на 4-5 человек.\n\n"
            "<b>В номере:</b>\n"
            "• 4 основных спальных места + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ, чайник\n"
            "• Санузел с душем\n"
            "• Собственная летняя веранда"
        ),
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/39b/600_400_1/39ba579fcbb6ae083d987d605177265a.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
    },
}

# =====================================================================
# ФУНКЦИЯ ЗАГРУЗКИ ФОТОГРАФИЙ (ОБХОД БЛОКИРОВКИ ХОТЛИНКА)
# =====================================================================
async def send_room_photo(message: Message, room: Dict[str, Any], caption: str, reply_markup: InlineKeyboardMarkup):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://rusalo4ka.com/",
    }
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(room["site_image_url"]) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = BufferedInputFile(file=image_data, filename="room.jpg")
                    await message.answer_photo(photo=file, caption=caption, reply_markup=reply_markup)
                    return
    except Exception as e:
        logging.warning(f"Ошибка загрузки фото с сайта rusalo4ka.com: {e}")

    try:
        await message.answer_photo(photo=room.get("fallback_image_url"), caption=caption, reply_markup=reply_markup)
    except Exception:
        await message.answer(text=caption, reply_markup=reply_markup)

def parse_dates(text: str) -> Tuple[bool, int, str, str, str]:
    pattern = r"(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?\s*[-—–toдо\s]+\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?"
    match = re.search(pattern, text)
    if not match:
        return False, 0, "", "", text

    d1, m1, y1, d2, m2, y2 = match.groups()
    current_year = datetime.now().year
    season_year = current_year if datetime.now().month <= 9 else current_year + 1
    year1 = int(y1) if y1 else season_year
    year2 = int(y2) if y2 else season_year

    try:
        dt1 = datetime(year1, int(m1), int(d1))
        dt2 = datetime(year2, int(m2), int(d2))
        nights = (dt2 - dt1).days
        if nights <= 0:
            return False, 0, "", "", text
        
        date_in = f"{dt1.strftime('%d.%m.%Y')} (заезд с 13:00)"
        date_out = f"{dt2.strftime('%d.%m.%Y')} (выезд до 11:00)"
        full_text = f"{dt1.strftime('%d.%m.%Y')} — {dt2.strftime('%d.%m.%Y')}"
        return True, nights, date_in, date_out, full_text
    except ValueError:
        return False, 0, "", "", text

# =====================================================================
# 2. FSM (МАШИНА СОСТОЯНИЙ)
# =====================================================================
class BookingFlow(StatesGroup):
    waiting_dates = State()
    choosing_room = State()
    waiting_guests = State()
    confirm_price = State()
    waiting_fullname = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_notes = State()

# =====================================================================
# 3. КЛАВИАТУРЫ
# =====================================================================
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🏡 Наши номера"), KeyboardButton(text="📝 Забронировать")],
        [KeyboardButton(text="🏊‍♂️ Бассейн"), KeyboardButton(text="🌴 О базе")],
        [KeyboardButton(text="🎡 Инфраструктура и услуги"), KeyboardButton(text="⭐ Отзывы")],
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

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Пропустить")],
            [KeyboardButton(text="❌ Отменить бронирование")]
        ],
        resize_keyboard=True
    )

def get_rooms_list_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"view_room:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_single_room_keyboard(room_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛎 Забронировать этот номер", callback_data=f"book_room_target:{room_key}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку категорий", callback_data="back_to_rooms_catalog")]
        ]
    )

def get_rooms_booking_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']} ({data['price_per_night']} ₽/сут)", callback_data=f"select_room_fsm:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отменить бронирование", callback_data="cancel_fsm_cb")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_guests_keyboard(max_guests: int) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=f"👤 {i} чел.", callback_data=f"set_guests_fsm:{i}")
        for i in range(1, max_guests + 1)
    ]
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text="❌ Отменить бронирование", callback_data="cancel_fsm_cb")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_payment_decision_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить (Внести предоплату 30%)", callback_data="pay_prepayment_click")],
            [InlineKeyboardButton(text="❌ Отменить бронирование", callback_data="cancel_fsm_cb")]
        ]
    )

# =====================================================================
# 4. ОБРАБОТЧИКИ МЕНЮ
# =====================================================================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "<b>Добро пожаловать в базу отдыха «Русалочка»! 🌊</b>\n\n"
        "Семейный отдых на песчаном побережье в станице Благовещенская (Анапа).\n"
        "Большой бассейн с морской водой, уютные эко-домики и номера с оборудованной кухней!\n\n"
        "📅 <b>Период работы базы: с 15 июня по 15 сентября</b>\n"
        "🕒 <b>Заезд — с 13:00 | Выезд — до 11:00</b>\n\n"
        "Выберите нужный раздел в меню ниже ⬇"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())

@router.message(F.text == "❌ Отменить бронирование")
async def cancel_booking_text(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "cancel_fsm_cb")
async def cancel_fsm_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- НАШИ НОМЕРА ---
@router.message(F.text == "🏡 Наши номера")
async def show_rooms(message: Message):
    text = (
        "<b>🏡 Категории номеров базы отдыха «Русалочка»:</b>\n\n"
        "Нажмите на интересующую категорию, чтобы посмотреть реальные фотографии, "
        "комплектацию и условия:"
    )
    await message.answer(text, reply_markup=get_rooms_list_keyboard())

@router.callback_query(F.data == "back_to_rooms_catalog")
async def back_to_catalog(callback: CallbackQuery):
    await callback.message.delete()
    text = (
        "<b>🏡 Категории номеров базы отдыха «Русалочка»:</b>\n\n"
        "Нажмите на категорию для просмотра фотографий и описания:"
    )
    await callback.message.answer(text, reply_markup=get_rooms_list_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("view_room:"))
async def view_single_room(callback: CallbackQuery):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    await callback.message.delete()
    caption = (
        f"{room['description']}\n\n"
        f"👥 <b>Вместимость:</b> до {room['max_guests']} человек\n"
        f"💰 <b>Стоимость:</b> от {room['price_per_night']} ₽ / сутки"
    )
    await send_room_photo(
        message=callback.message,
        room=room,
        caption=caption,
        reply_markup=get_single_room_keyboard(room_key)
    )
    await callback.answer()

# --- ОТЗЫВЫ ---
@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    url = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⭐ Открыть отзывы на Яндекс.Картах", url=url)]]
    )
    await message.answer(
        "<b>⭐ Отзывы наших гостей:</b>\n\n"
        "Ознакомьтесь с реальными впечатлениями, оценками и фотографиями отдыхающих "
        "на официальной странице базы на Яндекс.Картах:",
        reply_markup=kb
    )

# --- БАССЕЙН ---
@router.message(F.text == "🏊‍♂️ Бассейн")
async def show_pool(message: Message):
    caption = (
        "<b>🏊‍♂ Самый большой бассейн в округе!</b>\n"
        "<i>Кристально чистая морская вода, безопасная зона для малышей и комфортные шезлонги для загара.</i>\n\n"
        "<b>Абонементы на посещение:</b>\n"
        "✅ <b>Для гостей, проживающих в номерах категории «Эко Домик» и «Номер с кухней (апарт.)», пользование бассейном:</b>\n"
        "👉 <b>БЕСПЛАТНО</b>\n\n"
        "Остальные гости могут приобрести доступ к бассейну за дополнительную плату в администрации:\n\n"
        "• <b>1 час:</b> Взрослый/Детский (с 4 лет) — <b>180 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n"
        "• <b>1 день:</b> Взрослый/Детский (с 4 лет) — <b>550 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n"
        "• <b>5 дней:</b> Взрослый/Детский (с 4 лет) — <b>1 950 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n\n"
        "⚠️ <i>Дети до 14 лет могут посещать бассейн только в сопровождении взрослых.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛎 Забронировать отдых", callback_data="start_booking_fsm")]]
    )
    pool_stub = {
        "site_image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/785/800_600_1/7858c9735d6e066a33c2a3e5c942488a.jpg",
        "fallback_image_url": "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1000&q=80"
    }
    await send_room_photo(message=message, room=pool_stub, caption=caption, reply_markup=kb)

# --- ИНФРАСТРУКТУРА ---
@router.message(F.text == "🎡 Инфраструктура и услуги")
async def show_infra(message: Message):
    text = (
        "<b>🎡 ИНФРАСТРУКТУРА И УСЛУГИ</b>\n\n"
        "✅ <b>ВКЛЮЧЕНО В СТОИМОСТЬ:</b>\n\n"
        "👶 <b>Детская площадка</b>\n"
        "Игровой комплекс для малышей на свежем воздухе.\n\n"
        "⚽ <b>Спортивный инвентарь</b>\n"
        "Мячи, ракетки, настольный теннис, шахматы, шашки и настольный футбол — всё для активного отдыха.\n\n"
        "🥩 <b>Мангальная зона</b>\n"
        "Оборудованная зона отдыха с бесплатным предоставлением решеток, шампуров, печи и казана (12 л).\n\n"
        "🌸 <b>Зеленая зона</b>\n"
        "Зеленая территория: 350 кустов роз и 1100 кустов лаванды.\n\n"
        "------------------------------------\n\n"
        "💲 <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:</b>\n\n"
        "🎨 <b>Студия творчества и шоу</b>\n"
        "Регулярные шоу-программы и мастер-классы (создание слаймов, блеск-тату, роспись футболок, кепок и фигурок).\n\n"
        "🚲 <b>Полезный сервис</b>\n"
        "Прокат детских колясок (от 0 до 5 лет), детских и взрослых велосипедов/самокатов. Прачечная и гладильная комната. "
        "Зарядная станция для авто GB/T 7kwt (Цена 22₽/ 1 кВт.ч).\n\n"
        "☕ <b>Вкусные радости</b>\n"
        "Натуральный зерновой кофе, прохладительные напитки и вкусный шашлык, который приготовят прямо при вас."
    )
    await message.answer(text)

# --- О БАЗЕ ---
@router.message(F.text == "🌴 О базе")
async def show_about(message: Message):
    text = (
        "<b>🌴 Семейная база отдыха «Русалочка»</b>\n\n"
        "«Рай для ваших детей и спокойный отдых для родителей!»\n"
        "Пока взрослые расслабляются, детям всегда есть чем заняться.\n\n"
        "• Закрытая зеленая территория\n"
        "• Шаговая доступность к просторному пляжу и морю\n"
        "• Открытый бассейн, детский городок и анимация\n"
        "• Период работы: <b>с 15 июня по 15 сентября</b>\n"
        "• Официальный сайт: https://rusalo4ka.com/"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 Открыть сайт rusalo4ka.com", url="https://rusalo4ka.com/")]]
    )
    await message.answer(text, reply_markup=kb)

# --- КОНТАКТЫ ---
@router.message(F.text == "📞 Контакты и локация")
async def show_contacts(message: Message):
    text = (
        "<b>📞 Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Краснодарский край, г. Анапа, ст. Благовещенская, б/о «Русалочка»\n"
        "📞 <b>Отдел бронирования:</b> +7 (918) 47-74-366\n"
        "💬 <b>Telegram:</b> @BAZU193\n"
        "✉️ <b>E-mail:</b> anaparusalochka@rambler.ru\n"
        "🌐 <b>Сайт:</b> https://rusalo4ka.com/\n\n"
        "📍 <i>Геолокация отправлена ниже:</i>"
    )
    await message.answer(text)
    await message.answer_location(latitude=GEO_LATITUDE, longitude=GEO_LONGITUDE)

# --- FAQ ---
@router.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def show_faq(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Время заезда и выезда", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="🐾 Можно ли с собаками?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="💳 Гарантия брони и оплата", callback_data="faq:payment")],
            [InlineKeyboardButton(text="📍 Как к вам добраться?", callback_data="faq:route")],
        ]
    )
    await message.answer("<b>Часто задаваемые вопросы (FAQ):</b>", reply_markup=kb)

@router.callback_query(F.data.startswith("faq:"))
async def faq_click(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    answers = {
        "checkin": (
            "<b>🕒 Время заезда и выезда:</b>\n\n"
            "• <b>Заезд:</b> с <b>13:00</b>\n"
            "• <b>Выезд:</b> до <b>11:00</b>"
        ),
        "pets": (
            "<b>🐾 Размещение с животными:</b>\n\n"
            "— Возможно исключительно с декоративными собаками до 6 кг в номерах категории «Номер с кухней (апарт.)» эко.\n"
            "— Тариф: 800 руб./сутки.\n"
            "— Выгул собак на территории базы ЗАПРЕЩЕН."
        ),
        "payment": (
            "<b>💳 Гарантия бронирования и оплата:</b>\n\n"
            "• Для подтверждения бронирования необходимо произвести оплату в размере <b>30.00% от общей стоимости</b>.\n"
            "• Оставшаяся сумма (70%) оплачивается при заселении.\n"
            "• Бесплатная отмена возможна за 14 дней до даты заезда."
        ),
        "route": "<b>📍 Адрес:</b> Краснодарский край, г. Анапа, станица Благовещенская, б/о «Русалочка»."
    }
    ans = answers.get(action, "Информация уточняется.")
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="faq_back_root")]]
    )
    await callback.message.edit_text(ans, reply_markup=back_kb)
    await callback.answer()

@router.callback_query(F.data == "faq_back_root")
async def faq_back_root(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Время заезда и выезда", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="🐾 Можно ли с собаками?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="💳 Гарантия брони и оплата", callback_data="faq:payment")],
            [InlineKeyboardButton(text="📍 Как к вам добраться?", callback_data="faq:route")],
        ]
    )
    await callback.message.edit_text("<b>Часто задаваемые вопросы (FAQ):</b>", reply_markup=kb)
    await callback.answer()

# =====================================================================
# 5. ПОШАГОВЫЙ СЦЕНАРИЙ БРОНИРОВАНИЯ
# =====================================================================

# 1. ЗАПРОС ДАТ
@router.message(F.text == "📝 Забронировать")
@router.callback_query(F.data == "start_booking_fsm")
async def fsm_step1_dates(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    prompt = (
        "📅 <b>Шаг 1 из 5: Выберите даты заезда и выезда</b>\n\n"
        "База отдыха принимает гостей в летний сезон <b>с 15 июня по 15 сентября</b>.\n"
        "🕒 <i>Заезд с 13:00, выезд до 11:00</i>\n\n"
        "Введите желаемые даты в формате: <b>ДД.ММ - ДД.ММ</b>\n"
        "<i>Например: 20.06 - 30.06 или 01.07 - 10.07</i>"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(prompt, reply_markup=get_cancel_reply_keyboard())
        await event.answer()
    else:
        await event.answer(prompt, reply_markup=get_cancel_reply_keyboard())

    await state.set_state(BookingFlow.waiting_dates)

@router.callback_query(F.data.startswith("book_room_target:"))
async def fsm_from_card(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)

    await state.update_data(preselected_room_key=room_key)
    prompt = (
        f"Вы выбрали: <b>{room['title']}</b>\n\n"
        "📅 <b>Шаг 1 из 5: Даты проживания</b>\n"
        "База работает <b>с 15 июня по 15 сентября</b> (заезд с 13:00, выезд до 11:00).\n\n"
        "Введите даты заезда и выезда (например: <b>01.07 - 10.07</b>):"
    )
    await callback.message.answer(prompt, reply_markup=get_cancel_reply_keyboard())
    await callback.answer()
    await state.set_state(BookingFlow.waiting_dates)

# 2. ОБРАБОТКА ДАТ И ПОКАЗ КАТЕГОРИЙ
@router.message(BookingFlow.waiting_dates, F.text)
async def fsm_step2_process_dates(message: Message, state: FSMContext):
    raw_dates = message.text.strip()
    is_valid, nights, date_in, date_out, full_dates_str = parse_dates(raw_dates)

    if not is_valid or nights <= 0:
        await message.answer(
            "⚠️ Пожалуйста, введите корректные даты заезда и выезда через дефис.\n"
            "<i>Пример: 15.06 - 25.06 или 05.07 - 12.07</i>"
        )
        return

    await state.update_data(
        nights=nights,
        date_in=date_in,
        date_out=date_out,
        full_dates_str=full_dates_str
    )

    data = await state.get_data()
    preselected = data.get("preselected_room_key")

    if preselected and preselected in ROOMS_CATALOG:
        room = ROOMS_CATALOG[preselected]
        await state.update_data(
            room_key=preselected,
            room_title=room["title"],
            price_per_night=room["price_per_night"],
            max_guests=room["max_guests"]
        )
        await message.answer(
            f"📅 <b>Заезд:</b> {date_in}\n"
            f"📅 <b>Выезд:</b> {date_out}\n"
            f"🌙 <b>Ночей:</b> {nights}\n"
            f"🏡 <b>Категория:</b> {room['title']}\n\n"
            f"👥 <b>Шаг 3 из 5: Количество гостей</b>\n"
            f"Вместимость номера: <b>до {room['max_guests']} человек</b>.\n"
            "Выберите количество гостей:",
            reply_markup=get_guests_keyboard(room["max_guests"])
        )
        await state.set_state(BookingFlow.waiting_guests)
    else:
        await message.answer(
            f"📅 <b>Период:</b> {full_dates_str} ({nights} ноч.)\n\n"
            "🏡 <b>Шаг 2 из 5: Выберите желаемую категорию номера:</b>",
            reply_markup=get_rooms_booking_keyboard()
        )
        await state.set_state(BookingFlow.choosing_room)

# ВЫБОР НОМЕРА ИЗ СПИСКА
@router.callback_query(BookingFlow.choosing_room, F.data.startswith("select_room_fsm:"))
async def fsm_step3_select_room(callback: CallbackQuery, state: FSMContext):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        await callback.answer("Ошибка выбора категории", show_alert=True)
        return

    await state.update_data(
        room_key=room_key,
        room_title=room["title"],
        price_per_night=room["price_per_night"],
        max_guests=room["max_guests"]
    )

    data = await state.get_data()
    nights = data.get("nights", 1)

    await callback.message.edit_text(
        f"Вы выбрали: <b>{room['title']}</b>\n"
        f"💰 Стоимость за сутки: <b>{room['price_per_night']} ₽</b>\n"
        f"🌙 Ночей: <b>{nights}</b>\n\n"
        f"👥 <b>Шаг 3 из 5: Выберите количество гостей</b> (максимум до {room['max_guests']} чел.):",
        reply_markup=get_guests_keyboard(room["max_guests"])
    )
    await state.set_state(BookingFlow.waiting_guests)
    await callback.answer()

# 3. ВЫБОР ГОСТЕЙ И РАСЧЕТ 30% ПРЕДОПЛАТЫ
@router.callback_query(BookingFlow.waiting_guests, F.data.startswith("set_guests_fsm:"))
async def fsm_step4_calc_summary(callback: CallbackQuery, state: FSMContext):
    guests_count = int(callback.data.split(":")[1])
    data = await state.get_data()

    room_title = data.get("room_title", "Номер")
    nights = data.get("nights", 1)
    price_per_night = data.get("price_per_night", 3500)
    date_in = data.get("date_in", "")
    date_out = data.get("date_out", "")

    total_price = nights * price_per_night
    prepayment_30 = round(total_price * 0.30)
    balance_70 = total_price - prepayment_30

    await state.update_data(
        guests_count=guests_count,
        total_price=total_price,
        prepayment=prepayment_30,
        balance=balance_70
    )

    await callback.message.delete()

    summary_text = (
        "📋 <b>ДЕТАЛИЗАЦИЯ И РАСЧЕТ СТОИМОСТИ</b>\n"
        "────────────────────────\n"
        f"🏡 <b>1 номер:</b> {room_title}\n"
        f"📥 <b>Заезд:</b> {date_in}\n"
        f"📤 <b>Выезд:</b> {date_out}\n"
        f"🌙 <b>Период:</b> {nights} ночей\n"
        f"👥 <b>Количество гостей:</b> {guests_count} чел.\n\n"
        f"💵 <b>Проживание ({nights} ноч.):</b> {total_price:,} ₽\n"
        "🍽 <b>Питание:</b> По выбору на месте\n"
        "────────────────────────\n"
        f"🧾 <b>ИТОГО К ОПЛАТЕ:</b> <b>{total_price:,} ₽</b>\n"
        f"💳 <b>Предоплата (30.00%):</b> <b>{prepayment_30:,} ₽</b>\n"
        f"🤝 <b>Остаток при заселении (70%):</b> {balance_70:,} ₽\n\n"
        "📌 <b>Тариф:</b> Акция «Сезонное предложение»\n"
        "🔒 <b>Гарантия бронирования:</b>\n"
        "<i>Для подтверждения бронирования необходимо произвести оплату в размере 30.00% от общей стоимости.</i>\n\n"
        "🛡 <b>Отмена бронирования:</b>\n"
        "<i>Бесплатная отмена бронирования возможна за 14 дней до даты заезда. При отмене менее чем за 14 дней взимается штраф в размере внесенной предоплаты.</i>"
    ).replace(",", " ")

    await callback.message.answer(summary_text, reply_markup=get_payment_decision_keyboard())
    await state.set_state(BookingFlow.confirm_price)
    await callback.answer()

# 4. НАЖАТИЕ «ОПЛАТИТЬ (ВНЕСТИ ПРЕДОПЛАТУ 30%)»
@router.callback_query(BookingFlow.confirm_price, F.data == "pay_prepayment_click")
async def fsm_step5_start_customer_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "👤 <b>Шаг 4 из 5: Данные заказчика</b>\n\n"
        "Укажите ваши <b>Имя и Фамилию</b> (как в паспорте для договора бронирования):",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingFlow.waiting_fullname)
    await callback.answer()

# 5. ИМЯ И ФАМИЛИЯ
@router.message(BookingFlow.waiting_fullname, F.text)
async def fsm_step5_name_received(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text.strip())
    await message.answer(
        "📱 <b>Шаг 5 из 5: Контактный телефон</b>\n\n"
        "Нажмите кнопку <b>«Отправить контакт»</b> ниже или введите номер вручную:",
        reply_markup=get_phone_reply_keyboard()
    )
    await state.set_state(BookingFlow.waiting_phone)

# 6. ТЕЛЕФОН
@router.message(BookingFlow.waiting_phone, F.contact | F.text)
async def fsm_step6_phone_received(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    await state.update_data(phone=phone)

    await message.answer(
        "✉️ <b>Укажите ваш E-mail:</b>\n"
        "На него будет отправлен ваучер бронирования и электронный чек.\n"
        "<i>(Или нажмите «Пропустить», если хотите получить подтверждение только в Telegram)</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(BookingFlow.waiting_email)

# 7. EMAIL
@router.message(BookingFlow.waiting_email, F.text)
async def fsm_step7_email_received(message: Message, state: FSMContext):
    email = message.text.strip()
    if email == "➡️ Пропустить":
        email = "Не указан"
    await state.update_data(email=email)

    await message.answer(
        "✍️ <b>Примечания и пожелания:</b>\n"
        "Укажите пожелания (детская кроватка, парковочное место, ориентировочное время прибытия).\n"
        "<i>Либо нажмите «Пропустить»:</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(BookingFlow.waiting_notes)

# 8. ФИНИШ: ПРИМЕЧАНИЯ, ПОДТВЕРЖДЕНИЕ И КАРТОЧКА АДМИНУ
@router.message(BookingFlow.waiting_notes, F.text)
async def fsm_step8_finish(message: Message, state: FSMContext, bot: Bot):
    notes = message.text.strip()
    if notes == "➡️ Пропустить":
        notes = "Без особых примечаний"

    data = await state.get_data()
    room_title = data.get("room_title", "Номер")
    nights = data.get("nights", 1)
    date_in = data.get("date_in", "")
    date_out = data.get("date_out", "")
    guests_count = data.get("guests_count", 1)
    total_price = data.get("total_price", 0)
    prepayment = data.get("prepayment", 0)
    balance = data.get("balance", 0)
    fullname = data.get("fullname", "Гость")
    phone = data.get("phone", "Не указан")
    email = data.get("email", "Не указан")

    order_id = datetime.now().strftime("%d%m-%H%M")

    # Сообщение клиенту
    client_response = (
        f"🎉 <b>Спасибо, {fullname}! Заявка №{order_id} оформлена!</b>\n\n"
        "📋 <b>Ваш расчет бронирования:</b>\n"
        f"• <b>Категория:</b> {room_title}\n"
        f"• <b>Заезд:</b> {date_in}\n"
        f"• <b>Выезд:</b> {date_out}\n"
        f"• <b>Гости:</b> {guests_count} чел. ({nights} ноч.)\n"
        f"• <b>Сумма бронирования:</b> {total_price:,} ₽\n"
        f"• <b>Предоплата (30%):</b> <b>{prepayment:,} ₽</b>\n"
        f"• <b>Остаток при заезде (70%):</b> {balance:,} ₽\n"
        f"• <b>Телефон:</b> {phone}\n"
        f"• <b>E-mail:</b> {email}\n"
        f"• <b>Примечания:</b> {notes}\n\n"
        "💳 <b>Оплата предоплаты:</b>\n"
        "Администратор базы отдыха сейчас свяжется с вами по телефону для подтверждения наличия мест "
        "и направит официальные реквизиты/ссылку для внесения 30% предоплаты."
    ).replace(",", " ")

    await message.answer(client_response, reply_markup=get_main_menu_keyboard())

    # Мгновенная заявка администратору в Telegram (ID: 5014057300)
    username = f"@{message.from_user.username}" if message.from_user.username else "нет @username"
    user_id = message.from_user.id

    admin_notification = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА БРОНИРОВАНИЕ (№{order_id})</b>\n\n"
        f"🏡 <b>Категория:</b> {room_title}\n"
        f"📥 <b>Заезд:</b> {date_in}\n"
        f"📤 <b>Выезд:</b> {date_out} ({nights} ноч.)\n"
        f"👥 <b>Гости:</b> {guests_count} чел.\n\n"
        f"💰 <b>Общая сумма:</b> <b>{total_price:,} ₽</b>\n"
        f"💳 <b>Предоплата 30%:</b> <b>{prepayment:,} ₽</b>\n"
        f"🤝 <b>Остаток (при заезде):</b> {balance:,} ₽\n\n"
        f"👤 <b>Заказчик:</b> {fullname}\n"
        f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
        f"✉️ <b>E-mail:</b> {email}\n"
        f"📝 <b>Примечания:</b> <i>{notes}</i>\n\n"
        f"📱 <b>Telegram:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"⏰ <b>Время заявки:</b> {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
    ).replace(",", " ")

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification)
        except Exception as e:
            logging.error(f"Не удалось доставить уведомление администратору {ADMIN_CHAT_ID}: {e}")

    await state.clear()

# =====================================================================
# 6. ТОЧКА ВХОДА
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
