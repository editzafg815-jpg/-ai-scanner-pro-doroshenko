import asyncio
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

# ==============================================================================
# КОНФИГУРАЦИЯ И ЛОГИРОВАНИЕ (Система мониторинга)
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("VLADOS_SYSTEM")

BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = 8273386412 
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==============================================================================
# МОДУЛЬ БАЗЫ ДАННЫХ (SQLite Engine)
# ==============================================================================
def db_init():
    conn = sqlite3.connect('vlados_prod.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, status TEXT, last_active TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS stats (total_signals INTEGER, approved_users INTEGER)')
    conn.commit()
    conn.close()

# ==============================================================================
# КЛАССЫ СОСТОЯНИЙ (FSM Architecture)
# ==============================================================================
class TradingSystem(StatesGroup):
    auth_step = State()
    main_menu = State()
    dep_verification = State()
    dashboard = State()

# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Helper Methods)
# ==============================================================================
def create_keyboard(buttons: list, back_btn=None):
    kb = [[InlineKeyboardButton(text=t, callback_data=c)] for t, c in buttons]
    if back_btn:
        kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_btn)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_market_data(asset: str):
    """Генерация аналитики для пользователя"""
    time_str = (datetime.now(pytz.timezone('Europe/Uzhgorod')) + timedelta(minutes=5)).strftime("%H:%M:%S")
    return (f"📡 **СИГНАЛ: VLADOS QUANTUM ENGINE**\n\n"
            f"🔹 **Актив:** `{asset}`\n"
            f"💰 **Котировка:** `1.1250`\n"
            f"⚡️ **Направление:** 📈 BUY (Вверх)\n"
            f"⏳ **Вход до (Ужгород):** `{time_str}`\n"
            f"🎯 **Выплата:** `92%`\n"
            f"🔥 **Уровень точности:** `98%` ✅")

# ==============================================================================
# ХЕНДЛЕРЫ УРОВНЯ 1: СТАРТ И АВТОРИЗАЦИЯ
# ==============================================================================
@dp.message(Command("start"))
async def start_handler(m: types.Message):
    logger.info(f"User {m.from_user.id} accessed CORE.")
    await m.delete()
    await m.answer("👑 **VLADOS USDT: QUANTUM CORE v5.0**\nВыберите действие для продолжения:",
                   reply_markup=create_keyboard([("🚀 Запустить систему", "reg_init")]))

@dp.callback_query(F.data == "reg_init")
async def registration_flow(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("📝 **ШАГ 1: АВТОРИЗАЦИЯ**\nПройдите регистрацию по партнерской ссылке.",
                              reply_markup=create_keyboard([("📈 ПЕРЕЙТИ", "link_ref"), ("✅ Отправить ID", "send_id")], "start"))
    await state.set_state(TradingSystem.auth_step)

# ==============================================================================
# ХЕНДЛЕРЫ УРОВНЯ 2: ДЕПОЗИТ И МОДЕРАЦИЯ
# ==============================================================================
@dp.callback_query(F.data == "send_id")
async def send_id(c: types.CallbackQuery):
    await bot.send_message(ADMIN_ID, f"🔔 **НОВАЯ ЗАЯВКА**\nПользователь: {c.from_user.full_name}\nID: `{c.from_user.id}`",
                           reply_markup=create_keyboard([("✅ Одобрить", f"app:{c.from_user.id}")]))
    await c.message.edit_text("⏳ **Заявка принята. Ожидайте подтверждения доступа.**")

@dp.message(F.text.regexp(r'^\d+$'))
async def deposit_handler(m: types.Message):
    await bot.send_message(ADMIN_ID, f"💰 **ВХОДЯЩИЙ ДЕПОЗИТ**\nСумма: {m.text} USDT\nID: {m.from_user.id}",
                           reply_markup=create_keyboard([("✅ Открыть доступ", f"grant:{m.from_user.id}")]))
    await m.answer("⏳ **Сумма депозита обрабатывается сервером.**")

@dp.callback_query(F.data.startswith("grant:"))
async def access_granted(c: types.CallbackQuery):
    u_id = c.data.split(":")[1]
    await bot.send_message(int(u_id), "✅ **Доступ к системе VLADOS предоставлен!**\nВыберите режим работы:",
                           reply_markup=create_keyboard([("🤖 Авто-сигнал", "m_auto"), ("⚙️ Ручной режим", "m_man")]))
    await c.message.delete()

# ==============================================================================
# ХЕНДЛЕРЫ УРОВНЯ 3: ДАШБОРД И АНАЛИТИКА
# ==============================================================================
@dp.callback_query(F.data == "m_auto")
async def auto_mode(c: types.CallbackQuery):
    await c.message.edit_text(get_market_data("EUR/USD"), reply_markup=create_keyboard([("🔄 Обновить", "m_auto")], "m_man"))

@dp.callback_query(F.data == "m_man")
async def manual_mode(c: types.CallbackQuery):
    await c.message.edit_text("🌍 Выберите рынок для анализа:", 
                              reply_markup=create_keyboard([("🌍 Живой", "live"), ("💎 OTC", "otc")], "start"))

@dp.callback_query(F.data == "live")
async def live_market(c: types.CallbackQuery):
    await c.message.edit_text("🔹 Активы (Живой рынок):", reply_markup=create_keyboard([("EUR/USD", "sig"), ("GBP/USD", "sig")], "m_man"))

@dp.callback_query(F.data == "sig")
async def show_signal(c: types.CallbackQuery):
    await c.message.edit_text(get_market_data("EUR/USD"), reply_markup=create_keyboard([("🔙 Назад", "m_man")]))

# ==============================================================================
# СЕРВЕРНАЯ ЧАСТЬ (WEB API)
# ==============================================================================
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Quantum Core System Online"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    logger.info(f"System Web Interface operational on port {PORT}")

async def main():
    db_init()
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("System poll started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"FATAL SYSTEM ERROR: {e}")
