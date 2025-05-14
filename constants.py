from telegram import ReplyKeyboardMarkup, InputFile
import os
from pathlib import Path
from typing import Dict, Optional

# Путь к папке с изображениями
PET_IMAGES_DIR = Path("pets")


# Настройки изменения параметров
STATS_CHANGE_RATES = {
    'hunger_per_hour': 1000,
    'happiness_per_hour': -500,
    'health_per_hour': -2000,
    'feed_hunger_reduction': 3000,
    'play_happiness_increase': 20,
    'health_feed_benefit': 5,
    'health_play_benefit': 5
}

# Типы питомцев и соответствующие файлы
PET_TYPES = {
    'кролик': 'Rabbit_portrait.png',
    'сова': 'Owl_portrait.png',
    'ёж': 'Porcupine_portrait.png',
    'обезьянка': 'Monkey_portrait.png'
}

# Заранее открытые файлы изображений
PRELOADED_IMAGES: Dict[str, Optional[InputFile]] = {}

# Загружаем все изображения при импорте модуля
for pet_type, filename in PET_TYPES.items():
    image_path = PET_IMAGES_DIR / filename

    if image_path.exists():
        with open(image_path, 'rb') as f:
            PRELOADED_IMAGES[pet_type] = InputFile(f.read(), filename=filename)
    else:
        PRELOADED_IMAGES[pet_type] = None
        print(f"Warning: Image not found for {pet_type} at {image_path}")

# Полные пути к файлам (для совместимости)
PET_IMAGES = {
    pet_type: str(PET_IMAGES_DIR / filename)
    for pet_type, filename in PET_TYPES.items()
}

# Клавиатуры
PET_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    [['кролик', 'сова'], ['ёж', 'обезьянка']],
    one_time_keyboard=True,
    resize_keyboard=True
)

YES_NO_KEYBOARD = ReplyKeyboardMarkup(
    [['Да', 'Нет']],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Состояния диалога
ASK_NAME, NAME, PET_TYPE = range(3)

# Статусы здоровья
HEALTH_STATUSES = {
    'dead': (0, 1, "💀 Умер"),
    'critical': (1, 30, "Очень плохое состояние 😱"),
    'bad': (30, 60, "Плохое состояние 😢"),
    'good': (60, 101, "Хорошее состояние 😊")
}

GAMES = ["мяч", "прятки", "догонялки"]