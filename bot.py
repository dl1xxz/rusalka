import os
import asyncio
import logging
from typing import Dict, Any

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    InputMediaPhoto,
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

# Ссылки проекта
BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=15-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
PDF_RULES_PATH = "rules.pdf"

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

VALID_IMG_EXTENSIONS = ('.webp', '.jpg', '.jpeg', '.png')

# Каталог номеров базы отдыха «Русалочка»
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "folder": "images/kitchen_2p",
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
            "💰 <b>Стоимость:</b> от 4 500 ₽ / сутки"
        ),
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "folder": "images/kitchen_3p",
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
            "💰 <b>Стоимость:</b> от 5 500 ₽ / сутки"
        ),
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "folder": "images/eco_1k_2p",
        "description": (
            "🏡 <b>Эко-домик 1-комнатный 2-х местный + доп.место</b>\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "<b>В домике:</b>\n"
            "• Двуспальная кровать + кресло-кровать\n"
            "• Сплит-система, холодильник, электрочайник, телевизор\n"
            "• Собственный санузел с душем\n"
            "• Терраса со столом и стульями на свежем воздухе\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "💰 <b>Стоимость:</b> от 4 000 ₽ / сутки"
        ),
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "folder": "images/eco_2k_3p",
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
            "💰 <b>Стоимость:</b> от 6 000 ₽ / сутки"
        ),
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "folder": "images/std_brick_3p",
        "description": (
            "🏡 <b>СТАНДАРТ кирпичный домик 3-х местный</b>\n\n"
            "Капитальный прохладный домик для отдыха 3 человек.\n\n"
            "<b>В домике:</b>\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Собственный санузел с душем\n"
            "• Индивидуальная веранда перед входом\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "💰 <b>Стоимость:</b> от 3 500 ₽ / сутки"
        ),
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "folder": "images/std_wood_2p",
        "description": (
            "🏡 <b>СТАНДАРТ Деревянный домик 2-х местный</b>\n\n"
            "Уютный деревянный домик для двоих в тишине и зелени.\n\n"
            "<b>В домике:</b>\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Открытая терраса со столиком\n\n"
            "👥 <b>Вместимость:</b> до 2 человек\n"
            "💰 <b>Стоимость:</b> от 2 800 ₽ / сутки"
        ),
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный",
        "folder": "images/std_2p",
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный</b>\n\n"
            "Классический номер для 2 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать\n"
            "• Сплит-система, ТВ, холодильник\n"
            "• Санузел и душевая\n"
            "• Зона отдыха\n\n"
            "👥 <b>Вместимость:</b> до 2 человек\n"
            "💰 <b>Стоимость:</b> от 3 000 ₽ / сутки"
        ),
    },
    "std_2p_extra": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "folder": "images/std_2p_extra",
        "description": (
            "🏡 <b>СТАНДАРТ 2-х местный + доп.место</b>\n\n"
            "Номер категории стандарт для семьи до 3 человек.\n\n"
            "<b>В номере:</b>\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, телевизор, холодильник\n"
            "• Санузел с душем\n"
            "• Терраса для отдыха\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "💰 <b>Стоимость:</b> от 3 300 ₽ / сутки"
        ),
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный",
        "folder": "images/std_3p",
        "description": (
            "🏡 <b>СТАНДАРТ 3-х местный</b>\n\n"
            "Просторный 3-местный номер стандартной категории.\n\n"
            "<b>В номере:</b>\n"
            "• 3 основных спальных места\n"
            "• Кондиционер, холодильник, телевизор\n"
            "• Санузел с душем\n"
            "• Веранда для вечернего отдыха\n\n"
            "👥 <b>Вместимость:</b> до 3 человек\n"
            "💰 <b>Стоимость:</b> от 3 700 ₽ / сутки"
        ),
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "folder": "images/std_4p",
        "description": (
            "🏡 <b>СТАНДАРТ 4-х местный + доп.место</b>\n\n"
            "Семейный просторный номер на 4–5 гостей.\n\n"
            "<b>В номере:</b>\n"
            "• Спальные места: 4 основных + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Собственная летняя веранда\n\n"
            "👥 <b>Вместимость:</b> до 5 человек\n"
            "💰 <b>Стоимость:</b> от 4 600 ₽ / сутки"
        ),
    },
}

# =====================================================================
# FSM ДЛЯ ОБРАТНОЙ СВЯЗИ
# =====================================================================
class FeedbackState(StatesGroup):
    waiting_for_question = State()

# =====================================================================
# ФУНКЦИЯ ОТПРАВКИ ФОТО АЛЬБОМАМИ ИЗ ПАПКИ
# =====================================================================
async def send_room_media(message: Message, folder_path: str, caption: str, reply_markup: InlineKeyboardMarkup):
    images_list = []
    
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        files = sorted(os.listdir(folder_path))
        for f in files:
            if f.lower().endswith(VALID_IMG_EXTENSIONS):
                images_list.append(os.path.join(folder_path, f))

    if len(images_list) > 1:
        media_group = []
        for idx, img_path in enumerate(images_list[:10]):
            if idx == 0:
                media_group.append(InputMediaPhoto(media=FSInputFile(img_path), caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=FSInputFile(img_path)))
        
        await message.answer_media_group(media=media_group)
        await message.answer("Выберите действие:", reply_markup=reply_markup)
    elif len(images_list) == 1:
        await message.answer_photo(
            photo=FSInputFile(images_list[0]),
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        await message.answer(text=caption, reply_markup=reply_markup)

# =====================================================================
# КЛАВИАТУРЫ
# =====================================================================
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🏡 Наши номера"), KeyboardButton(text="📝 Забронировать")],
        [KeyboardButton(text="🌴 О базе"), KeyboardButton(text="🎡 Инфраструктура и услуги")],
        [KeyboardButton(text="⭐ Отзывы"), KeyboardButton(text="❓ Вопросы и ответы (FAQ)")],
        [KeyboardButton(text="📞 Контакты и локация")],
        [KeyboardButton(text="💬 Остались вопросы? Напишите нам")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_feedback_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить вопрос")]],
        resize_keyboard=True
    )

def get_rooms_list_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏡 {data['title']}", callback_data=f"view_room:{key}")]
        for key, data in ROOMS_CATALOG.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_single_room_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛎 Забронировать этот номер", url=BOOKING_URL)],
            [InlineKeyboardButton(text="⬅️ Назад к списку категорий", callback_data="back_to_rooms_catalog")]
        ]
    )

def get_booking_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к бронированию и оплате", url=BOOKING_URL)],
            [InlineKeyboardButton(text="💬 Задать вопрос администратору", callback_data="start_feedback_fsm")]
        ]
    )

def get_faq_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Во сколько заселение?", callback_data="faq:checkin")],
            [InlineKeyboardButton(text="Во сколько выселение из номера?", callback_data="faq:checkout")],
            [InlineKeyboardButton(text="При бронировании нужно вносить предоплату?", callback_data="faq:prepayment")],
            [InlineKeyboardButton(text="Предоплата возвратная?", callback_data="faq:refund")],
            [InlineKeyboardButton(text="Возможно размещение с животными?", callback_data="faq:pets")],
            [InlineKeyboardButton(text="📄 Посмотреть полные правила (PDF)", callback_data="faq:pdf_rules")],
            [InlineKeyboardButton(text="💬 Не нашли ответ? Написать нам", callback_data="start_feedback_fsm")],
        ]
    )

def get_contacts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Задать вопрос в боте", callback_data="start_feedback_fsm")],
            [InlineKeyboardButton(text="📄 Правила проживания (PDF)", callback_data="faq:pdf_rules")],
            [InlineKeyboardButton(text="🌐 Открыть сайт rusalo4ka.com", url="https://rusalo4ka.com/")]
        ]
    )

# =====================================================================
# РОУТЕР И ОБРАБОТЧИКИ
# =====================================================================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "<b>Добро пожаловать в базу отдыха «Русалочка»! 🌊</b>\n\n"
        "Отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
        "Ухоженная зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
        "📅 <b>Период работы: с 15 июня по 15 сентября</b>\n"
        "🕒 <b>Заезд — с 13:00 | Выезд — до 11:00</b>\n\n"
        "Ознакомьтесь с номерным фондом и услугами базы в меню ниже ⬇️"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())

# --- ОБРАБОТКА СИСТЕМЫ ВОПРОСОВ (ИНТЕГРАЦИЯ С ЧАТОМ АДМИНИСТРАТОРОВ) ---
@router.message(F.text == "❌ Отменить вопрос")
async def cancel_feedback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отправка вопроса отменена.", reply_markup=get_main_menu_keyboard())

@router.message(F.text.in_(["💬 Остались вопросы? Напишите нам", "💬 Задать вопрос"]))
@router.callback_query(F.data == "start_feedback_fsm")
async def start_feedback(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "<b>💬 Задать вопрос администратору базы отдыха</b>\n\n"
        "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот чат!"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_cancel_feedback_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_feedback_keyboard())
    await state.set_state(FeedbackState.waiting_for_question)

@router.message(FeedbackState.waiting_for_question, F.text)
async def process_feedback_question(message: Message, state: FSMContext, bot: Bot):
    user_question = message.text.strip()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "нет @username"

    # Сообщение гостю
    await message.answer(
        "✅ <b>Ваш вопрос передан администраторам базы отдыха «Русалочка»!</b>\n\n"
        "Мы ответим вам прямо сюда в ближайшее время.",
        reply_markup=get_main_menu_keyboard()
    )

    # Уведомление в админ-чат с системной меткой #USER_ID для ответа
    admin_ticket = (
        f"📩 <b>НОВЫЙ ВОПРОС ОТ ГОСТЯ</b>\n"
        f"👤 <b>Гость:</b> {user_name} ({username})\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        f"💬 <b>Вопрос:</b>\n<i>{user_question}</i>\n\n"
        f"👉 <i>Чтобы ответить гостю, просто нажмите «Ответить» (Reply) на это сообщение.</i>\n"
        f"<!-- user_id:{user_id} -->"
    )

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_ticket)
        except Exception as e:
            logging.error(f"Не удалось доставить вопрос в админ-чат: {e}")

    await state.clear()

# --- ОТВЕТ АДМИНИСТРАТОРА ИЗ ГРУППЫ (REPLY НА СООБЩЕНИЕ БОТА) ---
@router.message(F.reply_to_message & (F.chat.id == ADMIN_CHAT_ID))
async def reply_from_admin(message: Message, bot: Bot):
    reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    
    # Ищем скрытый маркер user_id в тексте исходного сообщения
    if "user_id:" in reply_text:
        try:
            target_user_id = int(reply_text.split("user_id:")[1].split(" ")[0].replace("-->", "").strip())
            
            client_msg = (
                "<b>💬 Ответ от администрации базы отдыха «Русалочка»:</b>\n\n"
                f"{message.text}"
            )
            await bot.send_message(chat_id=target_user_id, text=client_msg)
            await message.reply("✅ Ответ успешно доставлен гостю!")
        except Exception as e:
            await message.reply(f"❌ Не удалось отправить ответ: {e}")

# --- РАЗДЕЛ: НАШИ НОМЕРА ---
@router.message(F.text == "🏡 Наши номера")
async def show_rooms(message: Message):
    text = (
        "<b>🏡 Номерной фонд базы отдыха «Русалочка»:</b>\n\n"
        "Нажмите на интересующую категорию, чтобы посмотреть реальные фотографии, "
        "оснащение и стоимость номеров:"
    )
    await message.answer(text, reply_markup=get_rooms_list_keyboard())

@router.callback_query(F.data == "back_to_rooms_catalog")
async def back_to_catalog(callback: CallbackQuery):
    await callback.message.delete()
    text = (
        "<b>🏡 Номерной фонд базы отдыха «Русалочка»:</b>\n\n"
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
    await send_room_media(
        message=callback.message,
        folder_path=room.get("folder", ""),
        caption=room["description"],
        reply_markup=get_single_room_keyboard()
    )
    await callback.answer()

# --- РАЗДЕЛ: ЗАБРОНИРОВАТЬ ---
@router.message(F.text == "📝 Забронировать")
async def show_booking_info(message: Message):
    text = (
        "<b>📝 Онлайн-бронирование номеров</b>\n\n"
        "В нашем официальном модуле бронирования вы можете в реальном времени выбрать удобные даты отдыха, "
        "узнать актуальное наличие свободных номеров и моментально оформить бронь с гарантией!\n\n"
        "📌 <b>Условия проживания:</b>\n"
        "• <b>Период работы:</b> с 15 июня по 15 сентября\n"
        "• <b>Заезд:</b> с 13:00 | <b>Выезд:</b> до 11:00\n"
        "• <b>Предоплата для брони:</b> 30.00% от стоимости\n"
        "• <b>Остаток:</b> оплачивается при заселении\n"
        "• <b>Бесплатная отмена:</b> возможна за 14 дней до заезда\n\n"
        "Нажмите кнопку ниже, чтобы перейти к выбору дат и категории ⬇️"
    )
    await message.answer(text, reply_markup=get_booking_page_keyboard())

# --- РАЗДЕЛ: ОТЗЫВЫ ---
@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⭐ Открыть отзывы на Яндекс.Картах", url=REVIEWS_URL)]]
    )
    await message.answer(
        "<b>⭐ Отзывы наших гостей:</b>\n\n"
        "Ознакомьтесь с реальными впечатлениями, оценками и фотографиями отдыхающих "
        "на официальной странице базы на Яндекс.Картах:",
        reply_markup=kb
    )

# --- РАЗДЕЛ: ИНФРАСТРУКТУРА И УСЛУГИ ---
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
        "Оборудованная зона отдыха с бесплатным предоставлением решеток, шампуров.\n\n"
        "🌸 <b>Зеленая зона</b>\n"
        "Зеленая территория: 350 кустов роз и 1100 кустов лаванды.\n\n"
        "------------------------------------\n\n"
        "💲 <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:</b>\n\n"
        "🎨 <b>Студия творчества и шоу</b>\n"
        "Регулярные шоу-программы и мастер-классы (создание слаймов, блеск-тату, роспись футболок, кепок и фигурок).\n\n"
        "🧺 <b>Полезный сервис</b>\n"
        "Прачечная и гладильная комната.\n"
        "Зарядная станция для электромобилей GB/T 7kwt (Цена 22₽ / 1 кВт.ч)."
    )
    await message.answer(text)

# --- РАЗДЕЛ: О БАЗЕ ---
@router.message(F.text == "🌴 О базе")
async def show_about(message: Message):
    text = (
        "<b>🌴 База отдыха «Русалочка»</b>\n\n"
        "• Закрытая охраняемая зеленая территория\n"
        "• Шаговая доступность к просторному пляжу и теплому морю\n"
        "• Детский игровой комплекс, анимация и уютная атмосфера\n"
        "• Период работы: <b>с 15 июня по 15 сентября</b>\n"
        "• Официальный сайт: https://rusalo4ka.com/"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 Открыть сайт rusalo4ka.com", url="https://rusalo4ka.com/")]]
    )
    await message.answer(text, reply_markup=kb)

# --- РАЗДЕЛ: КОНТАКТЫ И ЛОКАЦИЯ ---
@router.message(F.text == "📞 Контакты и локация")
async def show_contacts(message: Message):
    text = (
        "<b>📞 Контакты базы отдыха «Русалочка»:</b>\n\n"
        "📍 <b>Адрес:</b> Краснодарский край, г. Анапа, ст. Благовещенская, б/о «Русалочка»\n"
        "📞 <b>Отдел бронирования:</b> +7 (918) 47-74-366\n"
        "✉️ <b>E-mail:</b> anaparusalochka@rambler.ru\n"
        "🌐 <b>Сайт:</b> https://rusalo4ka.com/\n\n"
        "📍 <i>Ниже отправлена геолокация для Яндекс.Карт и навигатора:</i>"
    )
    await message.answer(text, reply_markup=get_contacts_keyboard())
    await message.answer_location(latitude=GEO_LATITUDE, longitude=GEO_LONGITUDE)

# --- РАЗДЕЛ: ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ (ТОЧЬ В ТОЧЬ С САЙТА) ---
@router.message(F.text == "❓ Вопросы и ответы (FAQ)")
async def show_faq(message: Message):
    await message.answer("<b>Часто задаваемые вопросы</b>", reply_markup=get_faq_inline_keyboard())

# ОТПРАВКА ОФИЦИАЛЬНОГО PDF-ФАЙЛА ПРАВИЛ
@router.callback_query(F.data == "faq:pdf_rules")
async def send_pdf_rules(callback: CallbackQuery):
    if os.path.exists(PDF_RULES_PATH):
        doc = FSInputFile(PDF_RULES_PATH, filename="Правила_проживания_Русалочка.pdf")
        await callback.message.answer_document(
            document=doc,
            caption="📄 <b>Официальные правила проживания на базе отдыха «Русалочка» (PDF)</b>"
        )
    else:
        await callback.message.answer(
            "📄 Документ правил обновляется. Вы также можете ознакомиться с ними на нашем сайте: https://rusalo4ka.com/"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("faq:"))
async def faq_click(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    
    faq_data = {
        "checkin": {
            "q": "Во сколько заселение?",
            "a": "— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы Вас заселим раньше."
        },
        "checkout": {
            "q": "Во сколько выселение из номера?",
            "a": "— освободить номер нужно до 11:00, ключи, брелоки и браслеты от номера нужно сдать в администрации."
        },
        "prepayment": {
            "q": "При бронировании нужно вносить предоплату?",
            "a": "— бронирование выбранной категории номера (домика) производится после перечисления предоплаты (30% от полной стоимости проживания)."
        },
        "refund": {
            "q": "Предоплата возвратная?",
            "a": "— бесплатная отмена бронирования возможна за 14 дней до забронированной даты, после - взимается 100% от размера предоплаты. В экстренном случае обращайтесь на электронную почту."
        },
        "pets": {
            "q": "Возможно размещение с животными?",
            "a": (
                "— Возможность размещения исключительно с декоративными собаками, весом до 6 кг., предусмотрена в номерах категории «Номер с кухней (апарт.)» эко.\n\n"
                "— Тариф на размещение: 800 руб./сутки.\n\n"
                "— Выгул собак на территории Базы отдыха «Русалочка» ЗАПРЕЩЕН."
            )
        }
    }

    item = faq_data.get(action)
    if not item:
        await callback.answer()
        return

    text = f"<b>{item['q']}</b>\n\n{item['a']}"

    buttons = []
    if action == "pets":
        buttons.append([InlineKeyboardButton(text="📄 Посмотреть полные правила (PDF)", callback_data="faq:pdf_rules")])
    
    buttons.append([InlineKeyboardButton(text="💬 Задать вопрос администратору", callback_data="start_feedback_fsm")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в FAQ", callback_data="faq_back_root")])

    back_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=back_kb)
    await callback.answer()

@router.callback_query(F.data == "faq_back_root")
async def faq_back_root(callback: CallbackQuery):
    await callback.message.edit_text("<b>Часто задаваемые вопросы</b>", reply_markup=get_faq_inline_keyboard())
    await callback.answer()

# =====================================================================
# ТОЧКА ВХОДА (RUNNER)
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
