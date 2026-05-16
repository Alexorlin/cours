from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature


class CryptoEngine:
    """
    Ядро криптографічних операцій для ЕЦП.
    Використовує стандарт RSA-2048 та хешування SHA-256 з паддінгом PSS.
    """

    @staticmethod
    def generate_key_pair() -> tuple[bytes, bytes]:
        """
        Генерує нову пару ключів RSA.
        :return: Кортеж (private_key_pem, public_key_pem) у вигляді байтів.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    @staticmethod
    def sign_data(data: bytes, private_pem: bytes) -> bytes:
        """
        Створює цифровий підпис для переданих байтів.
        :param data: Байти документа (або будь-яких даних), які треба підписати.
        :param private_pem: Приватний ключ у форматі PEM (байти).
        :return: Байти згенерованого підпису.
        """
        private_key = serialization.load_pem_private_key(private_pem, password=None)

        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    def verify_signature(data: bytes, signature: bytes, public_pem: bytes) -> bool:
        """
        Перевіряє валідність цифрового підпису.
        :param data: Оригінальні байти документа.
        :param signature: Байти підпису, який треба перевірити.
        :param public_pem: Публічний ключ автора підпису у форматі PEM (байти).
        :return: True, якщо підпис валідний, інакше False.
        """
        public_key = serialization.load_pem_public_key(public_pem)

        try:
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
        except InvalidSignature:
            return False