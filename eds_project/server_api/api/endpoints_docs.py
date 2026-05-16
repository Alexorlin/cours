from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
import hashlib
import base64

from db import models
from db.database import SessionLocal
from core.security import SECRET_KEY, ALGORITHM
from core.verify_logic import verify_signature

router = APIRouter(prefix="/docs", tags=["Documents"])

# Ця змінна каже FastAPI, що для доступу сюди потрібен JWT токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Розшифровує токен і знаходить користувача в базі."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Невалідний токен")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Невалідний токен")

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Користувача не знайдено")
    return user


@router.post("/verify-and-save")
async def verify_and_save_document(
        file: UploadFile = File(...),
        signature_file: UploadFile = File(...),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Приймає документ та його ЕЦП.
    Перевіряє криптографічну цілісність та робить запис у журнал аудиту.
    """
    # 1. Читаємо байти завантажених файлів
    doc_bytes = await file.read()
    sig_bytes = await signature_file.read()

    # 2. Перевіряємо, чи є у користувача публічний ключ у базі
    if not current_user.public_key_pem:
        raise HTTPException(status_code=400, detail="У вас не завантажено публічний ключ")

    # 3. КРИПТОГРАФІЧНА ПЕРЕВІРКА
    is_valid = verify_signature(doc_bytes, sig_bytes, current_user.public_key_pem.encode('utf-8'))

    if not is_valid:
        raise HTTPException(status_code=400, detail="❌ ПІДПИС НЕДІЙСНИЙ або документ було змінено!")

    # 4. РЕЄСТРАЦІЯ ДОКУМЕНТА В БАЗІ (якщо він дійсний)
    file_hash = hashlib.sha256(doc_bytes).hexdigest()

    # Шукаємо, чи завантажували вже цей документ
    db_doc = db.query(models.Document).filter(models.Document.file_hash == file_hash).first()
    if not db_doc:
        db_doc = models.Document(filename=file.filename, file_hash=file_hash, owner_id=current_user.id)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

    # 5. ЖУРНАЛ АУДИТУ (зберігаємо сам факт підпису)
    new_sig = models.Signature(
        document_id=db_doc.id,
        user_id=current_user.id,
        signature_data=base64.b64encode(sig_bytes).decode('utf-8'),  # Зберігаємо байти як текст
        is_valid=True
    )
    db.add(new_sig)
    db.commit()

    return {"status": "success", "message": f"✅ Документ '{file.filename}' успішно перевірено та збережено в реєстр!"}


@router.get("/my-documents")
def get_my_documents(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Повертає список завантажених документів поточного користувача."""

    # Шукаємо всі документи, де owner_id збігається з ID користувача
    docs = db.query(models.Document).filter(models.Document.owner_id == current_user.id).all()

    result = []
    for doc in docs:
        result.append({
            "id": doc.id,
            "filename": doc.filename,
            # Форматуємо дату красиво
            "uploaded_at": doc.uploaded_at.strftime("%d.%m.%Y %H:%M") if doc.uploaded_at else "Невідомо",
            "status": "✅ Перевірено"
        })

    return result


@router.delete("/{doc_id}")
def delete_document(
        doc_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Видаляє документ користувача (і його підпис) з бази даних."""

    # 1. Шукаємо документ (перевіряємо, чи він належить саме цьому користувачу)
    doc = db.query(models.Document).filter(models.Document.id == doc_id,
                                           models.Document.owner_id == current_user.id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Документ не знайдено або у вас немає прав на його видалення")

    # 2. Спочатку видаляємо всі підписи, пов'язані з цим документом (щоб не було помилок бази даних)
    db.query(models.Signature).filter(models.Signature.document_id == doc_id).delete()

    # 3. Видаляємо сам документ
    db.delete(doc)
    db.commit()

    return {"message": "Документ успішно видалено"}