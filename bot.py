import os
import re
import logging
from typing import Dict, Any, List

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    InputMediaPhoto,
)
from dotenv import load_dotenv

# =====================================================================
# 1. КОНФИГУРАЦИЯ И ДАННЫЕ
# =====================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-79780607715530"))

BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=11-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_YANDEX_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
REVIEWS_2GIS_URL = "https://2gis.ru/anapa/firm/70000001033010188"
YANDEX_ROUTE_URL = "https://yandex.ru/maps/org/rusalochka/241387417775?si=5zprzpwhdg2vqk8wegq6b3krmr"
RULES_FILE_PATH = "rules.pdf"

class SupportStates(StatesGroup):
    waiting_for_question = State()

ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "folder": "kitchen_2p",
        "description": (
            "🏡 <b>Номер с кухней (апарт.) 2-х местный + доп.место</b>\n\n"
            "Уютный семейный апартамент с индивидуальной кухонной зоной.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место (диван / кресло-кровать)\n"
            "• Индивидуальная кухня: плита, СВЧ, холодильник, посуда, электрочайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi\n"
            "• Санузел с душевой кабиной\n"
            "• Индивидуальная веранда/балкон для отдыха\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 4 500 ₽ / сутки"
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
            "• Кухонный модуль: варочная панель, СВЧ, холодильник, посуда, электрочайник\n"
            "• Сплит-система, цифровое ТВ, Wi-Fi\n"
            "• Ванная комната с душем\n"
            "• Просторная веранда\n\n"
            "👥 <b>Вместимость:</b> до 4 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 5 500 ₽ / сутки"
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
            "• Сплит-система, холодильник, электрочайник, телевизор\n"
            "• Собственный санузел с душем\n"
            "• Терраса со столом и стульями на свежем воздухе\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 4 000 ₽ / сутки"
        ),
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "folder": "eco_2k_3p",
        "description": (
            "🏡 <b>Эко-домик 2-комнатный 3-х местный + доп.место</b>\n\n"
            "Двухкомнатный коттедж из бруса для большой семьи.\n\n"
            "<b>В домике:</b>\n"
            "• 2 изолированные спальные комнаты\n"
            "• 3 основных спальных места + евро-раскладушка\n"
            "• Кондиционер, холодильник, ТВ, электрочайник\n"
            "• Санузел с душевой кабиной\n"
            "• Большая деревянная терраса\n\n"
            "👥 <b>Вместимость:</b> до 4 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 6 000 ₽ / сутки"
        ),
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "folder": "std_brick_3p",
        "description": (
            "🏡 <b>СТАНДАРТ кирпичный домик 3-х местный</b>\n\n"
            "Капитальный прохладный домик для отдыха 3 человек.\n\n"
            "<b>В домике:</b>\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Собственный санузел с душем\n"
            "• Индивидуальная веранда перед входом\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 3 500 ₽ / сутки"
        ),
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "folder": "std_wood_2p",
        "description": (
            "🏡 <b>СТАНДАРТ Деревянный домик 2-х местный</b>\n\n"
            "Уютный деревянный домик для двоих в тишине и зелени.\n\n"
            "<b>В домике:</b>\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Открытая терраса со столиком\n\n"
            "👥 <b>Вместимость:</b> до 2 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 2 800 ₽ / сутки"
        ),
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный",
        "folder": "std_2p",
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный</b>\n\n"
            "Классический номер для 2 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать\n"
            "• Сплит-система, ТВ, холодильник\n"
            "• Санузел и душевая\n"
            "• Зона отдыха\n\n"
            "👥 <b>Вместимость:</b> до 2 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 3 000 ₽ / сутки"
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
            "• Сплит-система, телевизор, холодильник\n"
            "• Санузел с душем\n"
            "• Терраса для отдыха\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 3 300 ₽ / сутки"
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
            "• Кондиционер, холодильник, телевизор\n"
            "• Санузел с душем\n"
            "• Веранда для вечернего отдыха\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 3 700 ₽ / сутки"
        ),
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "folder": "std_4p",
        "description": (
            "🏡 <b>СТАНДАРТ 4-х местный + доп.место</b>\n\n"
            "Семейный просторный номер на 4–5 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• Спальные места: 4 основных + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Собственная летняя веранда\n\n"
            "👥 <b>Вместимость:</b> до 5 человек\n"
            "🍽 <b>с 3-х разовым комплексным питанием</b>\n"
            "💰 <b>Стоимость:</b> от 4 600 ₽ / сутки"
        ),
    },
}

def get_room_photos(folder_name: str) -> List[str]:
    """Сканирует папку images/<folder_name> и возвращает пути к 1.webp, 2.webp и т.д."""
    folder_path = os.path.join("images", folder_name)
    if not os.path.isdir(folder_path):
        return []

    photos = []
    valid_extensions = ('.webp', '.jpg', '.jpeg', '.png')
    try:
        files = sorted(os.listdir(folder_path))
        for f in files:
            if f.lower().endswith(valid_extensions):
                photos.append(os.path.join(folder_path, f))
    except Exception as e:
        logging.error(f"Ошибка чтения папки {folder_path}: {e}")
    return photos

# =====================================================================
# 2. КЛАВИАТУРЫ
# =====================================================================
def get_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏡 Список номеров", callback_data="menu_rooms"), InlineKeyboardButton(text="📝 Забронировать", callback_data="menu_book")],
        [InlineKeyboardButton(text="🌴 О базе", callback_data="menu_about"), InlineKeyboardButton(text="🎡 Услуги и сервис", callback_data="menu_infra")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="menu_reviews"), InlineKeyboardButton(text="❓ Вопросы и ответы (FAQ)", callback_data="menu_faq")],
        [InlineKeyboardButton(text="📞 Контакты и локация", callback_data="menu_contacts")],
        [InlineKeyboardButton(text="💬 Задать вопрос администратору", callback_data="menu_feedback")]
    ])

def get_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить вопрос", callback_data="cancel_feedback")]
    ])

def get_rooms_list_kb() -> InlineKeyboardMarkup:
    buttons = []
    for key, data in ROOMS_CATALOG.items():
        buttons.append([InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"view_room_{key}")])
    buttons.append([InlineKeyboardButton(text="⬅️️ В главное меню", callback_data="menu_root")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_single_room_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛎 Забронировать этот номер", url=BOOKING_URL)],
        [InlineKeyboardButton(text="⬅️ Назад к списку номеров", callback_data="menu_rooms")]
    ])

def get_faq_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Во сколько заселение?", callback_data="faq_checkin")],
        [InlineKeyboardButton(text="Во сколько выселение из номера?", callback_data="faq_checkout")],
        [InlineKeyboardButton(text="При бронировании нужно вносить предоплату?", callback_data="faq_prepayment")],
        [InlineKeyboardButton(text="Предоплата возвратная?", callback_data="faq_refund")],
        [InlineKeyboardButton(text="Возможно размещение с животными?", callback_data="faq_pets")],
        [InlineKeyboardButton(text="📄 Посмотреть правила (PDF)", callback_data="send_rules_pdf")],
        [InlineKeyboardButton(text="💬 Задать свой вопрос", callback_data="menu_feedback")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])

# =====================================================================
# 3. ИНИЦИАЛИЗАЦИЯ И ХЭНДЛЕРЫ
# =====================================================================
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
        "Семейный отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
        "Зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
        "📅 <b>Период работы:</b> с 11 июня по 15 сентября[cite: 17]\n"
        "🕒 <b>Заезд</b> — с 13:00 | <b>Выезд</b> — до 11:00\n\n"
        "Выберите нужный раздел в меню ниже ⬇️"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_kb())

@dp.callback_query(F.data == "menu_root")
async def cb_menu_root(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    welcome_text = (
        "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
        "Семейный отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
        "Зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
        "📅 <b>Период работы:</b> с 11 июня по 15 сентября[cite: 17]\n"
        "🕒 <b>Заезд</b> — с 13:00 | <b>Выезд</b> — до 11:00\n\n"
        "Выберите нужный раздел в меню ниже ⬇️"
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(welcome_text, reply_markup=get_main_menu_kb())
    else:
        await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_kb())

@dp.callback_query(F.data == "menu_rooms")
async def cb_rooms(callback: types.CallbackQuery):
    await callback.answer()
    text = "🏡 <b>Номерной фонд базы отдыха «Русалочка»:</b>\n\nВыберите категорию для просмотра фотографий и описания:"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_rooms_list_kb())
    else:
        await callback.message.edit_text(text, reply_markup=get_rooms_list_kb())

@dp.callback_query(F.data.startswith("view_room_"))
async def cb_view_room(callback: types.CallbackQuery):
    await callback.answer()
    room_key = callback.data.replace("view_room_", "")
    room = ROOMS_CATALOG.get(room_key)
    if not room:
        return

    photos = get_room_photos(room.get("folder", room_key))

    # Удаляем предыдущее меню перед выводом карточки номера
    try:
        await callback.message.delete()
    except Exception:
        pass

    if photos:
        # Отправляем фотографии альбомом (медиагруппой)
        media_group = []
        for idx, p_path in enumerate(photos):
            photo_file = FSInputFile(p_path)
            if idx == 0:
                media_group.append(InputMediaPhoto(media=photo_file, caption=room["description"], parse_mode="HTML"))
            else:
                media_group.append(InputMediaPhoto(media=photo_file))
        await callback.message.answer_media_group(media=media_group)
        await callback.message.answer("Выберите действие:", reply_markup=get_single_room_kb())
    else:
        await callback.message.answer(room["description"], reply_markup=get_single_room_kb())

@dp.callback_query(F.data == "menu_book")
async def cb_book(callback: types.CallbackQuery):
    await callback.answer()
    book_info = (
        "📝 <b>Онлайн-бронирование номеров</b>\n\n"
        "В нашем официальном модуле вы можете в реальном времени выбрать удобные даты, "
        "проверить наличие свободных мест и мгновенно забронировать проживание!\n\n"
        "📌 <b>Условия бронирования:</b>\n"
        "• Период работы: с 11 июня по 15 сентября[cite: 17]\n"
        "• Заезд: с 13:00 | Выезд: до 11:00\n"
        "• Предоплата: 30% от общей стоимости\n"
        "• Бесплатная отмена: возможна за 14 дней до заезда"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Перейти к бронированию и оплате", url=BOOKING_URL)],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await callback.message.edit_text(book_info, reply_markup=kb)

@dp.callback_query(F.data == "menu_infra")
async def cb_infra(callback: types.CallbackQuery):
    await callback.answer()
    infra_text = (
        "🎡 <b>ИНФРАСТРУКТУРА И УСЛУГИ</b>\n\n"
        "✅ <b>ВКЛЮЧЕНО В СТОИМОСТЬ:</b>\n"
        "• 👶 Детская игровая площадка\n"
        "• ⚽ Настольный теннис, футбол, шахматы, спортинвентарь\n"
        "• 🥩 Оборудованная мангальная зона (решетки, шампуры, печь, казан 12 л)\n"
        "• 🌸 Зеленая ухоженная территория (350 кустов роз и 2000 кустов лаванды)[cite: 18]\n\n"
        "💲 <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:</b>\n"
        "• 🎨 Творческие мастер-классы и шоу\n"
        "• 🧺 Прачечная и гладильная комната\n"
        "• ⚡ Зарядная станция GB/T 7 кВт для электромобилей:\n"
        "  — Цена: 25 ₽ / 1 кВт·ч[cite: 18]\n"
        "  — Время работы: с 9:00 до 19:00, для гостей базы отдыха — круглосуточно[cite: 18]"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await callback.message.edit_text(infra_text, reply_markup=kb)

@dp.callback_query(F.data == "menu_about")
async def cb_about(callback: types.CallbackQuery):
    await callback.answer()
    about_text = (
        "🌴 <b>База отдыха «Русалочка»</b>\n\n"
        "• Чистейший широкий песчаный пляж Черного моря\n"
        "• Охраняемая закрытая зеленая территория\n"
        "• Комплексное 3-разовое питание включено во все категории номеров\n"
        "• Период сезона: с 11 июня по 15 сентября[cite: 17]\n\n"
        "🌐 <b>Официальные сайты:</b>\n"
        "• https://rusalo4ka.com/[cite: 19]\n"
        "• https://русалочка.рф[cite: 19]"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 rusalo4ka.com", url="https://rusalo4ka.com/"), InlineKeyboardButton(text="🌐 русалочка.рф", url="https://xn--80aaahx7adkc.xn--p1ai/")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await callback.message.edit_text(about_text, reply_markup=kb)

@dp.callback_query(F.data == "menu_reviews")
async def cb_reviews(callback: types.CallbackQuery):
    await callback.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Отзывы на Яндекс.Картах", url=REVIEWS_YANDEX_URL)],
        [InlineKeyboardButton(text="🗺️ Отзывы в 2ГИС", url=REVIEWS_2GIS_URL)],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await callback.message.edit_text("⭐ Отзывы наших гостей на онлайн-картах:", reply_markup=kb)

@dp.callback_query(F.data == "menu_contacts")
async def cb_contacts(callback: types.CallbackQuery):
    await callback.answer()
    contacts_text = (
        "📞 <b>Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Краснодарский край, г. Анапа, ст. Благовещенская, ул. Прибрежная, д. 13, б/о «Русалочка»[cite: 21]\n"
        "📞 <b>Отдел бронирования:</b> +7 (918) 47-74-366\n"
        "✉️ <b>E-mail:</b> anaparusalochka@rambler.ru\n"
        "🌐 <b>Сайты:</b> https://rusalo4ka.com/ | https://русалочка.рф[cite: 19]"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧭 Маршрут в Яндекс Картах", url=YANDEX_ROUTE_URL)],
        [InlineKeyboardButton(text="📄 Посмотреть правила (PDF)", callback_data="send_rules_pdf")],
        [InlineKeyboardButton(text="💬 Задать вопрос в чате", callback_data="menu_feedback")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await callback.message.edit_text(contacts_text, reply_markup=kb)

@dp.callback_query(F.data == "send_rules_pdf")
async def cb_send_rules_pdf(callback: types.CallbackQuery):
    await callback.answer()
    if os.path.exists(RULES_FILE_PATH):
        doc = FSInputFile(RULES_FILE_PATH, filename="Правила_базы_отдыха_Русалочка.pdf")
        await callback.message.answer_document(document=doc, caption="📄 Официальные правила проживания на базе отдыха «Русалочка»")
    else:
        await callback.message.answer("📄 Правила доступны на официальном сайте: https://rusalo4ka.com/[cite: 19]")

@dp.callback_query(F.data == "menu_faq")
async def cb_faq(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Часто задаваемые вопросы:", reply_markup=get_faq_kb())

@dp.callback_query(F.data == "faq_checkin")
async def cb_faq_checkin(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Во сколько заселение?</b>\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы заселим Вас раньше."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="menu_faq")]])
    await callback.message.edit_text(ans, reply_markup=kb)

@dp.callback_query(F.data == "faq_checkout")
async def cb_faq_checkout(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Во сколько выселение?</b>\n\n— освободить номер нужно до 11:00, ключи и браслеты сдаются в администрацию."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="menu_faq")]])
    await callback.message.edit_text(ans, reply_markup=kb)

@dp.callback_query(F.data == "faq_prepayment")
async def cb_faq_prepayment(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>При бронировании нужно вносить предоплату?</b>\n\n— бронирование выбранной категории номера производится после перечисления предоплаты (30% от полной стоимости проживания)."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="menu_faq")]])
    await callback.message.edit_text(ans, reply_markup=kb)

@dp.callback_query(F.data == "faq_refund")
async def cb_faq_refund(callback: types.CallbackQuery):
    await callback.answer()
    ans = "<b>Предоплата возвратная?</b>\n\n— бесплатная отмена бронирования возможна за 14 дней до заезда, после — взимается 100% от суммы предоплаты."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="menu_faq")]])
    await callback.message.edit_text(ans, reply_markup=kb)

@dp.callback_query(F.data == "faq_pets")
async def cb_faq_pets(callback: types.CallbackQuery):
    await callback.answer()
    ans = (
        "<b>Возможно размещение с животными?</b>\n\n"
        "— Разрешено исключительно с декоративными собаками весом до 6 кг в категории «Номер с кухней эко».\n"
        "— Тариф: 800 руб./сутки.\n"
        "— Выгул собак по территории базы запрещен.\n\n"
        "📄 Ознакомьтесь с подробными правилами проживания по кнопке ниже:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Скачать полные правила (PDF)", callback_data="send_rules_pdf")],
        [InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="menu_faq")]
    ])
    await callback.message.edit_text(ans, reply_markup=kb)

# =====================================================================
# 4. ПОДДЕРЖКА И МОСТ С ЧАТОМ АДМИНИСТРАТОРОВ
# =====================================================================
@dp.callback_query(F.data == "menu_feedback")
async def cb_feedback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SupportStates.waiting_for_question)
    prompt = (
        "💬 <b>Задать вопрос администратору базы отдыха</b>\n\n"
        "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
    )
    await callback.message.answer(prompt, reply_markup=get_cancel_kb())

@dp.callback_query(F.data == "cancel_feedback")
async def cb_cancel_feedback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer("Отправка вопроса отменена.", reply_markup=get_main_menu_kb())

@dp.message(SupportStates.waiting_for_question, F.chat.type == "private")
async def process_guest_question(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    name = message.from_user.full_name

    await message.answer(
        "✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\n"
        "Мы ответим вам прямо в этот диалог в ближайшее время.",
        reply_markup=get_main_menu_kb()
    )

    if ADMIN_CHAT_ID != 0:
        ticket_text = (
            f"📩 <b>НОВЫЙ ВОПРОС ОТ ГОСТЯ В TELEGRAM</b>\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            f"💬 <b>Вопрос:</b>\n«{message.text}»\n\n"
            f"👉 Чтобы ответить гостю, ответьте цитатой (Reply) на это сообщение.\n"
            f"#user_{user_id}"
        )
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=ticket_text)

@dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def process_admin_reply(message: types.Message):
    replied_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = re.search(r"#user_(\d+)", replied_text)
    if match and message.text:
        target_guest_id = int(match.group(1))
        answer_to_guest = (
            f"💬 <b>Ответ от администрации базы отдыха «Русалочка»:</b>\n\n"
            f"{message.text}\n\n"
            f"---------------------------------\n"
            f"Если у вас остались вопросы, напишите их прямо сюда!"
        )
        try:
            await bot.send_message(chat_id=target_guest_id, text=answer_to_guest)
            await message.reply("✅ Ответ успешно доставлен гостю!")
        except Exception as e:
            await message.reply(f"⚠️ Не удалось доставить ответ пользователю {target_guest_id}: {e}")

@dp.message(F.chat.type == "private")
async def fallback_private(message: types.Message):
    prompt = (
        "Я получил ваше сообщение! 🌊\n\n"
        "Если вы хотите передать вопрос администратору базы «Русалочка», нажмите кнопку ниже:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Задать вопрос администратору", callback_data="menu_feedback")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu_root")]
    ])
    await message.answer(prompt, reply_markup=kb)

# =====================================================================
# 5. ЗАПУСК БОТА
# =====================================================================
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Запуск Telegram-бота базы отдыха «Русалочка»...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
