import os


class FileUtils:
    """
    Допоміжний клас для роботи з файловою системою.
    Усі операції виконуються в бінарному режимі ('rb', 'wb'),
    щоб не пошкодити криптографічні дані та файли документів.
    """

    @staticmethod
    def read_file_bytes(file_path: str) -> bytes:
        """
        Зчитує будь-який файл (PDF, TXT, DOCX) як масив байтів.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не знайдено: {file_path}")

        with open(file_path, 'rb') as file:
            return file.read()

    @staticmethod
    def write_file_bytes(file_path: str, data: bytes) -> None:
        """
        Записує масив байтів у файл. Використовується для збереження файлу підпису (.sig).
        """
        # Створюємо директорію, якщо вона не існує
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, 'wb') as file:
            file.write(data)

    @staticmethod
    def save_key_to_file(file_path: str, key_pem: bytes) -> None:
        """
        Зберігає згенерований ключ (PEM) у вказаний файл.
        """
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, 'wb') as file:
            file.write(key_pem)

    @staticmethod
    def get_signature_path(original_file_path: str) -> str:
        """
        Генерує стандартне ім'я для файлу підпису.
        Наприклад: 'document.pdf' -> 'document.pdf.sig'
        """
        return f"{original_file_path}.sig"