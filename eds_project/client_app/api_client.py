
import requests
import os


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None  # Тут ми будемо зберігати JWT-перепустку після логіну

    def register(self, username, password, public_key_pem):
        """Відправляє дані для реєстрації нового користувача."""
        url = f"{self.base_url}/auth/register"
        payload = {
            "username": username,
            "password": password,
            "public_key_pem": public_key_pem
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Викидає помилку, якщо статус сервера не 200-299
            return True, response.json().get("message")
        except requests.exceptions.HTTPError:
            error_detail = response.json().get("detail", "Помилка реєстрації")
            return False, error_detail
        except requests.exceptions.ConnectionError:
            return False, "Помилка з'єднання. Переконайтеся, що сервер (FastAPI) запущено."

    def login(self, username, password):
        """Авторизація користувача та отримання JWT-токена."""
        url = f"{self.base_url}/auth/login"
        # Для логіну сервер чекає дані у форматі форми (Form Data), а не JSON
        payload = {
            "username": username,
            "password": password
        }
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()

            # Якщо все успішно, зберігаємо токен у пам'яті клієнта
            self.token = response.json().get("access_token")
            return True, "Авторизація успішна"
        except requests.exceptions.HTTPError:
            error_detail = response.json().get("detail", "Невірний логін або пароль")
            return False, error_detail
        except requests.exceptions.ConnectionError:
            return False, "Помилка з'єднання із сервером."

    def verify_document(self, doc_path, sig_path):
        """Відправляє документ і підпис на сервер для криптографічної перевірки."""
        if not self.token:
            return False, "Ви не авторизовані. Будь ласка, увійдіть в систему."

        url = f"{self.base_url}/docs/verify-and-save"

        # Додаємо токен до заголовків запиту (так само як кнопка Authorize у Swagger)
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        try:
            # Читаємо файли в бінарному режимі ('rb')
            with open(doc_path, 'rb') as doc_file, open(sig_path, 'rb') as sig_file:
                # Пакуємо файли для відправки (Multipart Form)
                files = {
                    'file': (os.path.basename(doc_path), doc_file, 'application/octet-stream'),
                    'signature_file': (os.path.basename(sig_path), sig_file, 'application/octet-stream')
                }

                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()
                return True, response.json().get("message")

        except requests.exceptions.HTTPError:
            error_detail = response.json().get("detail", "Помилка перевірки на сервері")
            return False, error_detail
        except Exception as e:
            return False, f"Помилка при роботі з файлами: {str(e)}"

    def get_my_documents(self):
        """Отримує список документів з сервера."""
        if not self.token:
            return False, "Ви не авторизовані."

        url = f"{self.base_url}/docs/my-documents"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            # Повертаємо True і сам список словників (даних)
            return True, response.json()
        except requests.exceptions.HTTPError:
            return False, "Помилка завантаження списку"
        except Exception as e:
            return False, f"Помилка мережі: {str(e)}"

    def delete_document(self, doc_id):
        """Відправляє запит на видалення документа."""
        if not self.token:
            return False, "Ви не авторизовані."

        url = f"{self.base_url}/docs/{doc_id}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        try:
            # Використовуємо метод DELETE
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return True, response.json().get("message")
        except requests.exceptions.HTTPError:
            return False, "Не вдалося видалити документ (можливо, немає прав)"
        except Exception as e:
            return False, f"Помилка мережі: {str(e)}"