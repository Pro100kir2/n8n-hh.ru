import os
import subprocess
import sys
import time
from pathlib import Path

# Папки и файлы
SESSION_DIR = Path("session")
HH_LOGIN_SCRIPT = Path("hh_login.py")
HH_SERVER_SCRIPT = Path("hh_server.py")
N8N_DIR = Path("n8n")
N8N_GIT = "https://github.com/n8n-io/n8n.git"
N8N_VOLUME = "n8n_data"
N8N_CONTAINER_NAME = "n8n"
N8N_PORT = 5678


def ensure_session():
    """Проверяем папку session и запускаем логин если её нет."""
    if not SESSION_DIR.exists():
        print(f"Создаем папку session: {SESSION_DIR}")
        SESSION_DIR.mkdir(parents=True)
        print("Запускаем HH login...")
        subprocess.run([sys.executable, str(HH_LOGIN_SCRIPT)], check=True)
    else:
        print(f"Папка session уже существует: {SESSION_DIR}")


def ensure_n8n():
    """Проверяем папку n8n и Docker volume."""
    if not N8N_DIR.exists():
        print(f"Клонируем n8n из GitHub в {N8N_DIR}...")
        subprocess.run(["git", "clone", N8N_GIT, str(N8N_DIR)], check=True)
    else:
        print(f"Папка n8n уже существует: {N8N_DIR}")

    # Создаем Docker volume (если его нет)
    subprocess.run(["docker", "volume", "create", N8N_VOLUME], check=False)


def run_n8n():
    """Запускаем Docker контейнер с n8n в фоне, без вывода логов в PyCharm."""
    print("Запускаем n8n через Docker в фоне...")
    subprocess.Popen([
        "docker", "run", "-d", "--rm",
        "--name", N8N_CONTAINER_NAME,
        "-p", f"{N8N_PORT}:5678",
        "-v", f"{N8N_VOLUME}:/home/node/.n8n",
        "docker.n8n.io/n8nio/n8n"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # <- подавляем логи n8n


def run_hh_server():
    """Запускаем hh_server.py в текущей консоли PyCharm с логами."""
    print("Запускаем HH Server в текущей консоли PyCharm...")
    subprocess.run([sys.executable, str(HH_SERVER_SCRIPT)])


def main():
    ensure_session()
    ensure_n8n()
    run_n8n()
    time.sleep(5)  # Ждем немного, чтобы n8n поднялся
    run_hh_server()


if __name__ == "__main__":
    main()