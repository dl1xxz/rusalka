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
# 1. КОНФИГУРАЦИЯ И ДАННЫЕ С САЙТА RUSALO4KA.COM
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8698519060:AAFMCj3zZHAjxrANyC4al0pM-TAblht-s_M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5014057300"))

# Точные координаты базы отдыха «Русалочка» (Анапа, ст. Благовещенская)
GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

# Полный каталог 9 категорий номеров с сайта
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "details": (
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + раскладное доп. место\n"
            "• Индивидуальная кухня: плита, СВЧ, холодильник, посуда\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi\n"
            "• Индивидуальный санузел с душем\n"
            "• Терраса / веранда для отдыха\n"
            "• <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/c3c/600_400_1/c3c97d74db5e26b8cb7974531be32717.jpg",
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "details": (
            "<b>В номере:</b>\n"
            "• Двуспальная кровать, односпальная кровать + доп. место\n"
            "• Собственный кухонный модуль с варочной поверхностью, СВЧ и посудой\n"
            "• Сплит-система, плоский ТВ, холодильник\n"
            "• Санузел с душем\n"
            "• Личная зона отдыха на веранде\n"
            "• <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/d3c/600_400_1/d3c92df78508e92fba8933e146eb4a05.jpg",
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "details": (
            "<b>В эко-домике:</b>\n"
            "• Экологически чистый сруб из натурального дерева\n"
            "• Двуспальная кровать + кресло-кровать (доп. место)\n"
            "• Сплит-система, холодильник, чайник, телевизор\n"
            "• Собственный санузел с душем\n"
            "• Уютная веранда с летней мебелью на свежем воздухе\n"
            "• <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/e7a/600_400_1/e7a6d8feea4cb804da6c39a3f9e9cf24.jpg",
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "details": (
            "<b>В эко-домике:</b>\n"
            "• 2 раздельные комнаты из экологичного дерева\n"
            "• Спальные места: 3 основных + дополнительное место\n"
            "• Сплит-система, холодильник, чайник, ТВ\n"
            "• Санузел с душевой кабиной\n"
            "• Просторная деревянная веранда\n"
            "• <i>Бассейн включен в стоимость проживания бесплатно!</i>"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/f8d/600_400_1/f8dbb24b89ebc90539fbeceae47c87c9.jpg",
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "details": (
            "<b>В номере:</b>\n"
            "• Отдельный капитальный кирпичный домик (прохладно даже в жару)\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система / кондиционер, холодильник, ТВ\n"
            "• Индивидуальный санузел и душ\n"
            "• Беседка / веранда для отдыха рядом с домиком"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/b3b/600_400_1/b3b8dfa2e6fca78e1189c4908051a8eb.jpg",
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "details": (
            "<b>В номере:</b>\n"
            "• Отдельный уютный деревянный домик на 2 персоны\n"
            "• Двуспальная кровать или две раздельные кровати\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Собственный санузел с душем\n"
            "• Терраса со столом и стульями"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/a9f/600_400_1/a9fc2ce6fe7a77b81b8979c3f0b2fcf7.jpg",
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "details": (
            "<b>В номере:</b>\n"
            "• Спальные места: двуспальная кровать + доп. место\n"
            "• Сплит-система, телевизор, холодильник, электрочайник\n"
            "• Ванная комната с душем\n"
            "• Место отдыха перед номером"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/17a/600_400_1/17ae86be4efb702ec8c6cceee69a8bfe.jpg",
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный + доп.место",
        "details": (
            "<b>В номере:</b>\n"
            "• Размещение для 3 гостей + возможность доп. места\n"
            "• Сплит-система, ТВ, холодильник\n"
            "• Санузел с душем\n"
            "• Летняя зона отдыха на свежем воздухе"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/28a/600_400_1/28a47eb38cbf917c093498877bc9ec7e.jpg",
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "details": (
            "<b>В номере:</b>\n"
            "• Просторный семейный номер на 4 человека + доп. место\n"
            "• Сплит-система, холодильник, ТВ, чайник\n"
            "• Ванная комната с душем\n"
            "• Терраса для вечерних посиделок"
        ),
        "image_url": "https://rusalo4ka.com/upload/resize_cache/iblock/39b/600_400_1/39ba579fcbb6ae083d987d605177265a.jpg",
    },
}

# =====================================================================
# 2. FSM (МАШИНА СОСТОЯНИЙ)
# =====================================================================
class BookingState(StatesGroup):
    waiting_dates = State()        # Шаг 1: Даты
    choosing_room = State()        # Шаг 2: Категория номера
    waiting_guests = State()       # Шаг 3: Состав гостей
    waiting_name = State()         # Шаг 4: Имя
    waiting_phone = State()        # Шаг 5: Телефон

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
                InlineKeyboardButton(text="🛎 Забронировать", callback_data=f"book_from_card:{room_key}")
            ]
        ]
    )

def get_room_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура со всеми 9 номерами для шага выбора категории"""
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"select_room:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_fsm_inline")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_faq_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Время заезда и выезда", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="🐾 Можно ли с питомцами?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="💳 Оплата и бронирование", callback_data="faq:payment")],
            [InlineKeyboardButton(text="📍 Как к вам добраться?", callback_data="faq:route")],
        ]
    )

def get_faq_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="faq:back")]
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
        "Здесь вас ждет комфортный семейный отдых, чистейший морской воздух, собственный бассейн "
        "и благоустроенная зеленая территория!\n\n"
        "📅 <b>Обратите внимание:</b> база отдыха работает в курортный сезон <b>с 15 июня по 15 сентября</b>.\n\n"
        "Выберите нужный раздел в меню ниже ⬇️"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

@router.message(F.text == "❌ Отменить бронирование")
async def cancel_booking_text(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "cancel_fsm_inline")
async def cancel_fsm_inline_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Бронирование отменено.", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- РАЗДЕЛ: НАШИ НОМЕРА (ВСЕ 9 КАТЕГОРИЙ) ---
@router.message(F.text == "🏡 Наши номера")
async def show_rooms(message: Message):
    await message.answer("<b>Все категории номеров базы отдыха «Русалочка»:</b>")
    for key, room in ROOMS_CATALOG.items():
        caption = f"🏡 <b>{room['title']}</b>"
        try:
            await message.answer_photo(
                photo=room["image_url"],
                caption=caption,
                reply_markup=get_room_card_keyboard(key)
            )
        except Exception:
            # Fallback если Telegram временно недоступен к внешнему CDN
            await message.answer(
                text=f"{caption}\n\n{room['details']}",
                reply_markup=get_room_card_keyboard(key)
            )

@router.callback_query(F.data.startswith("room_info:"))
async def handle_room_info(callback: CallbackQuery):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        await callback.answer("Номер не найден.", show_alert=True)
        return

    text = f"<b>{room['title']}</b>\n\n{room['details']}"
    await callback.message.reply(text)
    await callback.answer()

# --- РАЗДЕЛ: БАССЕЙН (СЛОВО В СЛОВО С САЙТА) ---
@router.message(F.text == "🏊‍♂️ Бассейн")
async def show_pool(message: Message):
    pool_photo = "https://rusalo4ka.com/upload/resize_cache/iblock/785/800_600_1/7858c9735d6e066a33c2a3e5c942488a.jpg"
    caption = (
        "<b>🏊‍♂️ Самый большой бассейн в округе!</b>\n"
        "<i>Кристально чистая морская вода, безопасная зона для малышей и комфортные шезлонги для загара.</i>\n\n"
        "<b>Абонементы на посещение:</b>\n"
        "✅ <b>Для гостей, проживающих в номерах категории «Эко Домик» и «Номер с кухней (апарт.)», пользование бассейном:</b>\n"
        "👉 <b>БЕСПЛАТНО</b>\n\n"
        "Остальные гости могут приобрести доступ к бассейну за дополнительную плату в администрации:\n\n"
        "• <b>1 час:</b> Взрослый/Детский (с 4 лет) — <b>180 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n"
        "• <b>1 день:</b> Взрослый/Детский (с 4 лет) — <b>550 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n"
        "• <b>5 дней:</b> Взрослый/Детский (с 4 лет) — <b>1 950 ₽</b> | Дети (до 4 лет) — <b>Бесплатно</b>\n\n"
        "⚠️ <b>Внимание!</b> Дети до 14 лет могут посещать бассейн только в сопровождении взрослых."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛎 Забронировать отдых", callback_data="start_booking_now")]
        ]
    )
    try:
        await message.answer_photo(photo=pool_photo, caption=caption, reply_markup=kb)
    except Exception:
        await message.answer(caption, reply_markup=kb)

# --- РАЗДЕЛ: О БАЗЕ ---
@router.message(F.text == "🌴 О базе")
async def show_about(message: Message):
    about_text = (
        "<b>🌴 База отдыха «Русалочка»</b>\n\n"
        "<b>Рай для ваших детей и спокойный отдых для родителей!</b>\n"
        "Мы позиционируем себя как семейная база отдыха. Пока взрослые расслабляются, детям всегда есть чем заняться!\n\n"
        "• Закрытая, абсолютно безопасная зеленая территория\n"
        "• До моря и просторного песчаного пляжа — несколько минут прогулочным шагом\n"
        "• Бассейн с морской водой, игровые городки, детская анимация\n"
        "• Период работы: <b>с 15 июня по 15 сентября</b>\n\n"
        "Узнайте больше на нашем официальном сайте:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Перейти на сайт rusalo4ka.com", url="https://rusalo4ka.com/")]
        ]
    )
    await message.answer(about_text, reply_markup=kb)

# --- РАЗДЕЛ: ИНФРАСТРУКТУРА (СЛОВО В СЛОВО С САЙТА) ---
@router.message(F.text == "🎡 Инфраструктура и развлечения")
async def show_infrastructure(message: Message):
    infra_text = (
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
        "Прокат детских колясок (от 0 до 5 лет), детских и взрослых велосипедов/самокатов. "
        "Прачечная и гладильная комната. "
        "Зарядная станция для авто GB/T 7kwt (Цена 22₽/ 1 кВт.ч).\n\n"
        "☕ <b>Вкусные радости</b>\n"
        "Натуральный зерновой кофе, прохладительные напитки и вкусный шашлык, который приготовят прямо при вас."
    )
    await message.answer(infra_text)

# --- РАЗДЕЛ: FAQ ---
@router.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def show_faq(message: Message):
    await message.answer(
        "<b>Часто задаваемые вопросы (FAQ):</b>\nВыберите интересующий вопрос:",
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
            "Ранний заезд и поздний выезд согласовываются индивидуально при наличии возможности."
        ),
        "pets": (
            "<b>🐾 Размещение с животными:</b>\n\n"
            "— Возможность размещения исключительно с декоративными собаками, весом до 6 кг., предусмотрена в номерах категории «Номер с кухней (апарт.)» эко.\n"
            "— Тариф на размещение: 800 руб./сутки.\n"
            "— Выгул собак на территории Базы отдыха «Русалочка» ЗАПРЕЩЕН."
        ),
        "payment": (
            "<b>💳 Оплата и бронирование:</b>\n\n"
            "• Для фиксации брони вносится предоплата в размере одних суток проживания.\n"
            "• Оставшаяся сумма оплачивается при заселении.\n"
            "• При отмене брони более чем за 14 дней до заезда предоплата возвращается."
        ),
        "route": (
            "<b>📍 Как к нам добраться:</b>\n\n"
            "Краснодарский край, г. Анапа, ст. Благовещенская, база отдыха «Русалочка».\n"
            "Удобный подъезд на автомобиле, есть парковка и зарядка для электрокаров. "
            "Точную точку на карте можно открыть в разделе «Контакты и локация»."
        )
    }

    if action == "back":
        await callback.message.edit_text(
            "<b>Часто задаваемые вопросы (FAQ):</b>\nВыберите интересующий вопрос:",
            reply_markup=get_faq_inline_keyboard()
        )
    else:
        await callback.message.edit_text(
            faq_answers.get(action, "Информация уточняется."),
            reply_markup=get_faq_back_keyboard()
        )
    await callback.answer()

# --- РАЗДЕЛ: КОНТАКТЫ ---
@router.message(F.text == "📞 Контакты и локация")
async def show_contacts(message: Message):
    contacts_text = (
        "<b>📞 Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Краснодарский край, Анапа, ст. Благовещенская, б/о «Русалочка»\n"
        "🌐 <b>Сайт:</b> https://rusalo4ka.com/\n"
        "💬 <b>Менеджер в Telegram:</b> @BAZU193\n\n"
        "📍 <i>Ниже отправлена геолокация для Яндекс.Карт и навигатора:</i>"
    )
    await message.answer(contacts_text)
    await message.answer_location(latitude=GEO_LATITUDE, longitude=GEO_LONGITUDE)

# =====================================================================
# 5. ПОШАГОВЫЙ СЦЕНАРИЙ БРОНИРОВАНИЯ (FSM)
# СНАЧАЛА ДАТЫ (15 ИЮНЯ - 15 СЕНТЯБРЯ), ЗАТЕМ НОМЕР И КОНТАКТЫ
# =====================================================================
@router.message(F.text == "📝 Забронировать")
@router.callback_query(F.data == "start_booking_now")
async def start_booking_step1(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    prompt_text = (
        "📅 <b>Шаг 1 из 5: Желаемые даты отдыха</b>\n\n"
        "⚠️ <i>Обратите внимание: база отдыха работает исключительно в летний сезон <b>с 15 июня по 15 сентября</b>.</i>\n\n"
        "Пожалуйста, введите дату заезда и выезда в формате: <b>ДД.ММ - ДД.ММ</b>\n"
        "<i>Например: 20.06 - 30.06 или 05.07 - 15.07</i>"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(prompt_text, reply_markup=get_cancel_reply_keyboard())
        await event.answer()
    else:
        await event.answer(prompt_text, reply_markup=get_cancel_reply_keyboard())

    await state.set_state(BookingState.waiting_dates)

@router.callback_query(F.data.startswith("book_from_card:"))
async def start_booking_from_card(callback: CallbackQuery, state: FSMContext):
    """Если нажали 'Забронировать' прямо под карточкой конкретного номера"""
    await state.clear()
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    room_name = room["title"] if room else "Выбранный номер"
    
    # Запоминаем номер заранее, но сначала спрашиваем даты!
    await state.update_data(preselected_room=room_name)

    prompt_text = (
        f"Вы выбрали: <b>{room_name}</b>\n\n"
        "📅 <b>Шаг 1 из 5: Желаемые даты отдыха</b>\n"
        "⚠️ <i>База отдыха работает <b>с 15 июня по 15 сентября</b>.</i>\n\n"
        "Введите даты заезда и выезда (например: <b>01.07 - 10.07</b>):"
    )
    await callback.message.answer(prompt_text, reply_markup=get_cancel_reply_keyboard())
    await callback.answer()
    await state.set_state(BookingState.waiting_dates)

@router.message(BookingState.waiting_dates, F.text)
async def process_dates(message: Message, state: FSMContext):
    dates_text = message.text.strip()
    await state.update_data(dates=dates_text)

    data = await state.get_data()
    preselected = data.get("preselected_room")

    if preselected:
        # Если номер был выбран из карточки, подтверждаем его и переходим к гостям
        await state.update_data(room_name=preselected)
        await message.answer(
            f"Даты приняты: <b>{dates_text}</b>\nНомер: <b>{preselected}</b>\n\n"
            "<b>Шаг 3 из 5: Состав гостей</b>\n"
            "Укажите количество взрослых и детей (например: <i>2 взрослых + 1 ребенок 5 лет</i>):",
            reply_markup=get_cancel_reply_keyboard()
        )
        await state.set_state(BookingState.waiting_guests)
    else:
        # Если начали через кнопку «Забронировать», предлагаем выбрать из 9 номеров
        await message.answer(
            f"Даты заезда и выезда: <b>{dates_text}</b>\n\n"
            "🏡 <b>Шаг 2 из 5: Выберите категорию номера:</b>",
            reply_markup=get_room_selection_keyboard()
        )
        await state.set_state(BookingState.choosing_room)

@router.callback_query(BookingState.choosing_room, F.data.startswith("select_room:"))
async def process_room_choice(callback: CallbackQuery, state: FSMContext):
    room_key = callback.data.split(":")[1]
    room = ROOMS_CATALOG.get(room_key)
    room_title = room["title"] if room else "Категория выбрана"

    await state.update_data(room_name=room_title)
    await callback.message.edit_text(f"Выбран номер: <b>{room_title}</b>")
    await callback.message.answer(
        "<b>Шаг 3 из 5: Состав гостей</b>\n"
        "Сколько человек планирует отдыхать?\n"
        "<i>(Укажите количество взрослых и возраст детей, например: 2 взрослых + ребенок 7 лет)</i>",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_guests)
    await callback.answer()

@router.message(BookingState.waiting_guests, F.text)
async def process_guests(message: Message, state: FSMContext):
    await state.update_data(guests=message.text.strip())
    await message.answer(
        "<b>Шаг 4 из 5: Контактное лицо</b>\n"
        "Как к вам обращаться? Напишите ваше Имя и Фамилию:",
        reply_markup=get_cancel_reply_keyboard()
    )
    await state.set_state(BookingState.waiting_name)

@router.message(BookingState.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "<b>Шаг 5 из 5: Телефон для связи</b>\n"
        "Укажите ваш номер телефона. Можно нажать кнопку «Отправить контакт» или написать вручную:",
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

    order_id = datetime.now().strftime("%d%m-%H%M")

    # Сообщение гостю
    user_confirm_text = (
        f"🎉 <b>Спасибо, {guest_name}!</b>\n\n"
        f"Ваша заявка на предварительную бронь <b>№{order_id}</b> успешно принята.\n\n"
        "📋 <b>Детали бронирования:</b>\n"
        f"• <b>Период:</b> {dates}\n"
        f"• <b>Категория номера:</b> {room_name}\n"
        f"• <b>Состав гостей:</b> {guests}\n"
        f"• <b>Телефон:</b> {phone}\n\n"
        "Администратор базы свяжется с вами в течение рабочего времени для подтверждения доступности и бронирования!"
    )
    await message.answer(user_confirm_text, reply_markup=get_main_menu_keyboard())

    # Мгновенная карточка администратору в Telegram (ID: 5014057300)
    username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
    user_id = message.from_user.id

    admin_notification = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА БРОНЬ (№{order_id})</b>\n\n"
        f"📅 <b>Даты:</b> {dates}\n"
        f"🏡 <b>Категория:</b> {room_name}\n"
        f"👨‍👩‍👧‍👦 <b>Гости:</b> {guests}\n"
        f"👤 <b>Имя:</b> {guest_name}\n"
        f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
        f"💬 <b>Telegram:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"⏰ <b>Отправлено:</b> {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
    )

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification)
        except Exception as e:
            logging.error(f"Не удалось доставить уведомление администратору {ADMIN_CHAT_ID}: {e}")

    await state.clear()

# =====================================================================
# 6. ЗАПУСК
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
