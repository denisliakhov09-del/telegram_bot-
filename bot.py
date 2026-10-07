import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REF_LINK = os.getenv("REF_LINK", "https://example.com/").strip()
DEMO_APP_URL = os.getenv("DEMO_APP_URL", "https://example.com/").strip()

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в файле .env")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB = "bot.db"

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        account_id TEXT,
        stage TEXT NOT NULL DEFAULT 'new'
    )""")
    con.commit()
    con.close()

def save_user(tg_id, account_id, stage):
    con = sqlite3.connect(DB)
    con.execute("""INSERT INTO users(telegram_id,account_id,stage)
        VALUES(?,?,?)
        ON CONFLICT(telegram_id) DO UPDATE SET
        account_id=excluded.account_id, stage=excluded.stage""",
        (tg_id, account_id, stage))
    con.commit()
    con.close()

def get_user(tg_id):
    con = sqlite3.connect(DB)
    row = con.execute(
        "SELECT telegram_id,account_id,stage FROM users WHERE telegram_id=?",
        (tg_id,)).fetchone()
    con.close()
    return row

def start_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Ввести ID", callback_data="enter_id")
    kb.button(text="ℹ️ Как работает DEMO", callback_data="about")
    kb.adjust(1)
    return kb.as_markup()

def demo_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Открыть DEMO Mines", url=DEMO_APP_URL)
    kb.button(text="📊 Моя информация", callback_data="my_info")
    kb.button(text="🔄 Ввести другой ID", callback_data="enter_id")
    kb.adjust(1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это тестовая DEMO-версия.\n"
        "Введите ID аккаунта для демонстрационной проверки.",
        reply_markup=start_kb())

@dp.callback_query(F.data == "enter_id")
async def enter_id(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🔢 Отправьте ID аккаунта цифрами.\nНапример: <code>123456789</code>")

@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "ℹ️ <b>Как работает DEMO</b>\n\n"
        "1. Вводите тестовый ID.\n"
        "2. Бот сохраняет его локально.\n"
        "3. После DEMO-проверки открывается меню.\n"
        "4. Кнопка DEMO Mines открывает тестовую Mini App.\n\n"
        "⚠️ Реальная проверка депозита здесь не выполняется.")

@dp.message(F.text.regexp(r"^\d+$"))
async def process_id(message: types.Message):
    tg_id = message.from_user.id
    account_id = message.text.strip()
    old = get_user(tg_id)

    if old is None or old[2] != "demo_verified":
        save_user(tg_id, account_id, "waiting_demo")
        msg = await message.answer("🔄 <b>DEMO-проверка ID...</b>")
        await asyncio.sleep(1)
        kb = InlineKeyboardBuilder()
        kb.button(text="🌐 Перейти по партнёрской ссылке", url=REF_LINK)
        kb.button(text="🎮 Активировать DEMO", callback_data="activate_demo")
        kb.adjust(1)
        await msg.edit_text(
            f"ℹ️ <b>DEMO-проверка завершена.</b>\n\n"
            f"ID: <code>{account_id}</code>\n\n"
            "Это демонстрационный сценарий; реальная проверка 1Win не выполняется.",
            reply_markup=kb.as_markup())
        return

    save_user(tg_id, account_id, "demo_verified")
    await message.answer(
        f"✅ <b>DEMO-доступ активирован!</b>\n\n"
        f"ID: <code>{account_id}</code>\n\nВыберите действие:",
        reply_markup=demo_kb())

@dp.callback_query(F.data == "activate_demo")
async def activate_demo(callback: types.CallbackQuery):
    await callback.answer("DEMO активирован")
    row = get_user(callback.from_user.id)
    account_id = row[1] if row else "не указан"
    save_user(callback.from_user.id, account_id, "demo_verified")
    await callback.message.answer(
        f"✅ <b>DEMO-доступ активирован!</b>\n\n"
        f"ID: <code>{account_id}</code>\n\nВыберите действие:",
        reply_markup=demo_kb())

@dp.callback_query(F.data == "my_info")
async def my_info(callback: types.CallbackQuery):
    await callback.answer()
    row = get_user(callback.from_user.id)
    if not row:
        await callback.message.answer("Данные пока не найдены.")
        return
    await callback.message.answer(
        "📊 <b>Моя информация</b>\n\n"
        f"Telegram ID: <code>{row[0]}</code>\n"
        f"Введённый ID: <code>{row[1]}</code>\n"
        f"Статус DEMO: <code>{row[2]}</code>")

@dp.message()
async def other(message: types.Message):
    await message.answer("Введите ID только цифрами, например <code>123456789</code>.")

async def main():
    init_db()
    print("Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
