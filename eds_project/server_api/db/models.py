from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # Тут ми будемо зберігається публічний ключ (.pem), який ти генеруєтсья локально
    public_key_pem = Column(Text, nullable=True)

    # Зв'язки з іншими таблицями
    documents = relationship("Document", back_populates="owner")
    signatures = relationship("Signature", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    # Зберігаємо хеш документа для гарантії того, що файл не був підмінений
    file_hash = Column(String, unique=True, index=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    signatures = relationship("Signature", back_populates="document")


class Signature(Base):
    """Таблиця журналу аудиту (Non-repudiation)"""
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Зберігаємо сам підпис (байти, конвертовані у Base64)
    signature_data = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_valid = Column(Boolean, default=True)

    document = relationship("Document", back_populates="signatures")
    user = relationship("User", back_populates="signatures")