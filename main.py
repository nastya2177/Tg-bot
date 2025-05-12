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

NAME, PLAY = range(2)


def init_db():
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pets (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        hunger INTEGER DEFAULT 50,
        happiness INTEGER DEFAULT 50,
        health INTEGER DEFAULT 100,
        last_fed TEXT,
        last_played TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()


def create_pet(user_id, name):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO pets (user_id, name, hunger, happiness, health, last_fed, last_played, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, 50, 50, 100, now, now, now))

    conn.commit()
    conn.close()



def get_pet(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,))
    pet = cursor.fetchone()

    conn.close()

    if pet:
        return {
            'user_id': pet[0],
            'name': pet[1],
            'hunger': pet[2],
            'happiness': pet[3],
            'health': pet[4],
            'last_fed': pet[5],
            'last_played': pet[6],
            'created_at': pet[7]
        }
    return None


# Функция для обновления состояния питомца
def update_pet(user_id, **kwargs):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(user_id)

    cursor.execute(f'UPDATE pets SET {set_clause} WHERE user_id = ?', values)

    conn.commit()
    conn.close()


def check_pet_status(user_id):
    pet = get_pet(user_id)
    if not pet:
        return None

    now = datetime.now()
    last_fed = datetime.fromisoformat(pet['last_fed'])
    last_played = datetime.fromisoformat(pet['last_played'])

    hours_since_fed = (now - last_fed).total_seconds() / 3600
    hours_since_played = (now - last_played).total_seconds() / 3600

    hunger = min(100, max(0, pet['hunger'] + int(10 * hours_since_fed)))
    happiness = min(100, max(0, pet['happiness'] - int(5 * hours_since_played)))

    health = min(100, max(0, pet['health'] - int(2 * hours_since_fed) - int(2 * hours_since_played)))

    update_pet(
        user_id,
        hunger=hunger,
        happiness=happiness,
        health=health
    )

    return get_pet(user_id)


async def start(update, context):
    user_id = update.message.from_user.id
    pet = get_pet(user_id)

    if pet:
        await update.message.reply_text(
            f"У вас уже есть питомец по имени {pet['name']}!\n"
            "Используйте /status чтобы проверить его состояние или /play чтобы поиграть с ним."
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Привет! Это виртуальный питомец Тамагочи.\n"
            "Как вы хотите назвать своего питомца?"
        )
        return NAME



async def get_pet_name(update, context):
    pet_name = update.message.text
    user_id = update.message.from_user.id

    create_pet(user_id, pet_name)

    await update.message.reply_text(
        f"Поздравляю! Вы завели нового питомца по имени {pet_name}!\n"
        "Используйте /feed чтобы покормить его, /play чтобы поиграть, /status чтобы проверить его состояние."
    )

    return ConversationHandler.END



async def status(update, context):
    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        await update.message.reply_text("У вас еще нет питомца. Используйте /start чтобы создать его.")
        return

    if pet['health'] < 30:
        status_msg = "Очень плохое состояние 😱"
    elif pet['health'] < 60:
        status_msg = "Плохое состояние 😢"
    else:
        status_msg = "Хорошее состояние 😊"

    await update.message.reply_text(
        f"Имя: {pet['name']}\n"
        f"Голод: {pet['hunger']}/100\n"
        f"Счастье: {pet['happiness']}/100\n"
        f"Здоровье: {pet['health']}/100\n"
        f"Состояние: {status_msg}"
    )


async def feed(update, context):
    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        await update.message.reply_text("У вас еще нет питомца. Используйте /start чтобы создать его.")
        return

    now = datetime.now().isoformat()
    hunger = max(0, pet['hunger'] - 30)

    update_pet(
        user_id,
        hunger=hunger,
        last_fed=now
    )

    await update.message.reply_text(f"Вы покормили {pet['name']}! 🍔")



async def play(update, context):

    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        await update.message.reply_text("У вас еще нет питомца. Используйте /start чтобы создать его.")
        return

    now = datetime.now().isoformat()
    happiness = min(100, pet['happiness'] + 20)

    update_pet(
        user_id,
        happiness=happiness,
        last_played=now
    )

    games = ["мяч", "прятки", "догонялки"]
    game = random.choice(games)

    await update.message.reply_text(f"Вы поиграли с {pet['name']} в {game}! 🎾")



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
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("play", play))

    application.run_polling()


if __name__ == '__main__':
    main()