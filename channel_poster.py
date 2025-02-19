import json
import random
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from loguru import logger

# Загрузка переменных окружения
load_dotenv()
POSTER_TOKEN = os.getenv("POSTER_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
logger.debug(f"Токен загружен: {POSTER_TOKEN}")
target = "content/dating2"
smart_link = "https://google.com"
prokladka = "https://yandex.ru"

# Инициализация бота и диспетчера
bot = Bot(token=POSTER_TOKEN)
dp = Dispatcher()

# Подключение к базе данных SQLite
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Создаем таблицу, если её нет
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT
    )
""")
conn.commit()

user_chat_id = None  # Глобальная переменная для хранения ID пользователя


def save_user(user_id, username):
    """Функция для сохранения пользователя в базу"""
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        logger.info(f"👤 Новый пользователь сохранён: {user_id} ({username})")


def load_messages(target):
    """ Загружаем посты из JSON"""
    with open(f"{target}/messages.json", "r", encoding="utf-8") as file:
        return json.load(file)


async def send_post(messages):
    """Отправка поста"""
    links = messages.get("links_texts")
    buttons = messages.get("buttons_text")
    text = messages.get("desc")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if links:
        for link in links:
            text += "\n" + f"<a href='{random.choice([smart_link, prokladka])}'>{link}</a>"
    if buttons:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=button, url=random.choice([smart_link, prokladka]))]
                for button in buttons
            ]
        )
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=FSInputFile('content/' + messages.get("image")),
        caption=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


def generate_post_times():
    """Генерирует 6 случайных временных точек с интервалом 3-5 часов."""
    # start_time = datetime.now().replace(hour=21, minute=20, second=0, microsecond=0)
    start_time = datetime.now()
    times = []
    for _ in range(6):
        if times:
            start_time = times[-1] + timedelta(minutes=random.randint(1, 3))
        else:
            start_time += timedelta(minutes=random.randint(0, 2))  # Первый пост в начале дня
        times.append(start_time)
    return times


async def scheduler():
    """Планировщик постов на сутки."""
    while True:
        post_times = generate_post_times()
        content_list = load_messages(target=target)
        random.shuffle(content_list)

        for post_time in post_times:
            now = datetime.now()
            delay = (post_time - now).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)  # Ожидание времени постинга
                content = random.choice(content_list)  # Выбираем случайный пост
                await send_post(content)

        await asyncio.sleep(600)  # Ждем сутки перед генерацией новых постов


async def main():
    """Запуск бота"""
    asyncio.create_task(scheduler())  # Запуск планировщика
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
