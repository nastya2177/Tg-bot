# database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from constants import STATS_CHANGE_RATES
import os
from typing import Dict, Any

# Настройка подключения к PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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


# Создаем engine с пулом подключений
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Генератор сессий для FastAPI (если будете использовать)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных (создание таблиц)"""
    Base.metadata.create_all(bind=engine)


def create_pet(user_id: int, name: str, pet_type: str) -> None:
    """Создание нового питомца"""
    db = SessionLocal()
    try:
        pet = Pet(
            user_id=user_id,
            name=name,
            pet_type=pet_type,
            created_at=datetime.now(),
            is_alive=True
        )
        db.add(pet)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_pet(user_id: int) -> Dict[str, Any]:
    """Получение информации о питомце"""
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.user_id == user_id).first()
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
        db.close()


def update_pet(user_id: int, **kwargs: Any) -> None:
    """Обновление данных питомца"""
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.user_id == user_id).first()
        if pet:
            for key, value in kwargs.items():
                if key in ['last_fed', 'last_played'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(pet, key, value)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def kill_pet(user_id: int) -> None:
    """Удаление питомца и добавление в историю"""
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.user_id == user_id).first()
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
            db.add(pet_history)
            db.delete(pet)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def check_pet_status(user_id: int) -> Dict[str, Any]:
    """Проверка и обновление статуса питомца"""
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.user_id == user_id).first()
        if not pet or not pet.is_alive:
            return None

        now = datetime.now()
        last_fed = pet.last_fed if pet.last_fed else now
        last_played = pet.last_played if pet.last_played else now

        hours_since_fed = (now - last_fed).total_seconds() / 3600
        hours_since_played = (now - last_played).total_seconds() / 3600

        hunger = min(100, max(0, pet.hunger + int(STATS_CHANGE_RATES['hunger_per_hour'] * hours_since_fed)))
        happiness = min(100, max(0, pet.happiness + int(STATS_CHANGE_RATES['happiness_per_hour'] * hours_since_played)))
        health = min(100, max(0, pet.health + int(
            STATS_CHANGE_RATES['health_per_hour'] * (hours_since_fed + hours_since_played))))

        if health <= 0:
            db.close()
            kill_pet(user_id)
            return None

        pet.hunger = hunger
        pet.happiness = happiness
        pet.health = health
        pet.last_fed = now if hunger < pet.hunger else last_fed
        pet.last_played = now if happiness > pet.happiness else last_played

        db.commit()
        return get_pet(user_id)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_pets_history(user_id: int) -> list:
    """Получение истории питомцев"""
    db = SessionLocal()
    try:
        history = db.query(PetHistory) \
            .filter(PetHistory.user_id == user_id) \
            .order_by(PetHistory.died_at.desc()) \
            .all()

        return [{
            'name': item.name,
            'pet_type': item.pet_type,
            'created_at': item.created_at.isoformat(),
            'died_at': item.died_at.isoformat(),
            'lifespan_seconds': item.lifespan_seconds
        } for item in history]
    finally:
        db.close()