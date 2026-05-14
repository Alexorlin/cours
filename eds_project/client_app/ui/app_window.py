import customtkinter as ctk
from customtkinter import filedialog
import os
from core.crypto_engine import CryptoEngine
from core.file_utils import FileUtils
from api_client import ApiClient  # <-- Імпортуємо наш мережевий двигун

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("СЕД: Електронний цифровий підпис")
        self.geometry("650x600")  # Трохи збільшили вікно, щоб все влізло

        # Ініціалізуємо клієнт для зв'язку з сервером
        self.api = ApiClient()

        # Створюємо вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_gen = self.tabview.add("Генерація ключів")
        self.tab_sign = self.tabview.add("Підписання")
        self.tab_verify = self.tabview.add("Локальна перевірка")
        self.tab_server = self.tabview.add("Сервер (Мережа)")  # <-- НОВА ВКЛАДКА
        self.tab_history = self.tabview.add("Мої документи")

        self.setup_gen_tab()
        self.setup_sign_tab()
        self.setup_verify_tab()
        self.setup_server_tab()  # <-- Ініціалізуємо нову вкладку
        self.setup_history_tab()

    # ==========================================
    # ВКЛАДКА 1: ГЕНЕРАЦІЯ
    # ==========================================
    def setup_gen_tab(self):
        btn_gen = ctk.CTkButton(self.tab_gen, text="Згенерувати пару ключів", command=self.generate_keys)
        btn_gen.pack(pady=50)

        self.lbl_gen_status = ctk.CTkLabel(self.tab_gen, text="Оберіть папку для збереження ключів")
        self.lbl_gen_status.pack(pady=10)

    def generate_keys(self):
        save_dir = filedialog.askdirectory(title="Оберіть папку для збереження ключів")
        if not save_dir:
            return

        try:
            priv_pem, pub_pem = CryptoEngine.generate_key_pair()
            FileUtils.save_key_to_file(os.path.join(save_dir, "private_key.pem"), priv_pem)
            FileUtils.save_key_to_file(os.path.join(save_dir, "public_key.pem"), pub_pem)
            self.lbl_gen_status.configure(text="Успіх! Ключі збережено.", text_color="green")
        except Exception as e:
            self.lbl_gen_status.configure(text=f"Помилка: {e}", text_color="red")

    # ==========================================
    # ВКЛАДКА 2: ПІДПИСАННЯ
    # ==========================================
    def setup_sign_tab(self):
        self.sign_doc_path = None
        self.sign_key_path = None

        btn_doc = ctk.CTkButton(self.tab_sign, text="Обрати документ", command=self.select_doc_to_sign)
        btn_doc.pack(pady=10)

        btn_key = ctk.CTkButton(self.tab_sign, text="Обрати приватний ключ", command=self.select_priv_key)
        btn_key.pack(pady=10)

        self.btn_sign = ctk.CTkButton(self.tab_sign, text="Підписати документ", command=self.sign_document,
                                      fg_color="green")
        self.btn_sign.pack(pady=20)

        self.lbl_sign_status = ctk.CTkLabel(self.tab_sign, text="")
        self.lbl_sign_status.pack()

    def select_doc_to_sign(self):
        self.sign_doc_path = filedialog.askopenfilename(title="Оберіть документ")
        self.lbl_sign_status.configure(
            text=f"Документ: {os.path.basename(self.sign_doc_path)}" if self.sign_doc_path else "", text_color="white")

    def select_priv_key(self):
        self.sign_key_path = filedialog.askopenfilename(title="Оберіть приватний ключ",
                                                        filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])

    def sign_document(self):
        if not self.sign_doc_path or not self.sign_key_path:
            self.lbl_sign_status.configure(text="Оберіть документ та ключ!", text_color="red")
            return

        try:
            doc_bytes = FileUtils.read_file_bytes(self.sign_doc_path)
            key_bytes = FileUtils.read_file_bytes(self.sign_key_path)

            signature = CryptoEngine.sign_data(doc_bytes, key_bytes)
            sig_path = FileUtils.get_signature_path(self.sign_doc_path)

            FileUtils.write_file_bytes(sig_path, signature)
            self.lbl_sign_status.configure(text=f"Успіх! Підпис збережено як:\n{os.path.basename(sig_path)}",
                                           text_color="green")
        except Exception as e:
            self.lbl_sign_status.configure(text="Помилка підписання!", text_color="red")

    # ==========================================
    # ВКЛАДКА 3: ЛОКАЛЬНА ВЕРИФІКАЦІЯ
    # ==========================================
    def setup_verify_tab(self):
        self.ver_doc_path = None
        self.ver_sig_path = None
        self.ver_key_path = None

        btn_doc = ctk.CTkButton(self.tab_verify, text="1. Обрати документ", command=lambda: self.set_path('doc'))
        btn_doc.pack(pady=5)

        btn_sig = ctk.CTkButton(self.tab_verify, text="2. Обрати файл підпису (.sig)",
                                command=lambda: self.set_path('sig'))
        btn_sig.pack(pady=5)

        btn_key = ctk.CTkButton(self.tab_verify, text="3. Обрати публічний ключ", command=lambda: self.set_path('key'))
        btn_key.pack(pady=5)

        btn_verify = ctk.CTkButton(self.tab_verify, text="Перевірити", command=self.verify_document, fg_color="#1f538d")
        btn_verify.pack(pady=15)

        self.lbl_ver_status = ctk.CTkLabel(self.tab_verify, text="")
        self.lbl_ver_status.pack()

    def set_path(self, target):
        path = filedialog.askopenfilename()
        if target == 'doc':
            self.ver_doc_path = path
        elif target == 'sig':
            self.ver_sig_path = path
        elif target == 'key':
            self.ver_key_path = path

    def verify_document(self):
        if not all([self.ver_doc_path, self.ver_sig_path, self.ver_key_path]):
            self.lbl_ver_status.configure(text="Оберіть всі 3 файли!", text_color="red")
            return

        try:
            doc_bytes = FileUtils.read_file_bytes(self.ver_doc_path)
            sig_bytes = FileUtils.read_file_bytes(self.ver_sig_path)
            key_bytes = FileUtils.read_file_bytes(self.ver_key_path)

            is_valid = CryptoEngine.verify_signature(doc_bytes, sig_bytes, key_bytes)
            if is_valid:
                self.lbl_ver_status.configure(text="✅ ПІДПИС ДІЙСНИЙ. Документ цілий.", text_color="green")
            else:
                self.lbl_ver_status.configure(text="❌ ПІДПИС НЕДІЙСНИЙ або документ змінено!", text_color="red")
        except Exception:
            self.lbl_ver_status.configure(text="Помилка читання або перевірки!", text_color="red")

    # ==========================================
    # ВКЛАДКА 4: СЕРВЕР (МЕРЕЖА)
    # ==========================================
    def setup_server_tab(self):
        # --- Блок Авторизації ---
        frame_auth = ctk.CTkFrame(self.tab_server)
        frame_auth.pack(pady=10, padx=20, fill="x")

        self.entry_user = ctk.CTkEntry(frame_auth, placeholder_text="Логін")
        self.entry_user.pack(pady=5)

        self.entry_pass = ctk.CTkEntry(frame_auth, placeholder_text="Пароль", show="*")
        self.entry_pass.pack(pady=5)

        frame_btns = ctk.CTkFrame(frame_auth, fg_color="transparent")
        frame_btns.pack(pady=5)

        btn_login = ctk.CTkButton(frame_btns, text="Увійти", command=self.do_login, width=110)
        btn_login.pack(side="left", padx=5)

        btn_reg = ctk.CTkButton(frame_btns, text="Реєстрація", command=self.do_register, width=110)
        btn_reg.pack(side="left", padx=5)

        btn_logout = ctk.CTkButton(frame_btns, text="Вийти", command=self.do_logout, width=80, fg_color="gray")
        btn_logout.pack(side="left", padx=5)

        self.lbl_server_auth = ctk.CTkLabel(frame_auth, text="Статус: Не авторизовано", text_color="orange")
        self.lbl_server_auth.pack(pady=5)

        # --- Блок Відправки документів ---
        self.srv_doc_path = None
        self.srv_sig_path = None

        frame_files = ctk.CTkFrame(self.tab_server)
        frame_files.pack(pady=10, padx=20, fill="x")

        btn_s_doc = ctk.CTkButton(frame_files, text="1. Обрати Документ", command=lambda: self.set_srv_path('doc'))
        btn_s_doc.pack(pady=5)

        btn_s_sig = ctk.CTkButton(frame_files, text="2. Обрати Підпис (.sig)", command=lambda: self.set_srv_path('sig'))
        btn_s_sig.pack(pady=5)

        self.btn_send = ctk.CTkButton(self.tab_server, text="Відправити на Сервер", command=self.verify_on_server,
                                      fg_color="green")
        self.btn_send.pack(pady=10)

        self.lbl_server_status = ctk.CTkLabel(self.tab_server, text="")
        self.lbl_server_status.pack()

    def do_login(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if not user or not pwd:
            self.lbl_server_auth.configure(text="Введіть логін та пароль!", text_color="red")
            return

        success, msg = self.api.login(user, pwd)
        if success:
            self.lbl_server_auth.configure(text=f"✅ Авторизовано як: {user}", text_color="green")
        else:
            self.lbl_server_auth.configure(text=f"❌ Помилка: {msg}", text_color="red")

    def do_logout(self):
        self.api.token = None  # Знищуємо токен
        self.lbl_server_auth.configure(text="Статус: Ви вийшли з системи", text_color="orange")

        # Очищаємо список документів, щоб інша людина не побачила
        if hasattr(self, 'history_frame'):
            for widget in self.history_frame.winfo_children():
                widget.destroy()
            self.lbl_history_status.configure(text="Натисніть 'Оновити список', щоб завантажити дані.",
                                              text_color="white")

    def do_register(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if not user or not pwd:
            self.lbl_server_auth.configure(text="Введіть логін та пароль!", text_color="red")
            return

        pub_key_path = filedialog.askopenfilename(title="Оберіть ВАШ public_key.pem", filetypes=[("PEM", "*.pem")])
        if not pub_key_path:
            return

        try:
            pub_bytes = FileUtils.read_file_bytes(pub_key_path)
            pub_pem = pub_bytes.decode('utf-8')
            success, msg = self.api.register(user, pwd, pub_pem)
            if success:
                self.lbl_server_auth.configure(text=f"✅ {msg}", text_color="green")
            else:
                self.lbl_server_auth.configure(text=f"❌ Помилка: {msg}", text_color="red")
        except Exception as e:
            self.lbl_server_auth.configure(text=f"❌ Помилка читання ключа: {e}", text_color="red")

    def set_srv_path(self, target):
        path = filedialog.askopenfilename()
        if not path: return

        if target == 'doc':
            self.srv_doc_path = path
            self.lbl_server_status.configure(text=f"📄 {os.path.basename(path)}")
        elif target == 'sig':
            self.srv_sig_path = path
            self.lbl_server_status.configure(text=f"🔐 {os.path.basename(path)}")

    def verify_on_server(self):
        if not self.srv_doc_path or not self.srv_sig_path:
            self.lbl_server_status.configure(text="Оберіть документ та підпис!", text_color="red")
            return

        self.lbl_server_status.configure(text="⏳ Відправка на сервер...", text_color="yellow")
        self.update()

        success, msg = self.api.verify_document(self.srv_doc_path, self.srv_sig_path)
        if success:
            self.lbl_server_status.configure(text=msg, text_color="green")
        else:
            self.lbl_server_status.configure(text=f"❌ Відмова сервера: {msg}", text_color="red")

    # ==========================================
    # ВКЛАДКА 5: ІСТОРІЯ ДОКУМЕНТІВ - НОВЕ!
    # ==========================================
    def setup_history_tab(self):
        # Кнопка для оновлення списку
        btn_refresh = ctk.CTkButton(self.tab_history, text="🔄 Оновити список", command=self.load_documents)
        btn_refresh.pack(pady=10)

        self.lbl_history_status = ctk.CTkLabel(self.tab_history,
                                               text="Натисніть 'Оновити список', щоб завантажити дані.")
        self.lbl_history_status.pack(pady=5)

        # Скролл-фрейм (як вікно чату), де будуть з'являтися документи
        self.history_frame = ctk.CTkScrollableFrame(self.tab_history, width=550, height=400)
        self.history_frame.pack(pady=10, padx=20, fill="both", expand=True)

    def load_documents(self):
        # Перевіряємо, чи є токен
        if not self.api.token:
            self.lbl_history_status.configure(text="❌ Спершу авторизуйтесь у вкладці 'Сервер (Мережа)'!",
                                              text_color="red")
            return

        self.lbl_history_status.configure(text="⏳ Завантаження...", text_color="yellow")
        self.update()

        success, data = self.api.get_my_documents()

        if success:
            # Очищаємо фрейм від старих записів (якщо були)
            for widget in self.history_frame.winfo_children():
                widget.destroy()

            if not data:
                self.lbl_history_status.configure(text="📭 У вас ще немає завантажених документів.", text_color="white")
                return

            self.lbl_history_status.configure(text=f"✅ Знайдено документів: {len(data)}", text_color="green")

            # Створюємо "картку" для кожного документа
            for doc in data:
                doc_frame = ctk.CTkFrame(self.history_frame, fg_color="#2b2b2b")
                doc_frame.pack(pady=5, padx=5, fill="x")

                # ---  КНОПКА ВИДАЛЕННЯ ---
                # lambda d=doc['id']: self.delete_doc_ui(d) - передає ID конкретного документа
                btn_del = ctk.CTkButton(doc_frame, text="🗑 Видалити", width=80, fg_color="#8b0000",
                                        hover_color="#5a0000",
                                        command=lambda d=doc['id']: self.delete_doc_ui(d))
                btn_del.pack(side="right", padx=10, pady=10)
                # -----------------------------

                lbl_name = ctk.CTkLabel(doc_frame, text=f"📄 {doc['filename']}", font=("Arial", 14, "bold"))
                lbl_name.pack(anchor="w", padx=10, pady=(5, 0))

                lbl_info = ctk.CTkLabel(doc_frame, text=f"Дата: {doc['uploaded_at']}  |  Статус: {doc['status']}",
                                        text_color="gray")
                lbl_info.pack(anchor="w", padx=10, pady=(0, 5))
        else:
            self.lbl_history_status.configure(text=f"❌ Помилка: {data}", text_color="red")

    def delete_doc_ui(self, doc_id):
        """Обробляє натискання кнопки видалення документа."""
        success, msg = self.api.delete_document(doc_id)
        if success:
            # Якщо успішно видалили на сервері — просто оновлюємо список
            self.load_documents()
        else:
            self.lbl_history_status.configure(text=f"❌ Помилка: {msg}", text_color="red")