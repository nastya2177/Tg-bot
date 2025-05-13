from telegram import ReplyKeyboardMarkup

PET_IMAGES = {
    'кролик': 'Rabbit_portrait.png',
    'сова': 'Owl_portrait.png',
    'ёж': 'Hedgehog_portrait.png',
    'обезьянка': 'Monkey_portrait.png'
}


PET_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    [['кролик', 'сова'], ['ёж', 'обезьянка']],
    one_time_keyboard=True,
    resize_keyboard=True
)


NAME, PET_TYPE = range(2)


HEALTH_STATUSES = {
    'critical': (0, 30, "Очень плохое состояние 😱"),
    'bad': (30, 60, "Плохое состояние 😢"),
    'good': (60, 101, "Хорошее состояние 😊")
}