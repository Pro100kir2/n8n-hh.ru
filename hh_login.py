import os
import sys
import json
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Путь для хранения файлов n8n и сессий
N8N_FILES_DIR = os.getenv(
    "N8N_FILES_DIR",
    os.path.expanduser("~/.n8n-files")
)
SESSION_FILE = os.path.join(N8N_FILES_DIR, "hh_session.json")

# Телефон из .env
HH_PHONE = os.getenv("HH_PHONE")


def ensure_dir():
    if not os.path.exists(N8N_FILES_DIR):
        print(f"Создаём директорию: {N8N_FILES_DIR}")
        os.makedirs(N8N_FILES_DIR)


def login():
    if not HH_PHONE:
        print("ERROR: Пожалуйста, укажите HH_PHONE в файле .env")
        return

    ensure_dir()
    with sync_playwright() as p:
        # Обычный браузер для надёжного входа
        browser = p.chromium.launch(headless=True, slow_mo=0)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()
        page.goto("https://hh.ru/login", wait_until="domcontentloaded", timeout=60000)

        # Клик по кнопке "Войти по номеру телефона"
        enter_btn = page.locator("xpath=//button[.//span[text()='Войти']]")
        enter_btn.wait_for(state="visible", timeout=60000)
        enter_btn.first.click()

        # Ввод телефона в нужное поле
        phone_input = page.locator(
            "xpath=/html/body/div[2]/div/div/div[1]/div/div/div[1]/div/div/div/div/div/div[1]/div/div/form/div/div/div[3]/div[1]/div[2]/div/div/div[2]/div[2]/input"
        )
        phone_input.wait_for(state="visible", timeout=60000)
        phone_input.fill(HH_PHONE)

        # Клик по кнопке "Продолжить"
        continue_btn = page.locator("xpath=//button[.//span[text()='Дальше']]")
        continue_btn.wait_for(state="visible", timeout=60000)
        continue_btn.first.click()

        # Запрос кода подтверждения
        code = input("Введите код подтверждения из SMS: ")

        # Ввод кода и Enter
        code_input = page.locator("xpath=//input[@name='code']")
        code_input.wait_for(state="visible", timeout=60000)
        code_input.fill(code)
        page.keyboard.press("Enter")

        # Ждём загрузки страницы с резюме
        page.wait_for_selector("a[href*='/resume']", timeout=60000)

        # Сохраняем cookies и local storage
        context.storage_state(path=SESSION_FILE)
        print(f"Сессия успешно сохранена в {SESSION_FILE}")

        browser.close()


def get_cookies():
    if not os.path.exists(SESSION_FILE):
        print("Сессия не найдена. Пожалуйста, сначала выполните login()")
        return None

    with open(SESSION_FILE, "r") as f:
        state = json.load(f)
        cookies = state.get("cookies", [])
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        return cookie_str


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--get-cookies":
        print(get_cookies())
    else:
        login()