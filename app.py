import asyncio
import random
import os
import pytz
import logging
import sqlite3
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ИНИЦИАЛИЗАЦИЯ И ЛОГИРОВАНИЕ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = 8273386412
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('quantum_system.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# --- СПИСКИ РЫНКОВ ---
MARKETS = {
    "FOREX": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF"],
    "CRYPTO": ["BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD"],
    "STOCKS": ["TSLA", "AAPL", "NVDA", "AMZN"]
}

# --- КЛАССЫ СОСТОЯНИЙ ---
class TradingFlow(StatesGroup):
    registration = State()
    main_menu = State()
    market_select = State()
    signal_view = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_kb(buttons: list, back_callback=None):
    kb = [[InlineKeyboardButton(text=t, callback_data=c)] for t, c in buttons]
    if back_callback:
        kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def format_signal(asset):
    tz = pytz.timezone('Europe/Uzhgorod')
    time_str = (datetime.now(tz) + timedelta(minutes=5)).strftime("%H:%M:%S")
    return (f"📡 **СИГНАЛ VLADOS QUANTUM**\n\n"
            f"🔹 **Инструмент:** `{asset}`\n"
            f"💰 **Котировка:** `{round(random.uniform(1.0, 1.5), 4)}`\n"
            f"⚡️ **Напр:** {random.choice(['📈 ВВЕРХ', '📉 ВНИЗ'])}\n"
            f"⏳ **Вход до:** `{time_str}`\n"
            f"🔥 **Уверенность:** `{random.randint(90, 99)}%` ✅")

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_command(m: types.Message):
    logger.info(f"User {m.from_user.id} started bot.")
    await m.delete()
    await m.answer("👑 **VLADOS QUANTUM CORE**\nСистема готова к работе.",
                   reply_markup=get_kb([("🚀 Запустить", "reg_flow")]))

@dp.callback_query(F.data == "reg_flow")
async def registration_flow(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("📝 **РЕГИСТРАЦИЯ**\n\n1. Перейдите по ссылке\n2. Отправьте ID",
                              reply_markup=get_kb([("📈 ПЛАТФОРМА", "https://u3.shortink.io/register?a=U7DMqgf943dAUl"),
                                                  ("✅ Отправить ID", "check_id")], "main_menu"))
    await state.set_state(TradingFlow.registration)

@dp.callback_query(F.data == "check_id")
async def process_id(c: types.CallbackQuery):
    await bot.send_message(ADMIN_ID, f"🔔 **Новая заявка:** {c.from_user.full_name}\nID: `{c.from_user.id}`",
                           reply_markup=get_kb([("✅ Одобрить", f"app:{c.from_user.id}")]))
    await c.message.edit_text("⏳ **Заявка отправлена на модерацию.**")

@dp.callback_query(F.data.startswith("app:"))
async def approve_user(c: types.CallbackQuery):
    u_id = c.data.split(":")[1]
    await bot.send_message(int(u_id), "✅ **Одобрено!** Пришлите скриншот депозита.")
    await c.message.delete()

@dp.message(F.photo)
async def handle_deposit(m: types.Message):
    await bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=f"💰 **Депозит от {m.from_user.id}**",
                         reply_markup=get_kb([("✅ Допуск", f"grant:{m.from_user.id}")]))
    await m.answer("⏳ **Скриншот на проверке.**")

@dp.callback_query(F.data.startswith("grant:"))
async def grant_access(c: types.CallbackQuery):
    u_id = c.data.split(":")[1]
    await bot.send_message(int(u_id), "✅ **Доступ предоставлен!** Выберите режим:",
                           reply_markup=get_kb([("🤖 Авто", "m_auto"), ("⚙️ Ручной", "m_man")]))
    await c.message.delete()

@dp.callback_query(F.data == "m_auto")
async def auto_mode(c: types.CallbackQuery):
    await c.message.edit_text(format_signal("EUR/USD"), reply_markup=get_kb([("🔄 Обновить", "m_auto")], "m_man"))

@dp.callback_query(F.data == "m_man")
async def manual_mode(c: types.CallbackQuery):
    await c.message.edit_text("🌍 Выберите рынок:", reply_markup=get_kb([("🌍 Живой", "live"), ("💎 OTC", "otc")], "start"))

@dp.callback_query(F.data == "live")
async def live_market(c: types.CallbackQuery):
    await c.message.edit_text("🔹 Доступные инструменты:", reply_markup=get_kb([("EUR/USD", "sig"), ("GBP/USD", "sig")], "m_man"))

@dp.callback_query(F.data == "sig")
async def show_signal(c: types.CallbackQuery):
    await c.message.edit_text(format_signal("EUR/USD"), reply_markup=get_kb([("🔙 Назад", "m_man")]))

# --- ЗАПУСК ---
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    logger.info(f"WebServer started on port {PORT}")

async def main():
    init_db()
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Critical error: {e}")
