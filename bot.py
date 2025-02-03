import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Укажите ID чата в .env

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в файле .env")

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище активности пользователей
user_activity = {}

# Запрещенные слова
bad_words = ["хуй", "мат2", "мат3"]


### 📌 Стандартные команды ###
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот активности. Пиши мне и участвуй в рейтинге!")


@dp.message(Command("бот_график_уборки"))
async def cmd_schedule(message: Message):
    await message.answer("🧹 График уборки: Понедельник, Среда, Пятница в 9:00.")


@dp.message(Command("бот_подрядчики"))
async def cmd_contractors(message: Message):
    await message.answer("👷 Список подрядчиков:\n1. Подрядчик 1\n2. Подрядчик 2\n3. Подрядчик 3")


@dp.message(Command("бот_состав_тарифа"))
async def cmd_tariff(message: Message):
    await message.answer("📊 Состав тарифа:\n1. Вода\n2. Электричество\n3. Уборка")


@dp.message(Command("бот_горячие_телефоны"))
async def cmd_hotlines(message: Message):
    await message.answer("☎ Горячие телефоны:\n1. Пожарные — 101\n2. Полиция — 102\n3. МЧС — 112")


@dp.message(Command("бот_аварийка"))
async def cmd_emergency(message: Message):
    await message.answer("🚨 Аварийка: Телефон аварийной службы — 112.")


@dp.message(Command("помощь"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 Доступные команды:\n"
        "/бот_график_уборки\n"
        "/бот_подрядчики\n"
        "/бот_состав_тарифа\n"
        "/бот_горячие_телефоны\n"
        "/бот_аварийка\n"
        "\n💡 Или просто напишите 'бот, кто самый активный?'"
    )


### 📌 Отслеживание активности пользователей ###
@dp.message()
async def track_activity(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = message.text.lower()

    # 📌 Если в сообщении есть "бот", реагируем
    if "бот" in text:
        await handle_bot_mention(message)
        return

    # 📌 Проверяем на маты
    if any(word in text for word in bad_words):
        await message.delete()
        await message.answer(f"❌ @{username}, не используй маты! Блокировка на 1 день.")

        until_date = datetime.now() + timedelta(days=1)
        try:
            await bot.ban_chat_member(message.chat.id, user_id, until_date=until_date)
        except Exception as e:
            logging.error(f"Ошибка при бане: {e}")
        return

    # 📌 Увеличиваем счетчик сообщений пользователя
    if user_id in user_activity:
        user_activity[user_id]["count"] += 1
    else:
        user_activity[user_id] = {"count": 1, "username": username}


### 📌 Ответ на "бот, кто самый активный?" ###
async def handle_bot_mention(message: Message):
    text = message.text.lower()

    if "кто самый активный" in text:
        if not user_activity:
            await message.answer("📊 Пока нет данных о активности.")
            return

        sorted_users = sorted(user_activity.items(), key=lambda x: x[1]["count"], reverse=True)
        top_users = sorted_users[:3]

        report = "📊 Самые активные за сегодня:\n"
        for i, (user_id, data) in enumerate(top_users, start=1):
            report += f"{i}. @{data['username']} — {data['count']} сообщений\n"

        winner = top_users[0][1]['username']
        report += f"\n🎉 @{winner} — лидер активности сегодня!"
        await message.answer(report)

    else:
        await message.answer("👋 Привет! Я бот активности. Напиши 'бот, кто самый активный?' чтобы узнать топ-3!")


### 📌 Автоотчет в 21:00 ###
async def daily_report():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=21, minute=0, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        sleep_seconds = (target_time - now).total_seconds()
        logging.info(f"⏳ Ожидание до 21:00: {sleep_seconds} секунд")
        await asyncio.sleep(sleep_seconds)

        if user_activity:
            sorted_users = sorted(user_activity.items(), key=lambda x: x[1]["count"], reverse=True)
            top_users = sorted_users[:3]

            report = "📊 Итоги дня:\n"
            for i, (user_id, data) in enumerate(top_users, start=1):
                report += f"{i}. @{data['username']} — {data['count']} сообщений\n"

            winner = top_users[0][1]['username']
            report += f"\n🎊 Поздравляем @{winner} — ты самый активный сегодня!"

            if CHAT_ID:
                await bot.send_message(CHAT_ID, report)

        user_activity.clear()


### 📌 Запуск бота ###
async def main():
    asyncio.create_task(daily_report())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
