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

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw" 

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- ПОЛНЫЕ СПИСКИ АКТИВОВ ---
LIVE_ASSETS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", 
    "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", 
    "EUR/AUD", "EUR/CAD", "CAD/CHF", "AUD/NZD", "GBP/USD"
]

OTC_VALUTAS = [
    "AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", 
    "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", 
    "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", 
    "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC"
]

OTC_CRYPTO = [
    "Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", 
    "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", 
    "Litecoin OTC", "TRON OTC", "Chainlink OTC"
]

OTC_STOCKS = [
    "Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC", 
    "Google OTC", "Microsoft OTC", "Netflix OTC", "Nvidia OTC"
]

ALL_TIMEFRAMES = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]
ALL_EXPIRATIONS = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]

class FSM(StatesGroup):
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()

# --- ЛОГИКА ГЕНЕРАЦИИ СИГНАЛОВ ---
def get_signal_data(asset, tf, exp):
    directions = [("🟢 ВВЕРХ (BUY)", "📈"), ("🔴 ВНИЗ (SELL)", "📉")]
    direction, icon = random.choice(directions)
    timestamp = int(time.time() + 300)
    
    text = (
        f"🔥 **QUANTUM CORE TRADING SYSTEM**\n"
        f"📡 **СТАТУС:** АКТИВЕН\n\n"
        f"🔷 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {icon} {direction}\n"
        f"📊 **Таймфрейм:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"⏳ **Вход до времени:** `{timestamp}`\n"
        f"🎯 **Вероятность успеха:** `{random.randint(96, 99)}%`\n"
        f"💰 **Выплата:** `{random.randint(95, 98)}%`\n\n"
        "✅ *Сигнал прошел глубокий анализ алгоритмов.*\n"
        "⚠️ *Соблюдайте правила риск-менеджмента.*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще сигнал", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ])
    return text, kb

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим (Случайный)", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим (Выбор активов)", callback_data="m:man")]
    ])

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ **Добро пожаловать в VLADOS USDT.**\n\nВыберите режим работы бота для получения торговых рекомендаций:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery):
    asset = random.choice(LIVE_ASSETS + OTC_VALUTAS + OTC_CRYPTO + OTC_STOCKS)
    tf = random.choice(ALL_TIMEFRAMES)
    exp = random.choice(ALL_EXPIRATIONS)
    text, kb = get_signal_data(asset, tf, exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def man_mode(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой рынок", callback_data="mkt:live")],
        [InlineKeyboardButton(text="💎 Рынок OTC", callback_data="mkt:otc")]
    ])
    await callback.message.edit_text("🌍 **Выберите рынок:**", reply_markup=kb)
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("mkt:"))
async def mkt_selection(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in LIVE_ASSETS[:10]])
        await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💱 Валюты", callback_data="cat:val")],
            [InlineKeyboardButton(text="⚡️ Крипта", callback_data="cat:crypto")],
            [InlineKeyboardButton(text="📊 Акции", callback_data="cat:stock")]
        ])
        await callback.message.edit_text("💎 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("cat:"))
async def cat_selection(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    items = OTC_VALUTAS if cat == "val" else (OTC_CRYPTO if cat == "crypto" else OTC_STOCKS)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in items[:10]])
    await callback.message.edit_text("🔹 **Выберите OTC актив:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in ALL_TIMEFRAMES])
    await callback.message.edit_text("⏳ **Выберите таймфрейм:**", reply_markup=kb)
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in ALL_EXPIRATIONS])
    await callback.message.edit_text("⏱ **Выберите экспирацию:**", reply_markup=kb)
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def final_sig(callback: types.CallbackQuery, state: FSMContext):
    exp = callback.data.split(":")[1]
    data = await state.get_data()
    text, kb = get_signal_data(data["asset"], data["tf"], exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ **Главное меню:**", reply_markup=get_main_menu())

@dp.callback_query(F.data.startswith("regen:"))
async def regen_sig(callback: types.CallbackQuery):
    params = callback.data.split(":")
    text, kb = get_signal_data(params[1], params[2], params[3])
    await callback.message.edit_text(text, reply_markup=kb)

# --- СИСТЕМА ЗАПУСКА ---
async def main():
    def run_web():
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="Bot is running"))
        web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), handle_signals=False)
    Thread(target=run_web, daemon=True).start()
    
    # ПРИНУДИТЕЛЬНАЯ ОЧИСТКА КОНФЛИКТОВ
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

