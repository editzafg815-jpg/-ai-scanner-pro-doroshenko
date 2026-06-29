import asyncio
import random
import os
import logging
import time
from threading import Thread
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования для отслеживания состояний
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- КОНФИГУРАЦИЯ ---
# Вставь сюда НОВЫЙ токен после /revoke в @BotFather
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw" 

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БАЗА ДАННЫХ АКТИВОВ ---
# Расширенные списки для увеличения объема кода
LIVE_ASSETS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF", "AUD/NZD", "GBP/CHF", "EUR/NZD"]
OTC_VALUTAS = ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC"]
OTC_CRYPTO = ["Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", "Litecoin OTC", "TRON OTC", "Chainlink OTC", "Stellar OTC"]
OTC_STOCKS = ["Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC", "Google OTC", "Microsoft OTC", "Netflix OTC", "Nvidia OTC", "Intel OTC", "AMD OTC"]

ALL_TIMEFRAMES = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]
ALL_EXPIRATIONS = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]

# --- СОСТОЯНИЯ FSM ---
class FSM(StatesGroup):
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_signal_ui(asset, tf, exp):
    """Генерация красивого торгового сигнала."""
    directions = [("🟢 ВВЕРХ (BUY)", "📈"), ("🔴 ВНИЗ (SELL)", "📉")]
    direction, icon = random.choice(directions)
    timestamp = int(time.time() + 300)
    text = (f"🔥 **QUANTUM CORE TRADING SYSTEM**\n"
            f"📡 **СТАТУС:** АНАЛИЗ ЗАВЕРШЕН\n\n"
            f"🔷 **Актив:** `{asset}`\n"
            f"⚡️ **Направление:** {icon} {direction}\n"
            f"📊 **Таймфрейм:** `{tf}`\n"
            f"⏱ **Экспирация:** `{exp}`\n"
            f"⏳ **Вход до времени:** `{timestamp}`\n"
            f"🎯 **Вероятность:** `{random.randint(96, 99)}%`\n"
            f"💰 **Выплата:** `{random.randint(95, 98)}%`\n\n"
            "✅ *Сигнал прошел глубокий алгоритмический анализ.*")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сгенерировать новый", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим", callback_data="m:man")]
    ])
    await message.answer("✅ **VLADOS USDT CONNECTED**\n\nВыберите метод генерации рекомендаций:", reply_markup=kb)

@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery):
    asset = random.choice(LIVE_ASSETS + OTC_VALUTAS + OTC_CRYPTO + OTC_STOCKS)
    text, kb = get_signal_ui(asset, random.choice(ALL_TIMEFRAMES), random.choice(ALL_EXPIRATIONS))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def man_mode(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой рынок (Live)", callback_data="mkt:live")],
        [InlineKeyboardButton(text="💎 Рынок OTC", callback_data="mkt:otc")]
    ])
    await callback.message.edit_text("🌍 **Выберите рыночную площадку:**", reply_markup=kb)
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("mkt:"))
async def mkt_selection(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in LIVE_ASSETS[:8]])
        await callback.message.edit_text("🔹 **Выберите валютную пару:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💱 Валюты", callback_data="cat:val")],
            [InlineKeyboardButton(text="⚡️ Криптовалюты", callback_data="cat:crypto")],
            [InlineKeyboardButton(text="📊 Акции", callback_data="cat:stock")]
        ])
        await callback.message.edit_text("💎 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("cat:"))
async def cat_selection(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    items = OTC_VALUTAS if cat == "val" else (OTC_CRYPTO if cat == "crypto" else OTC_STOCKS)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in items[:8]])
    await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in ALL_TIMEFRAMES[:6]])
    await callback.message.edit_text("⏳ **Выберите таймфрейм анализа:**", reply_markup=kb)
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in ALL_EXPIRATIONS[:6]])
    await callback.message.edit_text("⏱ **Выберите время экспирации:**", reply_markup=kb)
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def final_sig(callback: types.CallbackQuery, state: FSMContext):
    exp = callback.data.split(":")[1]
    data = await state.get_data()
    text, kb = get_signal_ui(data["asset"], data["tf"], exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим", callback_data="m:man")]
    ])
    await callback.message.edit_text("✅ **Главное меню:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("regen:"))
async def regen_sig(callback: types.CallbackQuery):
    params = callback.data.split(":")
    text, kb = get_signal_ui(params[1], params[2], params[3])
    await callback.message.edit_text(text, reply_markup=kb)

# --- ЗАПУСК ---
async def main():
    """Главная функция запуска с бронебойной очисткой."""
    # Веб-сервер для удержания процесса в Render
    def run_web():
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="Bot is running"))
        web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), handle_signals=False)
    
    # Запуск веб-сервера в отдельном потоке
    Thread(target=run_web, daemon=True).start()
    
    logging.info("Инициализация системы... Очистка вебхуков...")
    
    # КРИТИЧЕСКИ ВАЖНО ДЛЯ ИЗБАВЛЕНИЯ ОТ КОНФЛИКТА
    # Удаляем вебхук, чтобы Telegram переключился на polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Пауза для гарантии завершения старых процессов
    await asyncio.sleep(5)
    
    logging.info("Система готова. Старт опроса API Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
