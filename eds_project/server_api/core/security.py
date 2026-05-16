
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

# СЕКРЕТНИЙ КЛЮЧ: Використовується для підпису самих JWT-токенів.
SECRET_KEY = "super_secret_key_for_eds_coursework"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Токен "згорить" через 2 години

# Налаштування алгоритму bcrypt для хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє, чи збігається введений пароль із хешем у базі."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Перетворює звичайний пароль на безпечний хеш."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Створює JWT-токен (перепустку) із заданими даними та терміном дії."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # Створюємо сам токен, підписаний нашим SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt