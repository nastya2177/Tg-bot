# constants.py
from telegram import ReplyKeyboardMarkup
from PIL import Image
import os

# Настройки изменения параметров
STATS_CHANGE_RATES = {
    'hunger_per_hour': 10,  # Скорость увеличения голода в час
    'happiness_per_hour': -5,  # Скорость уменьшения счастья в час
    'health_per_hour': -2,  # Скорость ухудшения здоровья в час

    'feed_hunger_reduction': 30,  # Сколько утоляется голод за кормление
    'play_happiness_increase': 20,  # Сколько добавляется счастья за игру

    'health_feed_benefit': 5,  # Польза для здоровья от кормления
    'health_play_benefit': 5  # Польза для здоровья от игры
}

# Пути к изображениям питомцев
PET_IMAGES = {
    'кролик': 'Rabbit_portrait.png',
    'сова': 'Owl_portrait.png',
    'ёж': 'Hedgehog_portrait.png',
    'обезьянка': 'Monkey_portrait.png'
}

# Предзагружаем изображения
PET_IMAGES_PRELOADED = {}
for pet_type, filename in PET_IMAGES.items():
    if os.path.exists(filename):
        PET_IMAGES_PRELOADED[pet_type] = open(filename, 'rb')

# Клавиатура для выбора типа питомца
PET_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    [['кролик', 'сова'], ['ёж', 'обезьянка']],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Состояния диалога
NAME, PET_TYPE = range(2)

# Статусы здоровья
HEALTH_STATUSES = {
    'critical': (0, 30, "Очень плохое состояние 😱"),
    'bad': (30, 60, "Плохое состояние 😢"),
    'good': (60, 101, "Хорошее состояние 😊")
}

# Игры для команды play
GAMES = ["мяч", "прятки", "догонялки", "прыжки", "головоломки"]