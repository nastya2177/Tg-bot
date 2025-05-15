import logging
import random
from datetime import datetime, timedelta
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardRemove, InputFile

from database import init_db, create_pet, get_pet, check_pet_status, update_pet, get_pets_history
from constants import (PET_IMAGES, PET_TYPE_KEYBOARD, YES_NO_KEYBOARD,
                       ASK_NAME, NAME, PET_TYPE, HEALTH_STATUSES, STATS_CHANGE_RATES, GAMES, PRELOADED_IMAGES )

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

import os
from telegram.ext import Updater

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def start(update, context):
    user_id = update.message.from_user.id
    pet = get_pet(user_id)

    if pet:
        await update.message.reply_text(
            f"У вас уже есть питомец по имени {pet['name']} ({pet['pet_type']})!\n"
            "Используйте /status чтобы проверить его состояние, /feed чтобы покормить или /play чтобы поиграть с ним."
        )
        return ConversationHandler.END
    else:
        history = get_pets_history(user_id)
        if history:
            await update.message.reply_text(
                "Ваш предыдущий питомец умер... Хотите завести нового?",
                reply_markup=YES_NO_KEYBOARD
            )
            return ASK_NAME
        else:
            await update.message.reply_text(
                "Привет! Это виртуальный питомец Тамагочи.\n"
                "Как вы хотите назвать своего питомца?"
            )
            return NAME


async def handle_new_pet_question(update, context):
    answer = update.message.text.lower()

    if answer == 'нет':
        await update.message.reply_text(
            "Хорошо, когда захотите завести нового питомца - используйте /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    elif answer == 'да':
        await update.message.reply_text(
            "Отлично! Как вы хотите назвать нового питомца?",
            reply_markup=ReplyKeyboardRemove()
        )
        return NAME
    else:
        await update.message.reply_text(
            "Пожалуйста, ответьте 'Да' или 'Нет'",
            reply_markup=YES_NO_KEYBOARD
        )
        return ASK_NAME


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

    if pet_type not in PRELOADED_IMAGES:
        await update.message.reply_text(
            "Пожалуйста, выберите тип питомца из предложенных вариантов.",
            reply_markup=PET_TYPE_KEYBOARD
        )
        return PET_TYPE

    create_pet(user_id, pet_name, pet_type)

    photo = PRELOADED_IMAGES[pet_type]
    if photo:
        try:
            await update.message.reply_photo(
                photo=photo,
                caption=f"Поздравляю! У Вас теперь есть {pet_type} по имени {pet_name}!\n"
                       "Используйте /feed чтобы покормить его, /play чтобы поиграть, /status чтобы проверить его состояние.",
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            await send_text_response(update, pet_type, pet_name)
    else:
        await send_text_response(update, pet_type, pet_name)

    return ConversationHandler.END

async def send_text_response(update, pet_type, pet_name):
    await update.message.reply_text(
        f"Поздравляю! У Вас теперь есть {pet_type} по имени {pet_name}!\n"
        "Используйте /feed чтобы покормить его, /play чтобы поиграть, /status чтобы проверить его состояние.",
        reply_markup=ReplyKeyboardRemove()
    )


async def status(update, context):
    user_id = update.message.from_user.id
    pet = check_pet_status(user_id)

    if not pet:
        history = get_pets_history(user_id)
        if history:
            last_pet = history[0]
            lifespan = str(timedelta(seconds=int(last_pet['lifespan_seconds'])))
            await update.message.reply_text(
                f"Ваш питомец {last_pet['name']} ({last_pet['pet_type']}) умер...\n"
                f"Он прожил: {lifespan}\n"
                "Используйте /start чтобы завести нового питомца или /history чтобы посмотреть историю."
            )
        else:
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
        history = get_pets_history(user_id)
        if history:
            last_pet = history[0]
            lifespan = str(timedelta(seconds=int(last_pet['lifespan_seconds'])))
            await update.message.reply_text(
                f"Ваш питомец {last_pet['name']} ({last_pet['pet_type']}) умер...\n"
                f"Он прожил: {lifespan}\n"
                "Используйте /start чтобы завести нового питомца или /history чтобы посмотреть историю."
            )
        else:
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
        history = get_pets_history(user_id)
        if history:
            last_pet = history[0]
            lifespan = str(timedelta(seconds=int(last_pet['lifespan_seconds'])))
            await update.message.reply_text(
                f"Ваш питомец {last_pet['name']} ({last_pet['pet_type']}) умер...\n"
                f"Он прожил: {lifespan}\n"
                "Используйте /start чтобы завести нового питомца или /history чтобы посмотреть историю."
            )
        else:
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
        f"{pet['name']} поиграл с Вами в {game}! 🎾 "
    )


async def history(update, context):
    user_id = update.message.from_user.id
    history = get_pets_history(user_id)

    if not history:
        await update.message.reply_text("У вас еще не было питомцев. Используйте /start чтобы создать первого.")
        return

    message = "История ваших питомцев:\n\n"
    for i, pet in enumerate(history, 1):
        lifespan = str(timedelta(seconds=int(pet['lifespan_seconds'])))
        message += (
            f"{i}. {pet['name']} ({pet['pet_type']})\n"
            f"   Создан: {datetime.fromisoformat(pet['created_at']).strftime('%Y-%m-%d %H:%M')}\n"
            f"   Умер: {datetime.fromisoformat(pet['died_at']).strftime('%Y-%m-%d %H:%M')}\n"
            f"   Прожил: {lifespan}\n\n"
        )

    await update.message.reply_text(message)


async def cancel(update, context):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def help_command(update, context):
    try:
        with open('help.txt', 'r', encoding='utf-8') as file:
            help_text = file.read().format(
                feed_health=STATS_CHANGE_RATES['health_feed_benefit'],
                play_health=STATS_CHANGE_RATES['health_play_benefit']
            )
    except Exception as e:
        logger.error(f"Ошибка при чтении файла help.txt: {e}")
        help_text = "Извините, не удалось загрузить справочную информацию."

    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_pet_question)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_name)],
            PET_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()