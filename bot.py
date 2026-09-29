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
# 1. КОНФИГУРАЦИЯ
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8698519060:AAFMCj3zZHAjxrANyC4al0pM-TAblht-s_M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5014057300"))

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

# Каталог номеров: фото из раздела сайта rusalo4ka.com, лимиты гостей и описание
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "max_guests": 3,
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 2-х местный + доп.место</b>\n\n"
            "Уютный семейный апартамент с индивидуальной кухонной зоной.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место (кресло-кровать / диван)\n"
            "• Кухня: плита, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi\n"
            "• Санузел с душевой кабиной\n"
            "• Индивидуальная веранда/балкон\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/c3c/600_400_1/c3c97d74db5e26b8cb7974531be32717.jpg",
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "max_guests": 4,
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 3-х местный + доп.место</b>\n\n"
            "Просторный апартамент для большой семьи.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать, 1-спальная кровать + доп. место\n"
            "• Полный кухонный блок: варочная панель, СВЧ, холодильник, посуда\n"
            "• Сплит-система, спутниковое ТВ, Wi-Fi\n"
            "• Ванная комната с душем\n"
            "• Летняя зона отдыха на веранде\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/d3c/600_400_1/d3c92df78508e92fba8933e146eb4a05.jpg",
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "max_guests": 3,
        "description": (
            "🏡 <b>Эко-домик 1-комнатный 2-х местный + доп.место</b>\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "<b>В домике:</b>\n"
            "• Двуспальная кровать + кресло-кровать (доп. место)\n"
            "• Сплит-система, холодильник, электрочайник, телевизор\n"
            "• Санузел с душем\n"
            "• Собственная терраса с садовой мебелью\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/e7a/600_400_1/e7a6d8feea4cb804da6c39a3f9e9cf24.jpg",
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "max_guests": 4,
        "description": (
            "🏡 <b>Эко-домик 2-комнатный 3-х местный + доп.место</b>\n\n"
            "Двухкомнатный коттедж из бруса для комфортного размещения до 4 гостей.\n\n"
            "<b>В домике:</b>\n"
            "• 2 изолированные спальные комнаты\n"
            "• 3 основных спальных места + доп. место\n"
            "• Сплит-система, холодильник, ТВ, чайник\n"
            "• Санузел с душевой кабиной\n"
            "• Просторная веранда\n"
            "🏊‍♂️ <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/f8d/600_400_1/f8dbb24b89ebc90539fbeceae47c87c9.jpg",
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "max_guests": 3,
        "description": (
            "🏡 <b>СТАНДАРТ кирпичный домик 3-х местный</b>\n\n"
            "Капитальный прохладный домик для комфортного отдыха 3 человек.\n\n"
            "<b>В домике:</b>\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, телевизор\n"
            "• Собственный санузел с душем\n"
            "• Индивидуальная веранда/столик перед входом"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/b3b/600_400_1/b3b8dfa2e6fca78e1189c4908051a8eb.jpg",
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "max_guests": 2,
        "description": (
            "🏡 <b>СТАНДАРТ Деревянный домик 2-х местный</b>\n\n"
            "Уютный деревянный домик для двоих среди зелени и роз.\n\n"
            "<b>В домике:</b>\n"
            "• Двуспальная кровать или две 1-спальные кровати\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Открытая терраса со столиком"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/a9f/600_400_1/a9fc2ce6fe7a77b81b8979c3f0b2fcf7.jpg",
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "max_guests": 3,
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный + доп.место</b>\n\n"
            "Классический уютный номер категории стандарт.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, ТВ, холодильник, чайник\n"
            "• Санузел и душевая\n"
            "• Терраса для отдыха"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/17a/600_400_1/17ae86be4efb702ec8c6cceee69a8bfe.jpg",
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный + доп.место",
        "max_guests": 4,
        "description": (
            "🏡 <b>СТАНДАРТ 3-х местный + доп.место</b>\n\n"
            "Вместительный 3-местный номер с дополнительным местом.\n\n"
            "<b>В номере:</b>\n"
            "• 3 основных спальных места + евро-раскладушка/кресло\n"
            "• Кондиционер, холодильник, телевизор\n"
            "• Санузел с душем\n"
            "• Зона отдыха на веранде"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/28a/600_400_1/28a47eb38cbf917c093498877bc9ec7e.jpg",
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "max_guests": 5,
        "description": (
            "🏡 <b>СТАНДАРТ 4-х местный + доп.место</b>\n\n"
            "Большой просторный номер для дружной компании или семьи с детьми.\n\n"
            "<b>В номере:</b>\n"
            "• Спальные места: 4 основных + 1 дополнительное место\n"
            "• Сплит-система, холодильник, ТВ, чайник\n"
            "• Санузел с душем\n"
            "• Веранда со столом и стульями"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/39b/600_400_1/39ba579fcbb6ae083d987d605177265a.jpg",
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
    waiting_comment = State()

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
        [KeyboardButton(text="📱 Отправить свой контакт", request_contact=True)],
        [KeyboardButton(text="❌ Отменить бронирование")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_skip_comment_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="➡️ Пропустить")],
        [KeyboardButton(text="❌ Отменить бронирование")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_rooms_list_keyboard() -> InlineKeyboardMarkup:
    """Список категорий для меню «Наши номера»"""
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"view_room:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_single_room_keyboard(room_key: str) -> InlineKeyboardMarkup:
    """Кнопки под конкретным номером"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛎 Забронировать этот номер", callback_data=f"book_target:{room_key}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку категорий", callback_data="back_to_rooms_list")]
        ]
    )

def get_guests_inline_keyboard(max_guests: int) -> InlineKeyboardMarkup:
    """Кнопки выбора количества человек под конкретную категорию"""
    buttons = [
        InlineKeyboardButton(text=f"👤 {i} чел.", callback_data=f"guests_count:{i}")
        for i in range(1, max_guests + 1)
    ]
    # Разбиваем по 2-3 кнопки в ряд
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_faq_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Время заезда и выезда", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="🐾 Можно ли с питомцами?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="💳 Оплата и бронирование", callback_data="faq:payment")],
            [InlineKeyboardButton(text="📍 Как к вам добраться?", callback_data="faq:route")],
        ]
    )

# =====================================================================
# 4. ОБРАБОТЧИКИ
# =====================================================================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "<b>Добро пожаловать в базу отдыха «Русалочка»! 🌊</b>\n\n"
        "Семейный отдых на Черноморском побережье (Анапа, ст. Благовещенская).\n"
        "Чистое море, большой бассейн, уютные эко-домики и номера с личной кухней!\n\n"
        "📅 <b>Сезон работы базы: с 15 июня по 15 сентября</b>\n\n"
        "Выберите раздел в меню ниже ⬇️"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())

@router.message(F.text == "❌ Отменить бронирование")
async def cancel_booking(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())

# --- РАЗДЕЛ: НАШИ НОМЕРА (СПИСОК И КАРТОЧКИ С ФОТО) ---
@router.message(F.text == "🏡 Наши номера")
async def show_rooms_menu(message: Message):
    text = (
        "<b>🏡 Категории номеров базы отдыха «Русалочка»:</b>\n\n"
        "Нажмите на интересующую категорию, чтобы посмотреть реальные фотографии, "
        "оснащение и стоимость:"
    )
    await message.answer(text, reply_markup=get_rooms_list_keyboard())

@router.callback_query(F.data == "back_to_rooms_list")
async def back_to_rooms_list_handler(callback: CallbackQuery):
    await callback.message.delete()
    text = (
        "<b>🏡 Категории номеров базы отдыха «Русалочка»:</b>\n\n"
        "Нажмите на категорию для просмотра фотографий и описания:"
    )
    await callback.message.answer(text, reply_markup=get_rooms_list_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("view_room:"))
async def view_room_handler(callback: CallbackQuery):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    await callback.message.delete()
    try:
        await callback.message.answer_photo(
            photo=room["image_url"],
            caption=f"{room['description']}\n\n👥 <b>Максимальная вместимость:</b> до {room['max_guests']} человек",
            reply_markup=get_single_room_keyboard(room_key)
        )
    except Exception:
        await callback.message.answer(
            text=f"{room['description']}\n\n👥 <b>Максимальная вместимость:</b> до {room['max_guests']} человек",
            reply_markup=get_single_room_keyboard(room_key)
        )
    await callback.answer()

# --- ОТЗЫВЫ ---
@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    reviews_url = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⭐ Читать отзывы на Яндекс.Картах", url=reviews_url)]]
    )
    await message.answer(
        "<b>⭐ Отзывы наших гостей:</b>\n\n"
        "Вы можете прочитать честные оценки, отзывы и фотографии отдыхающих "
        "на официальной странице базы на Яндекс.Картах:",
        reply_markup=kb
    )

# --- БАССЕЙН (СЛОВО В СЛОВО С САЙТА) ---
@router.message(F.text == "🏊‍♂️ Бассейн")
async def show_pool(message: Message):
    pool_photo = "https://rusalo4ka.com/upload/resize_cache/iblock/785/800_600_1/7858c9735d6e066a33c2a3e5c942488a.jpg"
    caption = (
        "<b>🏊‍♂️️ Самый большой бассейн в округе!</b>\n"
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
        inline_keyboard=[[InlineKeyboardButton(text="🛎 Забронировать отдых", callback_data="start_booking_general")]]
    )
    try:
        await message.answer_photo(photo=pool_photo, caption=caption, reply_markup=kb)
    except Exception:
        await message.answer(caption, reply_markup=kb)

# --- ИНФРАСТРУКТУРА (СЛОВО В СЛОВО С САЙТА) ---
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
        "• Закрытая охраняемая территория\n"
        "• Просторный пляж и теплое море в пешей доступности\n"
        "• Бассейн с чистой морской водой\n"
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
        "📞 <b>Администратор (Звонки):</b> 8 (918) 47-74-366\n"
        "💬 <b>Telegram администратора:</b> @BAZU193\n"
        "✉️ <b>E-mail:</b> anaparusalochka@rambler.ru\n"
        "🌐 <b>Сайт:</b> https://rusalo4ka.com/\n\n"
        "📍 <i>Геолокация отправлена ниже:</i>"
    )
    await message.answer(text)
    await message.answer_location(latitude=GEO_LATITUDE, longitude=GEO_LONGITUDE)

# --- FAQ ---
@router.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def show_faq(message: Message):
    await message.answer("<b>Часто задаваемые вопросы (FAQ):</b>", reply_markup=get_faq_inline_keyboard())

@router.callback_query(F.data.startswith("faq:"))
async def faq_callback_handler(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    answers = {
        "checkin": "🕒 <b>Время заезда и выезда:</b>\n\n• Заезд — с <b>14:00</b>\n• Выезд — до <b>12:00</b>",
        "pets": (
            "🐾 <b>Размещение с собаками:</b>\n\n"
            "— Возможно исключительно с декоративными собаками до 6 кг в номерах «Номер с кухней (апарт.)» эко.\n"
            "— Тариф: 800 руб./сутки.\n"
            "— Выгул собак на территории базы ЗАПРЕЩЕН."
        ),
        "payment": "💳 <b>Оплата:</b>\n\nПредоплата в размере 1 суток проживания при бронировании. Остаток — при заселении.",
        "route": "📍 <b>Адрес:</b> Краснодарский край, Анапа, станица Благовещенская, б/о «Русалочка»."
    }
    ans = answers.get(action, "Информация уточняется.")
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="faq_back")]]
    )
    await callback.message.edit_text(ans, reply_markup=back_kb)
    await callback.answer()

@router.callback_query(F.data == "faq_back")
async def faq_back_handler(callback: CallbackQuery):
    await callback.message.edit_text("<b>Часто задаваемые вопросы (FAQ):</b>", reply_markup=get_faq_inline_keyboard())
    await callback.answer()

# =====================================================================
# 5. ПОШАГОВОЕ БРОНИРОВАНИЕ (С ВАЛИДАЦИЕЙ ГОСТЕЙ, ДАТ И КОММЕНТАРИЕМ)
# =====================================================================

# Точка входа 1: из кнопки «Забронировать» общего меню
@router.message(F.text == "📝 Забронировать")
@router.callback_query(F.data == "start_booking_general")
async def booking_start_choose_room(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "<b>Шаг 1 из 6: Выбор категории номера</b>\n\n"
        "Выберите категорию, которую хотите забронировать:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"book_target:{key}")]
            for key, data in ROOMS_CATALOG.items()
        ]
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)
    await state.set_state(BookingState.choosing_room)

# Точка входа 2: из конкретной карточки номера («Забронировать этот номер»)
@router.callback_query(F.data.startswith("book_target:"))
async def booking_start_from_specific_room(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)

    await state.update_data(
        room_key=room_key,
        room_name=room["title"],
        max_guests=room["max_guests"]
    )

    text = (
        f"Вы выбрали: <b>{room['title']}</b>\n\n"
        "📅 <b>Шаг 2 из 6: Даты заезда и выезда</b>\n"
        "⚠️ <i>Напоминаем: база отдыха открыта в курортный сезон <b>с 15 июня по 15 сентября</b>.</i>\n\n"
        "Укажите даты отдыха (например: <b>20.06 - 30.06</b> или <b>10.07 - 20.07</b>):"
    )
    await callback.message.answer(text, reply_markup=get_cancel_reply_keyboard())
    await callback.answer()
    await state.set_state(BookingState.waiting_dates)

# Шаг: Ввод дат
@router.message(BookingState.waiting_dates, F.text)
async def booking_dates_handler(message: Message, state: FSMContext):
    dates_text = message.text.strip()
    await state.update_data(dates=dates_text)

    data = await state.get_data()
    max_guests = data.get("max_guests", 4)
    room_name = data.get("room_name", "Выбранный номер")

    text = (
        f"📅 Даты: <b>{dates_text}</b>\n"
        f"🏡 Категория: <b>{room_name}</b>\n\n"
        f"👥 <b>Шаг 3 из 6: Количество гостей</b>\n"
        f"Для данной категории максимальная вместимость — <b>до {max_guests} человек</b>.\n"
        "Выберите количество гостей кнопкой ниже или укажите текстом:"
    )
    await message.answer(text, reply_markup=get_guests_inline_keyboard(max_guests))
    await state.set_state(BookingState.waiting_guests)

# Шаг: Выбор гостей (кнопкой или текстом)
@router.callback_query(BookingState.waiting_guests, F.data.startswith("guests_count:"))
async def booking_guests_callback(callback: CallbackQuery, state: FSMContext):
    count = callback.data.split(":")[1]
    await state.update_data(guests=f"{count} чел.")
    await callback.message.delete()
    await callback.message.answer(
        f"Количество гостей: <b>{count} чел.</b>\n\n"
        "👤 <b>Шаг 4 из 6: Ваше имя</b>\n"
        "Как к вам обращаться? (Имя и Фамилия):",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_name)
    await callback.answer()

@router.message(BookingState.waiting_guests, F.text)
async def booking_guests_text(message: Message, state: FSMContext):
    data = await state.get_data()
    max_guests = data.get("max_guests", 4)

    # Проверка, если введено просто число
    try:
        num = int(''.join(filter(str.isdigit, message.text)))
        if num > max_guests:
            await message.answer(
                f"⚠️ Для этой категории максимальное количество человек — <b>{max_guests}</b>.\n"
                f"Пожалуйста, выберите число до {max_guests} или выберите другую категорию через меню."
            )
            return
    except Exception:
        pass

    await state.update_data(guests=message.text.strip())
    await message.answer(
        "👤 <b>Шаг 4 из 6: Ваше имя</b>\n"
        "Как к вам обращаться? (Имя и Фамилия):",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_name)

# Шаг: Имя
@router.message(BookingState.waiting_name, F.text)
async def booking_name_handler(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await message.answer(
        "📱 <b>Шаг 5 из 6: Контактный телефон</b>\n"
        "Нажмите кнопку «Отправить свой контакт» или напишите номер вручную:",
        reply_markup=get_phone_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_phone)

# Шаг: Телефон
@router.message(BookingState.waiting_phone, F.contact | F.text)
async def booking_phone_handler(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    await state.update_data(phone=phone)

    await message.answer(
        "✍️ <b>Шаг 6 из 6: Комментарий или пожелания</b>\n"
        "Напишите ваши пожелания (например: <i>нужна детская кроватка, время приезда в 16:00, парковочное место</i>).\n\n"
        "Если пожеланий нет — нажмите <b>«Пропустить»</b>:",
        reply_markup=get_skip_comment_keyboard()
    )
    await state.set_state(BookingState.waiting_comment)

# Шаг: Комментарий и отправка заявки
@router.message(BookingState.waiting_comment, F.text)
async def booking_finish(message: Message, state: FSMContext, bot: Bot):
    user_comment = message.text.strip()
    if user_comment == "➡️ Пропустить":
        user_comment = "Без комментариев"

    data = await state.get_data()
    room_name = data.get("room_name", "Не указан")
    dates = data.get("dates", "Не указаны")
    guests = data.get("guests", "Не указано")
    guest_name = data.get("guest_name", "Гость")
    phone = data.get("phone", "Не указан")

    order_id = datetime.now().strftime("%d%m-%H%M")

    # 1. Ответ клиенту
    guest_confirmation = (
        f"🎉 <b>Спасибо, {guest_name}! Заявка №{order_id} принята!</b>\n\n"
        "📋 <b>Данные бронирования:</b>\n"
        f"• <b>Категория:</b> {room_name}\n"
        f"• <b>Даты:</b> {dates}\n"
        f"• <b>Гости:</b> {guests}\n"
        f"• <b>Телефон:</b> {phone}\n"
        f"• <b>Комментарий:</b> {user_comment}\n\n"
        "Администратор свяжется с вами по указанному телефону для подтверждения наличия мест и внесения предоплаты!"
    )
    await message.answer(guest_confirmation, reply_markup=get_main_menu_keyboard())

    # 2. Мгновенное уведомление администратору (ID: 5014057300)
    username = f"@{message.from_user.username}" if message.from_user.username else "нет @username"
    user_id = message.from_user.id

    admin_notification = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА БРОНЬ (№{order_id})</b>\n\n"
        f"🏡 <b>Категория:</b> {room_name}\n"
        f"📅 <b>Даты отдыха:</b> {dates}\n"
        f"👥 <b>Гости:</b> {guests}\n"
        f"👤 <b>Имя:</b> {guest_name}\n"
        f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
        f"💬 <b>Комментарий:</b> <i>{user_comment}</i>\n\n"
        f"📱 <b>Telegram:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"⏰ <b>Время заявки:</b> {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
    )

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification)
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления в админ-чат {ADMIN_CHAT_ID}: {e}")

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
