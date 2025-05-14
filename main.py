import logging
import random
import os
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove, InputFile
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    CommandHandler,
    ConversationHandler,
    ContextTypes
)

# Импорт из других файлов проекта
from database import init_db, create_pet, get_pet, check_pet_status, update_pet, get_pets_history
from constants import (PET_IMAGES, PET_TYPE_KEYBOARD, YES_NO_KEYBOARD,
                       ASK_NAME, NAME, PET_TYPE, HEALTH_STATUSES, STATS_CHANGE_RATES, GAMES, PRELOADED_IMAGES)

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



async def post_init(application: Application) -> None:
    """Настройка вебхука при запуске"""
    webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook"
    await application.bot.set_webhook(
        webhook_url,
        secret_token=os.getenv('WEBHOOK_SECRET'),
        drop_pending_updates=True
    )
    logger.info(f"Вебхук установлен на: {webhook_url}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.message.from_user.id
    pet = get_pet(user_id)

    if pet:
        await update.message.reply_text(
            f"У вас уже есть питомец по имени {pet['name']} ({pet['pet_type']})!\n"
            "Используйте /status чтобы проверить его состояние."
        )
        return ConversationHandler.END

    history = get_pets_history(user_id)
    if history:
        await update.message.reply_text(
            "Ваш предыдущий питомец умер... Хотите завести нового?",
            reply_markup=YES_NO_KEYBOARD
        )
        return ASK_NAME

    await update.message.reply_text(
        "Привет! Это виртуальный питомец Тамагочи.\n"
        "Как вы хотите назвать своего питомца?"
    )
    return NAME


# ... (все остальные обработчики остаются БЕЗ изменений)
# Добавьте сюда все ваши существующие обработчики:
# handle_new_pet_question, get_pet_name, get_pet_type,
# status, feed, play, history, cancel, help_command
# Они могут оставаться точно такими же, как у вас были

def main():
    # Проверка обязательных переменных окружения
    required_vars = {
        'BOT_TOKEN': 'Токен бота от @BotFather',
        'DATABASE_URL': 'Строка подключения к PostgreSQL',
        'RENDER_SERVICE_NAME': 'Имя вашего сервиса на Render'
    }

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Не хватает переменных окружения: {missing_vars}")
        logger.info("Необходимо установить в настройках Render:")
        for var, desc in required_vars.items():
            logger.info(f"{var}: {desc}")
        return

    # Инициализация базы данных
    init_db()

    # Создание и настройка приложения
    application = Application.builder() \
        .token(os.getenv('BOT_TOKEN')) \
        .post_init(post_init) \
        .build()

    # Настройка обработчиков команд
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

    # Запуск бота в режиме вебхука
    try:
        port = int(os.getenv('PORT', 5000))
        logger.info(f"Запуск бота на порту {port}")

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook",
            secret_token=os.getenv('WEBHOOK_SECRET', 'default-secret'),
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")


if __name__ == '__main__':
    main()