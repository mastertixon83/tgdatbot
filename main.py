import json
import random
import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from loguru import logger

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
logger.debug(f"Токен загружен: {TOKEN}")
target = "content/channel"
smart_link = "https://google.com"
prokladka = "https://yandex.ru"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
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


async def send_post(user_id, messages):
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
    await bot.send_photo(chat_id=user_id,
                         photo=FSInputFile('content/' + messages.get("image")),
                         caption=text,
                         parse_mode="HTML",
                         reply_markup=keyboard)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """ Обработчик команды /start"""
    global user_chat_id
    user_chat_id = message.chat.id
    user_id = message.chat.id
    username = message.from_user.username if message.from_user.username else "Anonimus"

    save_user(user_id, username)

    logger.info(f"👤 Новый пользователь: {user_chat_id}")

    messages = load_messages(target=target)
    await send_post(user_id=user_chat_id, messages=messages[0])


async def send_random_post():
    """Функция для отправки сообщений"""
    global user_chat_id
    messages = load_messages(target=target)
    random.shuffle(messages)
    while True:
        if user_chat_id is None:
            await asyncio.sleep(5)
            continue

        for post in messages:

            delay = random.randint(1200, 1800)
            logger.info(f"⏳ Ожидание {delay} секунд перед отправкой поста...")
            await asyncio.sleep(delay)

            await send_post(user_id=user_chat_id, messages=post)


async def main():
    """Запуск бота"""
    asyncio.create_task(send_random_post())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
