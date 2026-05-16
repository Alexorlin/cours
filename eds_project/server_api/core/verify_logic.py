
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature


def verify_signature(data: bytes, signature: bytes, public_pem: bytes) -> bool:
    """
    Серверна функція перевірки ЕЦП.
    Бере байти документа, байти підпису та публічний ключ користувача з бази.
    """
    try:
        public_key = serialization.load_pem_public_key(public_pem)

        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        # Якщо ключ неправильного формату або підпис підроблено
        return False