# database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from constants import STATS_CHANGE_RATES

Base = declarative_base()

class Pet(Base):
    __tablename__ = 'pets'

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    pet_type = Column(String)
    hunger = Column(Integer, default=50)
    happiness = Column(Integer, default=50)
    health = Column(Integer, default=100)
    last_fed = Column(DateTime)
    last_played = Column(DateTime)
    created_at = Column(DateTime)
    is_alive = Column(Boolean, default=True)

class PetHistory(Base):
    __tablename__ = 'pets_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    name = Column(String)
    pet_type = Column(String)
    created_at = Column(DateTime)
    died_at = Column(DateTime)
    lifespan_seconds = Column(Float)

engine = create_engine('sqlite:///tamagotchi.db')
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def create_pet(user_id, name, pet_type):
    session = Session()
    try:
        pet = Pet(
            user_id=user_id,
            name=name,
            pet_type=pet_type,
            created_at=datetime.now(),
            is_alive=True
        )
        session.add(pet)
        session.commit()
    finally:
        session.close()

def get_pet(user_id):
    session = Session()
    try:
        pet = session.query(Pet).filter_by(user_id=user_id).first()
        if pet:
            return {
                'user_id': pet.user_id,
                'name': pet.name,
                'pet_type': pet.pet_type,
                'hunger': pet.hunger,
                'happiness': pet.happiness,
                'health': pet.health,
                'last_fed': pet.last_fed.isoformat() if pet.last_fed else None,
                'last_played': pet.last_played.isoformat() if pet.last_played else None,
                'created_at': pet.created_at.isoformat(),
                'is_alive': pet.is_alive
            }
        return None
    finally:
        session.close()

def update_pet(user_id, **kwargs):
    session = Session()
    try:
        pet = session.query(Pet).filter_by(user_id=user_id).first()
        if pet:
            for key, value in kwargs.items():
                # Преобразуем строки ISO формата в datetime, если это необходимо
                if key in ['last_fed', 'last_played'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(pet, key, value)
            session.commit()
    finally:
        session.close()

def kill_pet(user_id):
    session = Session()
    try:
        pet = session.query(Pet).filter_by(user_id=user_id).first()
        if pet:
            died_at = datetime.now()
            lifespan = (died_at - pet.created_at).total_seconds()

            pet_history = PetHistory(
                user_id=pet.user_id,
                name=pet.name,
                pet_type=pet.pet_type,
                created_at=pet.created_at,
                died_at=died_at,
                lifespan_seconds=lifespan
            )
            session.add(pet_history)
            session.delete(pet)
            session.commit()
    finally:
        session.close()

def check_pet_status(user_id):
    session = Session()
    try:
        pet = session.query(Pet).filter_by(user_id=user_id).first()
        if not pet or not pet.is_alive:
            return None

        now = datetime.now()
        last_fed = pet.last_fed if pet.last_fed else now
        last_played = pet.last_played if pet.last_played else now

        hours_since_fed = (now - last_fed).total_seconds() / 3600
        hours_since_played = (now - last_played).total_seconds() / 3600

        hunger = min(100, max(0, pet.hunger + int(STATS_CHANGE_RATES['hunger_per_hour'] * hours_since_fed)))
        happiness = min(100, max(0, pet.happiness + int(STATS_CHANGE_RATES['happiness_per_hour'] * hours_since_played)))
        health = min(100, max(0, pet.health + int(STATS_CHANGE_RATES['health_per_hour'] * (hours_since_fed + hours_since_played))))

        if health <= 0:
            session.close()
            kill_pet(user_id)
            return None

        pet.hunger = hunger
        pet.happiness = happiness
        pet.health = health
        pet.last_fed = now if hunger < pet.hunger else last_fed  # Обновляем только если голод уменьшился
        pet.last_played = now if happiness > pet.happiness else last_played  # Обновляем только если счастье увеличилось
        session.commit()

        return get_pet(user_id)
    finally:
        session.close()

def get_pets_history(user_id):
    session = Session()
    try:
        history = session.query(PetHistory).filter_by(user_id=user_id).order_by(PetHistory.died_at.desc()).all()
        return [{
            'name': item.name,
            'pet_type': item.pet_type,
            'created_at': item.created_at.isoformat(),
            'died_at': item.died_at.isoformat(),
            'lifespan_seconds': item.lifespan_seconds
        } for item in history]
    finally:
        session.close()