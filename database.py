# database.py
import sqlite3
from datetime import datetime
from constants import STATS_CHANGE_RATES

def init_db():
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    # Таблица текущих питомцев
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pets (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        pet_type TEXT,
        hunger INTEGER DEFAULT 50,
        happiness INTEGER DEFAULT 50,
        health INTEGER DEFAULT 100,
        last_fed TEXT,
        last_played TEXT,
        created_at TEXT,
        is_alive INTEGER DEFAULT 1
    )
    ''')

    # Таблица истории питомцев
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pets_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        pet_type TEXT,
        created_at TEXT,
        died_at TEXT,
        lifespan_seconds INTEGER
    )
    ''')

    conn.commit()
    conn.close()

def create_pet(user_id, name, pet_type):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO pets (user_id, name, pet_type, created_at, is_alive)
    VALUES (?, ?, ?, ?, 1)
    ''', (user_id, name, pet_type, now))

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
            'pet_type': pet[2],
            'hunger': pet[3],
            'happiness': pet[4],
            'health': pet[5],
            'last_fed': pet[6],
            'last_played': pet[7],
            'created_at': pet[8],
            'is_alive': pet[9]
        }
    return None

def update_pet(user_id, **kwargs):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(user_id)

    cursor.execute(f'UPDATE pets SET {set_clause} WHERE user_id = ?', values)

    conn.commit()
    conn.close()

def kill_pet(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    # Получаем данные питомца
    cursor.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,))
    pet = cursor.fetchone()

    if pet:
        created_at = datetime.fromisoformat(pet[8])
        died_at = datetime.now()
        lifespan = (died_at - created_at).total_seconds()

        # Добавляем в историю
        cursor.execute('''
        INSERT INTO pets_history (user_id, name, pet_type, created_at, died_at, lifespan_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (pet[0], pet[1], pet[2], pet[8], died_at.isoformat(), lifespan))

        # Удаляем из текущих питомцев
        cursor.execute('DELETE FROM pets WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

def check_pet_status(user_id):
    pet = get_pet(user_id)
    if not pet or not pet['is_alive']:
        return None

    now = datetime.now()
    last_fed = datetime.fromisoformat(pet['last_fed']) if pet['last_fed'] else now
    last_played = datetime.fromisoformat(pet['last_played']) if pet['last_played'] else now

    hours_since_fed = (now - last_fed).total_seconds() / 3600
    hours_since_played = (now - last_played).total_seconds() / 3600

    hunger = min(100, max(0, pet['hunger'] + int(STATS_CHANGE_RATES['hunger_per_hour'] * hours_since_fed)))
    happiness = min(100, max(0, pet['happiness'] + int(STATS_CHANGE_RATES['happiness_per_hour'] * hours_since_played)))
    health = min(100, max(0, pet['health'] + int(STATS_CHANGE_RATES['health_per_hour'] * (hours_since_fed + hours_since_played))))

    # Проверяем смерть питомца
    if health <= 0:
        kill_pet(user_id)
        return None

    update_pet(
        user_id,
        hunger=hunger,
        happiness=happiness,
        health=health,
        last_fed=last_fed.isoformat(),
        last_played=last_played.isoformat()
    )

    return get_pet(user_id)

def get_pets_history(user_id):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT name, pet_type, created_at, died_at, lifespan_seconds 
    FROM pets_history 
    WHERE user_id = ?
    ORDER BY died_at DESC
    ''', (user_id,))

    history = cursor.fetchall()
    conn.close()

    return [{
        'name': item[0],
        'pet_type': item[1],
        'created_at': item[2],
        'died_at': item[3],
        'lifespan_seconds': item[4]
    } for item in history]