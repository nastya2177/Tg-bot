import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import BOT_TOKEN
import sqlite3
from datetime import datetime, timedelta
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

PET_TYPES = ['monkey', 'owl', 'porcupine', 'rabbit']
PET_EMOJIS = {
    'monkey': '🐵',
    'owl': '🦉',
    'porcupine': '🦔',
    'rabbit': '🐇'
}

PET_TYPE, NAME, MAIN_MENU = range(3)

HELP_TEXT = """
🐾 *Добро пожаловать в Tamagotchi Bot!* 🐾

Здесь вы можете заботиться о своих виртуальных питомцах. 

*Основные команды:*
/start - начать игру или создать нового питомца
/menu - открыть главное меню
/help - показать эту справку
/status - показать статус текущего питомца
/feed - покормить текущего питомца
/play - поиграть с текущим питомцем

*Как играть:*
1. Вы можете создать до 4 питомцев разных типов
2. Каждый питомец требует ухода - кормления и игр
3. Если не ухаживать за питомцем, его показатели будут ухудшаться
4. Вы можете переключаться между питомцами в меню

*Типы питомцев:*
- monkey 🐵
- owl 🦉
- porcupine 🦔
- rabbit 🐇

Следите за показателями своих питомцев и получайте удовольствие от игры!
"""


def init_db():
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        type TEXT,
        hunger INTEGER DEFAULT 50,
        happiness INTEGER DEFAULT 50,
        health INTEGER DEFAULT 100,
        last_fed TEXT,
        last_played TEXT,
        created_at TEXT,
        is_active INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()


def create_pet(user_id, name, pet_type):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    # Деактивируем всех предыдущих питомцев
    cursor.execute('UPDATE pets SET is_active = 0 WHERE user_id = ?', (user_id,))

    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO pets (user_id, name, type, hunger, happiness, health, last_fed, last_played, created_at, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, pet_type, 50, 50, 100, now, now, now, 1))

    conn.commit()
    conn.close()


def get_active_pet(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pets WHERE user_id = ? AND is_active = 1', (user_id,))
    pet = cursor.fetchone()

    conn.close()

    if pet:
        return {
            'id': pet[0],
            'user_id': pet[1],
            'name': pet[2],
            'type': pet[3],
            'hunger': pet[4],
            'happiness': pet[5],
            'health': pet[6],
            'last_fed': pet[7],
            'last_played': pet[8],
            'created_at': pet[9],
            'is_active': pet[10]
        }
    return None


def get_all_pets(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pets WHERE user_id = ? ORDER BY is_active DESC', (user_id,))
    pets = cursor.fetchall()

    conn.close()

    return [{
        'id': pet[0],
        'user_id': pet[1],
        'name': pet[2],
        'type': pet[3],
        'hunger': pet[4],
        'happiness': pet[5],
        'health': pet[6],
        'last_fed': pet[7],
        'last_played': pet[8],
        'created_at': pet[9],
        'is_active': pet[10]
    } for pet in pets]


def update_pet(pet_id, **kwargs):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(pet_id)

    cursor.execute(f'UPDATE pets SET {set_clause} WHERE id = ?', values)

    conn.commit()
    conn.close()


def set_active_pet(user_id, pet_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    # Деактивируем всех питомцев
    cursor.execute('UPDATE pets SET is_active = 0 WHERE user_id = ?', (user_id,))
    # Активируем выбранного
    cursor.execute('UPDATE pets SET is_active = 1 WHERE id = ?', (pet_id,))

    conn.commit()
    conn.close()


def count_pets(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM pets WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]

    conn.close()
    return count


def check_pet_status(pet_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pets WHERE id = ?', (pet_id,))
    pet = cursor.fetchone()

    if not pet:
        conn.close()
        return None

    pet_dict = {
        'id': pet[0],
        'user_id': pet[1],
        'name': pet[2],
        'type': pet[3],
        'hunger': pet[4],
        'happiness': pet[5],
        'health': pet[6],
        'last_fed': pet[7],
        'last_played': pet[8],
        'created_at': pet[9],
        'is_active': pet[10]
    }

    now = datetime.now()
    last_fed = datetime.fromisoformat(pet_dict['last_fed'])
    last_played = datetime.fromisoformat(pet_dict['last_played'])

    hours_since_fed = (now - last_fed).total_seconds() / 3600
    hours_since_played = (now - last_played).total_seconds() / 3600

    hunger = min(100, max(0, pet_dict['hunger'] + int(10 * hours_since_fed)))
    happiness = min(100, max(0, pet_dict['happiness'] - int(5 * hours_since_played)))
    health = min(100, max(0, pet_dict['health'] - int(2 * hours_since_fed) - int(2 * hours_since_played)))

    update_pet(
        pet_dict['id'],
        hunger=hunger,
        happiness=happiness,
        health=health
    )

    pet_dict.update({
        'hunger': hunger,
        'happiness': happiness,
        'health': health
    })

    conn.close()
    return pet_dict


async def start(update, context):
    user_id = update.message.from_user.id
    pets = get_all_pets(user_id)

    if pets:
        await show_main_menu(update, context)
        return MAIN_MENU
    else:
        # Показываем справку при первом запуске
        await help_command(update, context)
        await update.message.reply_text(
            "Давайте создадим вашего первого питомца!\n"
            "Сначала выберите тип питомца:",
            reply_markup=ReplyKeyboardMarkup([PET_TYPES], one_time_keyboard=True)
        )
        return PET_TYPE


async def help_command(update, context):
    await update.message.reply_text(HELP_TEXT, parse_mode='Markdown')


async def choose_pet_type(update, context):
    pet_type = update.message.text.lower()
    if pet_type not in PET_TYPES:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных типов питомцев.")
        return PET_TYPE

    context.user_data['pet_type'] = pet_type
    await update.message.reply_text(
        "Отлично! Теперь придумайте имя для вашего питомца:",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_pet_name(update, context):
    pet_name = update.message.text
    user_id = update.message.from_user.id
    pet_type = context.user_data['pet_type']

    # Проверяем, есть ли уже питомец такого типа у пользователя
    pets = get_all_pets(user_id)
    existing_types = {pet['type'] for pet in pets}

    if pet_type in existing_types:
        await update.message.reply_text(
            f"У вас уже есть питомец типа {pet_type}. Пожалуйста, начните заново с /start."
        )
        return ConversationHandler.END

    if len(pets) >= 4:
        await update.message.reply_text(
            "У вас уже максимальное количество питомцев (4). Вы не можете создать больше."
        )
        return ConversationHandler.END

    create_pet(user_id, pet_name, pet_type)
    emoji = PET_EMOJIS.get(pet_type, '🐾')

    await update.message.reply_text(
        f"Поздравляю! Вы завели нового {pet_type} по имени {pet_name}! {emoji}\n"
        "Используйте /menu для управления питомцами."
    )

    await show_main_menu(update, context)
    return MAIN_MENU


async def show_main_menu(update, context):
    user_id = update.message.from_user.id
    pets = get_all_pets(user_id)
    active_pet = next((pet for pet in pets if pet['is_active']), None)

    if not pets:
        await update.message.reply_text("У вас нет питомцев. Используйте /start чтобы создать первого.")
        return

    if not active_pet and pets:
        set_active_pet(user_id, pets[0]['id'])
        active_pet = pets[0]

    emoji = PET_EMOJIS.get(active_pet['type'], '🐾')
    pet_info = (
        f"Текущий питомец: {active_pet['name']} ({active_pet['type']}) {emoji}\n"
        f"Голод: {active_pet['hunger']}/100\n"
        f"Счастье: {active_pet['happiness']}/100\n"
        f"Здоровье: {active_pet['health']}/100"
    )

    keyboard = [
        ['🍔 Покормить', '🎾 Поиграть'],
        ['📊 Статус', '🔄 Сменить питомца'],
        ['➕ Новый питомец']
    ]

    if len(pets) >= 4:
        keyboard[2] = []

    await update.message.reply_text(
        pet_info,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )


async def main_menu_handler(update, context):
    text = update.message.text
    user_id = update.message.from_user.id
    active_pet = get_active_pet(user_id)

    if not active_pet:
        await update.message.reply_text("У вас нет активного питомца.")
        return MAIN_MENU

    if text == '🍔 Покормить':
        await feed(update, context)
    elif text == '🎾 Поиграть':
        await play(update, context)
    elif text == '📊 Статус':
        await status(update, context)
    elif text == '🔄 Сменить питомца':
        await switch_pet(update, context)
        return MAIN_MENU
    elif text == '➕ Новый питомец':
        if count_pets(user_id) >= 4:
            await update.message.reply_text("У вас уже максимальное количество питомцев (4).")
            await show_main_menu(update, context)
            return MAIN_MENU
        else:
            await update.message.reply_text(
                "Выберите тип нового питомца:",
                reply_markup=ReplyKeyboardMarkup([PET_TYPES], one_time_keyboard=True)
            )
            return PET_TYPE

    await show_main_menu(update, context)
    return MAIN_MENU


async def status(update, context):
    user_id = update.message.from_user.id
    active_pet = get_active_pet(user_id)

    if not active_pet:
        await update.message.reply_text("У вас нет активного питомца.")
        return

    pet = check_pet_status(active_pet['id'])

    if pet['health'] < 30:
        status_msg = "Очень плохое состояние 😱"
    elif pet['health'] < 60:
        status_msg = "Плохое состояние 😢"
    else:
        status_msg = "Хорошее состояние 😊"

    emoji = PET_EMOJIS.get(pet['type'], '🐾')
    await update.message.reply_text(
        f"Имя: {pet['name']} ({pet['type']}) {emoji}\n"
        f"Голод: {pet['hunger']}/100\n"
        f"Счастье: {pet['happiness']}/100\n"
        f"Здоровье: {pet['health']}/100\n"
        f"Состояние: {status_msg}"
    )


async def feed(update, context):
    user_id = update.message.from_user.id
    active_pet = get_active_pet(user_id)

    if not active_pet:
        await update.message.reply_text("У вас нет активного питомца.")
        return

    pet = check_pet_status(active_pet['id'])
    now = datetime.now().isoformat()
    hunger = max(0, pet['hunger'] - 30)

    update_pet(
        pet['id'],
        hunger=hunger,
        last_fed=now
    )

    emoji = PET_EMOJIS.get(pet['type'], '🐾')
    await update.message.reply_text(f"Вы покормили {pet['name']} ({pet['type']})! 🍔 {emoji}")


async def play(update, context):
    user_id = update.message.from_user.id
    active_pet = get_active_pet(user_id)

    if not active_pet:
        await update.message.reply_text("У вас нет активного питомца.")
        return

    pet = check_pet_status(active_pet['id'])
    now = datetime.now().isoformat()
    happiness = min(100, pet['happiness'] + 20)

    update_pet(
        pet['id'],
        happiness=happiness,
        last_played=now
    )

    games = ["мяч", "прятки", "догонялки"]
    game = random.choice(games)
    emoji = PET_EMOJIS.get(pet['type'], '🐾')

    await update.message.reply_text(f"Вы поиграли с {pet['name']} ({pet['type']}) в {game}! 🎾 {emoji}")


async def switch_pet(update, context):
    user_id = update.message.from_user.id
    pets = get_all_pets(user_id)

    if len(pets) <= 1:
        await update.message.reply_text("У вас только один питомец.")
        await show_main_menu(update, context)
        return MAIN_MENU

    keyboard = []
    for pet in pets:
        emoji = PET_EMOJIS.get(pet['type'], '🐾')
        status = "✅" if pet['is_active'] else ""
        keyboard.append([f"{status} {pet['name']} ({pet['type']}) {emoji}"])

    await update.message.reply_text(
        "Выберите питомца:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

    return 'SELECT_PET'


async def select_pet(update, context):
    user_id = update.message.from_user.id
    pets = get_all_pets(user_id)
    selected = update.message.text

    for pet in pets:
        emoji = PET_EMOJIS.get(pet['type'], '🐾')
        pet_str = f"{pet['name']} ({pet['type']}) {emoji}"
        if pet_str in selected:
            set_active_pet(user_id, pet['id'])
            await update.message.reply_text(
                f"Теперь ваш активный питомец - {pet['name']}!",
                reply_markup=ReplyKeyboardRemove()
            )
            await show_main_menu(update, context)
            return MAIN_MENU

    await update.message.reply_text("Питомец не найден. Попробуйте еще раз.")
    return 'SELECT_PET'


async def menu(update, context):
    await show_main_menu(update, context)
    return MAIN_MENU


async def cancel(update, context):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('menu', menu)],
        states={
            PET_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_pet_type)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_name)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            'SELECT_PET': [MessageHandler(filters.TEXT & ~filters.COMMAND, select_pet)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()


if __name__ == '__main__':
    main()