import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

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
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()

def create_pet(user_id, name, pet_type):
    conn = sqlite3.connect('tamagotchi.db')
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO pets (user_id, name, pet_type, hunger, happiness, health, last_fed, last_played, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, pet_type, 50, 50, 100, now, now, now))

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
            'created_at': pet[8]
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