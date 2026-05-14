# server_api/endpoints_auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from db import models
from db.database import SessionLocal
from core import security

# Створюємо роутер, щоб згрупувати всі маршрути авторизації
router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- СХЕМИ PYDANTIC (Для перевірки вхідних/вихідних даних) ---

class UserCreate(BaseModel):
    username: str
    password: str
    public_key_pem: Optional[str] = None  # Публічний ключ (байти у вигляді тексту)


class Token(BaseModel):
    access_token: str
    token_type: str


# --- ЗАЛЕЖНІСТЬ ДЛЯ БАЗИ ДАНИХ ---

def get_db():
    """Відкриває і закриває сесію з базою даних для кожного запиту"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- ЕНДПОІНТИ ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Реєстрація нового користувача в системі СЕД."""

    # 1. Перевіряємо, чи немає вже такого логіну
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Користувач з таким логіном вже існує")

    # 2. Хешуємо пароль
    hashed_pwd = security.get_password_hash(user_data.password)

    # 3. Створюємо запис у базі
    new_user = models.User(
        username=user_data.username,
        password_hash=hashed_pwd,
        public_key_pem=user_data.public_key_pem
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Отримуємо з бази згенерований ID

    return {"message": "Користувача успішно зареєстровано", "user_id": new_user.id}


@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Авторизація користувача.
    Використовує стандартний формат OAuth2, що ідеально працює зі Swagger UI.
    """

    # 1. Шукаємо користувача
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # 2. Перевіряємо, чи існує користувач і чи сходиться пароль
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Генеруємо JWT токен (перепустку)
    access_token = security.create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.delete("/users/{user_id}", tags=["Admin"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Видалення користувача з бази даних (Адмін-функція)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Видаляємо пов'язані документи та підписи, щоб не було помилок цілісності
    db.query(models.Signature).filter(models.Signature.user_id == user_id).delete()
    db.query(models.Document).filter(models.Document.owner_id == user_id).delete()

    db.delete(user)
    db.commit()

    return {"message": f"Користувача з ID {user_id} та всі його дані успішно видалено"}