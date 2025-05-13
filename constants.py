# constants.py
from telegram import ReplyKeyboardMarkup
import os

# Настройки изменения параметров
STATS_CHANGE_RATES = {
    'hunger_per_hour': 1000,
    'happiness_per_hour': -5000,
    'health_per_hour': -2000,
    'feed_hunger_reduction': 30,
    'play_happiness_increase': 20,
    'health_feed_benefit': 5,
    'health_play_benefit': 5
}

# Пути к изображениям питомцев
PET_IMAGES = {
    'кролик': 'Rabbit_portrait.png',
    'сова': 'Owl_portrait.png',
    'ёж': 'Hedgehog_portrait.png',
    'обезьянка': 'Monkey_portrait.png'
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

GAMES = ["мяч", "прятки", "догонялки", "прыжки", "головоломки"]