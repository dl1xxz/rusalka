import os
import re
import json
import logging
from typing import Dict, Any, List

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    InputMediaPhoto,
)
from dotenv import load_dotenv

# =====================================================================
# 1. КОНФИГУРАЦИЯ
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не задан! Добавьте BOT_TOKEN в переменные окружения."
    )

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
BOT_VERSION = "RUSALOCHKA_TG_2026_V4"

# Замена внешней ссылки на официальный сайт
BOOKING_URL = "https://rusalo4ka.com/"

REVIEWS_YANDEX_URL = (
    "https://yandex.ru/maps/org/rusalochka/241387417775/"
    "reviews/?ll=37.156738%2C45.028213&z=11.94"
)
REVIEWS_2GIS_URL = "https://2gis.ru/anapa/firm/70000001033010188"
YANDEX_ROUTE_URL = (
    "https://yandex.ru/maps/org/rusalochka/241387417775"
    "?si=5zprzpwhdg2vqk8wegq6b3krmr"
)

RULES_FILE_PATH = "rules.pdf"
OFERTA_FILE_PATH = "oferta.pdf"
STATS_FILE = "booking_stats_tg.json"


# =====================================================================
# 2. СЧЕТЧИК ПЕРЕХОДОВ К БРОНИРОВАНИЮ
# =====================================================================
def increment_booking_clicks(user_id: int) -> int:
    data = {"total_clicks": 0, "users": {}}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    data["total_clicks"] = data.get("total_clicks", 0) + 1
    u_key = str(user_id)
    data["users"][u_key] = data.get("users", {}).get(u_key, 0) + 1

    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения статистики Telegram: {e}")

    return data["total_clicks"]


def get_booking_stats() -> dict:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_clicks": 0, "users": {}}


# =====================================================================
# 3. FSM СОСТОЯНИЯ
# =====================================================================
class SupportStates(StatesGroup):
    waiting_for_question = State()


# =====================================================================
# 4. НОМЕРНОЙ ФОНД (Цены: июнь 2026)
# =====================================================================
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "folder": "kitchen_2p",
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 2-х местный + доп.место</b>\n\n"
            "Уютный семейный апартамент повышенной комфортности с индивидуальной кухней.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место (диван / кресло-кровать)\n"
            "• Кухня: плита, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi, санузел с душем\n"
            "• Индивидуальная веранда/балкон\n\n"
            "👥 <b>Вместимость:</b> 2 осн. места + доп. место\n"
            "💰 <b>Июнь (Все включено с 3-раз. питанием):</b> от 10 500 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 9 300 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "folder": "kitchen_3p",
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 3-х местный + доп.место</b>\n\n"
            "Просторный апартамент для комфортного отдыха всей семьей.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать, 1-спальная кровать + доп. место\n"
            "• Кухонный модуль: варочная панель, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ТВ, Wi-Fi, санузел с душем, веранда\n\n"
            "👥 <b>Вместимость:</b> 3 осн. места + доп. место\n"
            "💰 <b>Июнь (Все включено с 3-раз. питанием):</b> от 15 500 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 13 700 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "folder": "eco_1k_2p",
        "description": (
            "🏡 <b>Эко-домик 1-комнатный 2-х местный + доп.место</b>\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "<b>В домике:</b>\n"
            "• Двуспальная кровать + кресло-кровать\n"
            "• Сплит-система, холодильник, чайник, ТВ, санузел с душем\n"
            "• Терраса на свежем воздухе\n\n"
            "👥 <b>Вместимость:</b> 2 осн. места + доп. место\n"
            "💰 <b>Июнь (Все включено с 3-раз. питанием):</b> от 9 690 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 8 490 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "folder": "eco_2k_3p",
        "description": (
            "🏡 <b>Эко-домик 2-комнатный 3-х местный + доп.место</b>\n\n"
            "Двухкомнатный коттедж из бруса для большой семьи.\n\n"
            "<b>В домике:</b>\n"
            "• 2 спальные комнаты (3 осн. места + евро-раскладушка)\n"
            "• Кондиционер, холодильник, ТВ, чайник, санузел с душем\n"
            "• Просторная деревянная терраса\n\n"
            "👥 <b>Вместимость:</b> 3 осн. места + доп. место\n"
            "💰 <b>Июнь (Все включено с 3-раз. питанием):</b> от 14 390 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 12 590 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "folder": "std_brick_3p",
        "description": (
            "🏡 <b>СТАНДАРТ кирпичный домик 3-х местный</b>\n\n"
            "Капитальный прохладный домик для семьи или компании.\n\n"
            "<b>В домике:</b>\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 <b>Вместимость:</b> 3 осн. места\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 9 890 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 8 090 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "folder": "std_wood_2p",
        "description": (
            "🏡 <b>СТАНДАРТ Деревянный домик 2-х местный</b>\n\n"
            "Уютный деревянный домик для двоих в зелёной зоне.\n\n"
            "<b>В домике:</b>\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ, санузел с душем, терраса\n\n"
            "👥 <b>Вместимость:</b> 2 осн. места\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 6 590 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 5 390 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный",
        "folder": "std_2p",
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный</b>\n\n"
            "Классический номер для 2 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать, кондиционер, ТВ, холодильник, санузел\n\n"
            "👥 <b>Вместимость:</b> 2 осн. места\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 6 390 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 5 190 ₽ / сутки"
        ),
    },
    "std_2p_extra": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "folder": "std_2p_extra",
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный + доп.место</b>\n\n"
            "Номер категории стандарт для семьи до 3 человек.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, ТВ, холодильник, санузел с душем, терраса\n\n"
            "👥 <b>Вместимость:</b> 2 осн. места + доп. место\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 6 390 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 5 190 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный",
        "folder": "std_3p",
        "description": (
            "🏡 <b>СТАНДАРТ 3-х местный</b>\n\n"
            "Просторный 3-местный номер стандартной категории.\n\n"
            "<b>В номере:</b>\n"
            "• 3 основных спальных места\n"
            "• Кондиционер, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 <b>Вместимость:</b> 3 осн. места\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 8 990 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 7 190 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "folder": "std_4p",
        "description": (
            "🏡 <b>СТАНДАРТ 4-х местный + доп.место</b>\n\n"
            "Семейный просторный номер на 4–5 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• 4 основных спальных места + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 <b>Вместимость:</b> 4 осн. места + доп. место\n"
            "💰 <b>Июнь (Полный пансион с 3-раз. питанием):</b> от 11 500 ₽ / сутки\n"
            "💰 <b>Июнь (Без питания):</b> от 9 100 ₽ / сутки\n"
            "➕ <b>Доп. место:</b> 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
}


def get_room_photos(folder_name: str) -> List[str]:
    folder_path = os.path.join("images", folder_name)
    if not os.path.isdir(folder_path):
        return []

    photos = []
    valid_extensions = (".webp", ".jpg", ".jpeg", ".png")
    try:
        files = sorted(os.listdir(folder_path))
        for filename in files:
            if filename.lower().endswith(valid_extensions):
                photos.append(os.path.join(folder_path, filename))
    except Exception as e:
        logging.error("Ошибка чтения папки %s: %s", folder_path, e)

    return photos


# =====================================================================
# 5. КЛАВИАТУРЫ
# =====================================================================
def get_main_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏡 Наши номера"),
                KeyboardButton(text="📝 Забронировать"),
            ],
            [
                KeyboardButton(text="🌴 О базе"),
                KeyboardButton(text="🎡 Инфраструктура и услуги"),
            ],
            [
                KeyboardButton(text="⭐ Отзывы"),
                KeyboardButton(text="❓ Вопросы и ответы (FAQ)"),
            ],
            [KeyboardButton(text="📞 Контакты и локация")],
            [KeyboardButton(text="💬 Остались вопросы? Напишите нам")],
        ],
        resize_keyboard=True,
    )


def get_cancel_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить вопрос")]],
        resize_keyboard=True,
    )


def get_rooms_list_kb() -> InlineKeyboardMarkup:
    buttons = []
    for key, data in ROOMS_CATALOG.items():
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🏡 {data['title']}", callback_data=f"view_room_{key}"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_single_room_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛎 Забронировать этот номер",
                    callback_data="click_book_card",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к списку номеров",
                    callback_data="menu_rooms_inline",
                )
            ],
        ]
    )


def get_faq_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Во сколько заселение?", callback_data="faq_checkin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Во сколько выселение из номера?",
                    callback_data="faq_checkout",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Можно ли без питания?", callback_data="faq_no_meals"
                )
            ],
            [
                InlineKeyboardButton(
                    text="При бронировании нужно вносить предоплату?",
                    callback_data="faq_prepayment",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Предоплата возвратная?", callback_data="faq_refund"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Возможно размещение с животными?",
                    callback_data="faq_pets",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Правила проживания (PDF)",
                    callback_data="send_rules_pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📑 Договор оферты (PDF)",
                    callback_data="send_oferta_pdf",
                )
            ],
        ]
    )


# =====================================================================
# 6. ИНИЦИАЛИЗАЦИЯ BOT / DISPATCHER
# =====================================================================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

WELCOME_MESSAGE = (
    "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
    "Семейный отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
    "Зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
    "📅 <b>Период работы:</b> с 11 июня по 15 сентября\n"
    "🕒 <b>Заезд</b> — с 13:00 | <b>Выезд</b> — до 11:00\n\n"
    "Выберите нужный раздел в меню ниже ⬇️"
)


# =====================================================================
# 7. ХЭНДЛЕРЫ
# =====================================================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_MESSAGE, reply_markup=get_main_reply_kb())


# Скрытая админ-команда для просмотра статистики кликов
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if ADMIN_CHAT_ID != 0 and message.chat.id != ADMIN_CHAT_ID:
        return
    stats = get_booking_stats()
    total = stats.get("total_clicks", 0)
    users_cnt = len(stats.get("users", {}))
    await message.answer(
        f"📊 <b>Статистика кликов кнопки «Забронировать»:</b>\n\n"
        f"• Всего переходов: <b>{total}</b>\n"
        f"• Уникальных пользователей: <b>{users_cnt}</b>"
    )


# 1. НАШИ НОМЕРА
@dp.message(F.text == "🏡 Наши номера")
async def msg_rooms(message: types.Message):
    text = (
        "🏡 <b>Номерной фонд базы отдыха «Русалочка»:</b>\n\n"
        "Выберите категорию для просмотра фотографий и описания:"
    )
    await message.answer(text, reply_markup=get_rooms_list_kb())


@dp.callback_query(F.data == "menu_rooms_inline")
async def cb_rooms_inline(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🏡 <b>Номерной фонд базы отдыха «Русалочка»:</b>\n\n"
        "Выберите категорию для просмотра фотографий и описания:"
    )
    await callback.message.answer(text, reply_markup=get_rooms_list_kb())


@dp.callback_query(F.data.startswith("view_room_"))
async def cb_view_room(callback: types.CallbackQuery):
    await callback.answer()
    room_key = callback.data.replace("view_room_", "")
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        return

    photos = get_room_photos(room.get("folder", room_key))

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photos:
        media_group = []
        for idx, photo_path in enumerate(photos):
            photo_file = FSInputFile(photo_path)
            if idx == 0:
                media_group.append(
                    InputMediaPhoto(
                        media=photo_file,
                        caption=room["description"],
                        parse_mode="HTML",
                    )
                )
            else:
                media_group.append(InputMediaPhoto(media=photo_file))

        await callback.message.answer_media_group(media=media_group)
        await callback.message.answer(
            "Выберите действие:", reply_markup=get_single_room_kb()
        )
    else:
        await callback.message.answer(
            room["description"], reply_markup=get_single_room_kb()
        )


# Клик по бронированию из карточки номера (со счётчиком)
@dp.callback_query(F.data == "click_book_card")
async def cb_click_book_card(callback: types.CallbackQuery):
    await callback.answer()
    increment_booking_clicks(callback.from_user.id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть сайт для бронирования", url=BOOKING_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к списку номеров",
                    callback_data="menu_rooms_inline",
                )
            ],
        ]
    )
    await callback.message.answer(
        "Нажмите на кнопку ниже, чтобы перейти на сайт базы отдыха «Русалочка»:",
        reply_markup=kb,
    )


# 2. ЗАБРОНИРОВАТЬ (ИЗ ГЛАВНОГО МЕНЮ)
@dp.message(F.text == "📝 Забронировать")
async def msg_book(message: types.Message):
    increment_booking_clicks(message.from_user.id)
    book_info = (
        "📝 <b>Онлайн-бронирование номеров</b>\n\n"
        "На нашем официальном сайте вы можете в реальном времени выбрать удобные даты, "
        "проверить наличие свободных мест и мгновенно забронировать проживание!\n\n"
        "📌 <b>Условия бронирования:</b>\n"
        "• Период работы: с 11 июня по 15 сентября\n"
        "• Заезд: с 13:00 | Выезд: до 11:00\n"
        "• Предоплата: 30% от общей стоимости\n"
        "• Бесплатная отмена: за 14 дней до заезда"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Перейти на сайт базы для бронирования",
                    url=BOOKING_URL,
                )
            ]
        ]
    )
    await message.answer(book_info, reply_markup=kb)


# 3. ИНФРАСТРУКТУРА И УСЛУГИ
@dp.message(F.text == "🎡 Инфраструктура и услуги")
async def msg_infra(message: types.Message):
    infra_text = (
        "🎡 <b>ИНФРАСТРУКТУРА И УСЛУГИ</b>\n\n"
        "✅ <b>ВКЛЮЧЕНО В СТОИМОСТЬ:</b>\n"
        "• 👶 Детская игровая площадка\n"
        "• ⚽ Настольный теннис, футбол, шахматы, спортинвентарь\n"
        "• 🥩 Оборудованная мангальная зона (решетки, шампуры, печь, казан 12 л)\n"
        "• 🌸 Зеленая ухоженная территория (350 кустов роз и 2000 кустов лаванды)\n\n"
        "💲 <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:</b>\n"
        "• 👶 Детская кроватка (до 3 лет): 800 ₽/сут (от 10 суток — бесплатно)\n"
        "• 🐶 Проживание с питомцем (до 5–7 кг): 800 ₽/сут (депозит 5 000 ₽)\n"
        "• 🎨 Творческие мастер-классы и шоу\n"
        "• 🧺 Прачечная и гладильная комната\n"
        "• ⚡ Зарядная станция GB/T 7 кВт для электромобилей:\n"
        "  — Цена: 25 ₽ / 1 кВт·ч\n"
        "  — Режим: с 9:00 до 19:00, для гостей базы отдыха — круглосуточно"
    )
    await message.answer(infra_text)


# 4. О БАЗЕ
@dp.message(F.text == "🌴 О базе")
async def msg_about(message: types.Message):
    about_text = (
        "🌴 <b>База отдыха «Русалочка»</b>\n\n"
        "• Чистейший широкий песчаный пляж Черного моря\n"
        "• Охраняемая закрытая зеленая территория\n"
        "• Комплексное 3-разовое питание включено во все основные категории номеров\n"
        "• Период сезона: с 11 июня по 15 сентября\n\n"
        "🌐 <b>Официальные сайты:</b>\n"
        "• https://rusalo4ka.com/\n"
        "• https://русалочка.рф"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 rusalo4ka.com", url="https://rusalo4ka.com/"
                ),
                InlineKeyboardButton(
                    text="🌐 русалочка.рф",
                    url="https://xn--80aaahx7adkc.xn--p1ai/",
                ),
            ]
        ]
    )
    await message.answer(about_text, reply_markup=kb)


# 5. ОТЗЫВЫ
@dp.message(F.text == "⭐ Отзывы")
async def msg_reviews(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Отзывы на Яндекс.Картах", url=REVIEWS_YANDEX_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺️ Отзывы в 2ГИС", url=REVIEWS_2GIS_URL
                )
            ],
        ]
    )
    await message.answer(
        "⭐ Отзывы наших гостей на онлайн-картах:", reply_markup=kb
    )


# 6. КОНТАКТЫ И ЛОКАЦИЯ
@dp.message(F.text == "📞 Контакты и локация")
async def msg_contacts(message: types.Message):
    contacts_text = (
        "📞 <b>Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Краснодарский край, г. Анапа, ст. Благовещенская, ул. Прибрежная, д. 13, б/о «Русалочка»\n"
        "📞 <b>Отдел бронирования:</b> +7 (918) 47-74-366\n"
        "✉️ <b>E-mail:</b> anaparusalochka@rambler.ru\n"
        "🌐 <b>Сайты:</b> https://rusalo4ka.com/ | https://русалочка.рф"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧭 Маршрут в Яндекс Картах", url=YANDEX_ROUTE_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Правила проживания (PDF)",
                    callback_data="send_rules_pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📑 Договор оферты (PDF)",
                    callback_data="send_oferta_pdf",
                )
            ],
        ]
    )
    await message.answer(contacts_text, reply_markup=kb)


@dp.callback_query(F.data == "send_rules_pdf")
async def cb_send_rules_pdf(callback: types.CallbackQuery):
    await callback.answer()
    if os.path.exists(RULES_FILE_PATH):
        doc = FSInputFile(
            RULES_FILE_PATH, filename="Правила_базы_отдыха_Русалочка.pdf"
        )
        await callback.message.answer_document(
            document=doc,
            caption="📄 Официальные правила проживания на базе отдыха «Русалочка»",
        )
    else:
        await callback.message.answer(
            "📄 Правила доступны на официальном сайте: https://rusalo4ka.com/"
        )


@dp.callback_query(F.data == "send_oferta_pdf")
async def cb_send_oferta_pdf(callback: types.CallbackQuery):
    await callback.answer()
    if os.path.exists(OFERTA_FILE_PATH):
        doc = FSInputFile(
            OFERTA_FILE_PATH, filename="Договор_оферты_Русалочка.pdf"
        )
        await callback.message.answer_document(
            document=doc,
            caption="📑 Договор публичной оферты базы отдыха «Русалочка»",
        )
    else:
        await callback.message.answer(
            "📑 Договор оферты доступен на официальном сайте: https://rusalo4ka.com/"
        )


# 7. FAQ
@dp.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def msg_faq(message: types.Message):
    await message.answer("Часто задаваемые вопросы:", reply_markup=get_faq_kb())


@dp.callback_query(F.data == "faq_checkin")
async def cb_faq_checkin(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Во сколько заселение?</b>\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы заселим Вас раньше."
    await callback.message.answer(ans)


@dp.callback_query(F.data == "faq_checkout")
async def cb_faq_checkout(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Во сколько выселение?</b>\n\n— освободить номер нужно до 11:00, ключи и браслеты сдаются в администрацию."
    await callback.message.answer(ans)


# НОВЫЙ ПУНКТ: Можно ли без питания?
@dp.callback_query(F.data == "faq_no_meals")
async def cb_faq_no_meals(callback: types.CallbackQuery):
    await callback.answer()
    ans = (
        "<b>Можно ли без питания?</b>\n\n"
        "— Да, можно. При бронировании можно выбрать тариф «Без питания».\n\n"
        "Если вы бронируете тариф «Без питания» и решите докупить питание на месте, "
        "стоимость питания составит: <b>1 500 ₽ / сутки</b> с человека."
    )
    await callback.message.answer(ans)


@dp.callback_query(F.data == "faq_prepayment")
async def cb_faq_prepayment(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>При бронировании нужно вносить предоплату?</b>\n\n— бронирование выбранной категории номера производится после перечисления предоплаты (30% от полной стоимости проживания)."
    await callback.message.answer(ans)


@dp.callback_query(F.data == "faq_refund")
async def cb_faq_refund(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Предоплата возвратная?</b>\n\n— бесплатная отмена бронирования возможна за 14 дней до заезда, после — взимается 100% от суммы предоплаты."
    await callback.message.answer(ans)


@dp.callback_query(F.data == "faq_pets")
async def cb_faq_pets(callback: types.CallbackQuery):
    await callback.answer()
    ans = (
        "<b>Возможно размещение с животными?</b>\n\n"
        "— Разрешено исключительно с декоративными собаками весом до 5–7 кг в категории «Номер с кухней эко».\n"
        "— Тариф: 800 руб./сутки.\n"
        "— Рекомендуется возвратный депозит: 5 000 руб.\n"
        "— Выгул собак по территории базы запрещен.\n\n"
        "📄 Ознакомьтесь с документами по кнопкам ниже:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Правила проживания (PDF)",
                    callback_data="send_rules_pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📑 Договор оферты (PDF)",
                    callback_data="send_oferta_pdf",
                )
            ],
        ]
    )
    await callback.message.answer(ans, reply_markup=kb)


# 8. ОБРАТНАЯ СВЯЗЬ
@dp.message(F.text == "💬 Остались вопросы? Напишите нам")
async def msg_feedback(message: types.Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_question)
    prompt = (
        "💬 <b>Задать вопрос администратору базы отдыха</b>\n\n"
        "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
    )
    await message.answer(prompt, reply_markup=get_cancel_reply_kb())


@dp.message(F.text == "❌ Отменить вопрос")
async def msg_cancel_feedback(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отправка вопроса отменена.", reply_markup=get_main_reply_kb()
    )


@dp.message(SupportStates.waiting_for_question, F.chat.type == "private")
async def process_guest_question(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    name = message.from_user.full_name

    await message.answer(
        "✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\n"
        "Мы ответим вам прямо в этот диалог в ближайшее время.",
        reply_markup=get_main_reply_kb(),
    )

    if ADMIN_CHAT_ID != 0:
        ticket_text = (
            "📩 <b>НОВЫЙ ВОПРОС ОТ ГОСТЯ В TELEGRAM</b>\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            f"💬 <b>Вопрос:</b>\n«{message.text}»\n\n"
            "👉 Чтобы ответить гостю, ответьте цитатой (Reply) на это сообщение.\n"
            f"#user_{user_id}"
        )
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=ticket_text)


# 9. ОТВЕТ АДМИНИСТРАТОРА
@dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def process_admin_reply(message: types.Message):
    replied_text = (
        message.reply_to_message.text
        or message.reply_to_message.caption
        or ""
    )
    match = re.search(r"#user_(\d+)", replied_text)
    if match and message.text:
        target_guest_id = int(match.group(1))
        answer_to_guest = (
            "💬 <b>Ответ от администрации базы отдыха «Русалочка»:</b>\n\n"
            f"{message.text}\n\n"
            "---------------------------------\n"
            "Если у вас остались вопросы, напишите их прямо сюда!"
        )
        try:
            await bot.send_message(
                chat_id=target_guest_id, text=answer_to_guest
            )
            await message.reply("✅ Ответ успешно доставлен гостю!")
        except Exception as e:
            await message.reply(
                f"⚠️ Не удалось доставить ответ пользователю {target_guest_id}: {e}"
            )


# =====================================================================
# 8. ЗАПУСК
# =====================================================================
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("=" * 60)
    logging.info("ЗАПУСК TELEGRAM-БОТА")
    logging.info("Версия: %s", BOT_VERSION)
    logging.info("=" * 60)

    try:
        me = await bot.get_me()
        logging.info("Telegram bot username: @%s", me.username)
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    except Exception:
        logging.exception("КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ БОТА")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
