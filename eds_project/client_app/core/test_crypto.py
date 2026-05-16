# client_app/core/test_crypto.py

from crypto_engine import CryptoEngine


def run_test():
    print("--- ТЕСТУВАННЯ КРИПТОГРАФІЧНОГО ЯДРА ---")

    # Етап 1: Генерація ключів
    print("\n1. Генеруємо ключі RSA-2048...")
    private_pem, public_pem = CryptoEngine.generate_key_pair()
    print("✅ Ключі успішно згенеровано!")

    # Етап 2: Підготовка даних
    # Імітуємо вміст PDF-файлу або текстового документа у вигляді байтів
    original_document = b"This is the official document for my course work. Do not change!"
    print(f"\n2. Оригінальний документ: {original_document}")

    # Етап 3: Підписання
    print("\n3. Накладаємо цифровий підпис...")
    signature = CryptoEngine.sign_data(original_document, private_pem)
    print(f"✅ Підпис успішно створено! (довжина: {len(signature)} байт)")

    # Етап 4: Перевірка валідного документа
    print("\n4. Верифікація оригінального документа...")
    is_valid = CryptoEngine.verify_signature(original_document, signature, public_pem)
    if is_valid:
        print("✅ УСПІХ: Підпис дійсний. Документ не змінено.")
    else:
        print("❌ ПОМИЛКА: Підпис не пройшов перевірку.")

    # Етап 5: Спроба "хакерської" підміни
    print("\n5. Імітуємо зміну документа зловмисником (додаємо крапку в кінці)...")
    hacked_document = b"This is the official document for my course work. Do not change!."

    is_hacked_valid = CryptoEngine.verify_signature(hacked_document, signature, public_pem)
    if not is_hacked_valid:
        print("✅ УСПІХ БЕЗПЕКИ: Система виявила підміну! Підпис визнано НЕДІЙСНИМ.")
    else:
        print("❌ КРИТИЧНА ПОМИЛКА БЕЗПЕКИ: Система прийняла підроблений документ.")


if __name__ == "__main__":
    run_test()