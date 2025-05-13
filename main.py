# bot.py
import logging
import random
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardRemove, InputFile
from config import BOT_TOKEN
from database import init_db, create_pet, get_pet, check_pet_status, update_pet
from constants import (PET_IMAGES_PRELOADED, PET_TYPE_KEYBOARD,
                       NAME, PET_TYPE, HEALTH_STATUSES, STATS_CHANGE_RATES, GAMES)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    user_id = update.message.from_user.id
    pet = get_pet(user_id)

    if pet:
        await update.message.reply_text(
            f"У вас уже есть питомец по имени {pet['name']} ({pet['pet_type']})!\n"
            "Используйте /status чтобы проверить его состояние, /feed чтобы покормить /play чтобы поиграть с ним."
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
    context.user_data['pet_name'] = pet_name

    await update.message.reply_text(
        "Теперь выберите тип питомца:",
        reply_markup=PET_TYPE_KEYBOARD
    )
    return PET_TYPE


async def get_pet_type(update, context):
    pet_type = update.message.text
    pet_name = context.user_data['pet_name']
    user_id = update.message.from_user.id

    if pet_type not in PET_IMAGES_PRELOADED:
        await update.message.reply_text(
            "Пожалуйста, выберите тип питомца из предложенных вариантов.",
            reply_markup=PET_TYPE_KEYBOARD
        )
        return PET_TYPE

    create_pet(user_id, pet_name, pet_type)

    # Отправляем предзагруженное изображение
    if pet_type in PET_IMAGES_PRELOADED:
        photo = PET_IMAGES_PRELOADED[pet_type]
        photo.seek(0)  # Перематываем файл в начало
        await update.message.reply_photo(
            photo=InputFile(photo),
            caption=f"Поздравляю! Вы завели нового {pet_type} по имени {pet_name}!\n"
                    "Используйте /feed чтобы покормить его, /play чтобы поиграть, /status чтобы проверить его состояние.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            f"Поздравляю! Вы завели нового {pet_type} по имени {pet_name}!\n"
            "Используйте /feed чтобы покормить его, /play чтобы поиграть, /status чтобы проверить его состояние.",
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END


async def status(update, context):
    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        await update.message.reply_text("У вас еще нет питомца. Используйте /start чтобы создать его.")
        return

    status_msg = ""
    for status_range in HEALTH_STATUSES.values():
        if status_range[0] <= pet['health'] < status_range[1]:
            status_msg = status_range[2]
            break

    await update.message.reply_text(
        f"Имя: {pet['name']} ({pet['pet_type']})\n"
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
    hunger = max(0, pet['hunger'] - STATS_CHANGE_RATES['feed_hunger_reduction'])
    health = min(100, pet['health'] + STATS_CHANGE_RATES['health_feed_benefit'])

    update_pet(
        user_id,
        hunger=hunger,
        health=health,
        last_fed=now
    )

    await update.message.reply_text(
        f"{pet['name']} покормлен! 🍔")


async def play(update, context):
    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        await update.message.reply_text("У вас еще нет питомца. Используйте /start чтобы создать его.")
        return

    now = datetime.now().isoformat()
    happiness = min(100, pet['happiness'] + STATS_CHANGE_RATES['play_happiness_increase'])
    health = min(100, pet['health'] + STATS_CHANGE_RATES['health_play_benefit'])

    update_pet(
        user_id,
        happiness=happiness,
        health=health,
        last_played=now
    )

    game = random.choice(GAMES)
    await update.message.reply_text(
        f"{pet['name']} поиграла с Вами в {game}! 🎾 "
    )


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
            PET_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("play", play))

    application.run_polling()


if __name__ == '__main__':
    from datetime import datetime

    main()