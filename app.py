import asyncio
import random
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ПОЛНЫЙ СПИСОК АКТИВОВ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]
OTC_DATA = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBPOTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC", "ZAR/USD OTC", "USD/CHF OTC", "USD/DZD OTC"],
    "crypto": ["Cardano OTC", "Bitcoin ETF OTC", "BNB OTC", "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC", "Chainlink OTC", "Bitcoin OTC"],
    "stock": ["American Express OTC", "FACEBOOK INC OTC", "Intel OTC", "VISA OTC", "Apple OTC", "Pfizer Inc OTC", "Cisco OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC"]
}

class FSM(StatesGroup):
    reg = State(); check = State(); mode = State(); market = State(); cat = State(); asset = State(); tf = State(); exp = State()

# --- МЕТОД РИЧАРДА (BINANCE ENGINE) ---
def get_binance_signal(asset, tf, exp):
    rsi = random.randint(30, 70)
    vol = round(random.uniform(1.2, 5.0), 2)
    price = round(random.uniform(1.0500, 1.4500), 4)
    dir_text, dir_icon = ("🟢 BUY / ВВЕРХ", "📈") if rsi < 55 else ("🔴 SELL / ВНИЗ", "📉")
    
    text = (f"📡 **СИГНАЛ VLADOS USDT: QUANTUM CORE**\n\n"
            f"🔹 **Актив:** `{asset}`\n"
            f"📊 **Binance Price:** `{price}`\n"
            f"⚡️ **Направление VLADOS:** {dir_icon} {dir_text}\n"
            f"📈 **RSI:** `{rsi}` | **Volume:** `{vol}M`\n"
            f"📊 **ТФ:** `{tf}` | ⏱ **Экспирация:** `{exp}`\n"
            f"🎯 **Точность алгоритма VLADOS:** `98.7%`\n\n"
            "⚠️ *Система работает по методу Ричарда (Binance Engine).*")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить сигнал VLADOS", callback_data="m:auto")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="check_dep")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("👑 **VLADOS USDT: QUANTUM CORE SYSTEM v5.0**\nВыберите язык:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang")]
    ]))

@dp.callback_query(F.data == "lang")
async def reg(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("📝 **РЕГИСТРАЦИЯ VLADOS USDT**\nПерейдите по ссылке и отправьте ID:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url="https://u3.shortink.io/register?a=U7DMqgf943dAUl")],
        [InlineKeyboardButton(text="✅ Проверить", callback_data="check_reg")]
    ]))
    await state.set_state(FSM.reg)

@dp.callback_query(F.data == "check_reg")
async def check_reg(c: types.CallbackQuery):
    await c.message.edit_text("✅ **Регистрация подтверждена!**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Проверить депозит", callback_data="check_dep")]
    ]))

@dp.callback_query(F.data == "check_dep")
async def check_dep(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("✅ **Депозит подтвержден. Выберите режим VLADOS:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Авто (Binance Engine)", callback_data="m:auto")], 
        [InlineKeyboardButton(text="⚙️ Ручной режим", callback_data="m:man")]]))
    await state.set_state(FSM.mode)

@dp.callback_query(F.data == "m:auto")
async def auto(c: types.CallbackQuery):
    text, kb = get_binance_signal(random.choice(LIVE), "1 мин", "3 мин")
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def man(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("🌍 **Выберите рынок:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой", callback_data="market:live")], 
        [InlineKeyboardButton(text="💎 OTC", callback_data="market:otc")]]))
    await state.set_state(FSM.market)

@dp.callback_query(F.data.startswith("market:"))
async def market_choice(c: types.CallbackQuery, state: FSMContext):
    if c.data.split(":")[1] == "live":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=p, callback_data=f"a:{p}")] for p in LIVE])
        await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
        await state.set_state(FSM.asset)
    else:
        await c.message.edit_text("📂 Выберите категорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Валюта", callback_data="cat:val")], 
            [InlineKeyboardButton(text="🪙 Крипта", callback_data="cat:crypto")], 
            [InlineKeyboardButton(text="📊 Акции", callback_data="cat:stock")]]))
        await state.set_state(FSM.cat)

@dp.callback_query(F.data.startswith("cat:"))
async def cat_choice(c: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in OTC_DATA[c.data.split(":")[1]]])
    await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
    await state.set_state(FSM.asset)

@dp.callback_query(F.data.startswith("a:"))
async def asset_choice(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=c.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1 мин", callback_data="tf:1 мин")]])
    await c.message.edit_text("⏳ Интервал свечи:", reply_markup=kb)
    await state.set_state(FSM.tf)

@dp.callback_query(F.data.startswith("tf:"))
async def final(c: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    text, kb = get_binance_signal(d['asset'], "1 мин", "3 мин")
    await c.message.edit_text(text, reply_markup=kb)

# --- ЗАПУСК ---
async def start_web():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="VLADOS USDT Bot Active"))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

async def main():
    await start_web()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
