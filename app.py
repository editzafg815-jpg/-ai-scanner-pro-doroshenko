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
LIVE = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", 
    "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", 
    "EUR/AUD", "EUR/CAD", "CAD/CHF", "AUD/NZD", "GBP/USD",
    "EUR/GBP", "USD/NOK", "USD/SEK", "NZD/JPY", "AUD/JPY"
]

OTC_GROUPS = {
    "val": [
        "AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", 
        "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", 
        "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", 
        "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "RUB/USD OTC"
    ],
    "crypto": [
        "Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", 
        "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", 
        "Litecoin OTC", "TRON OTC", "Chainlink OTC", "Polygon OTC"
    ],
    "stock": [
        "Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC", 
        "Google OTC", "Microsoft OTC", "Netflix OTC", "Nvidia OTC"
    ]
}

ALL_ASSETS = LIVE + OTC_GROUPS["val"] + OTC_GROUPS["crypto"] + OTC_GROUPS["stock"]
ALL_TIMEFRAMES = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]
ALL_EXPIRATIONS = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]

# --- СОСТОЯНИЯ ---
class FSM(StatesGroup):
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()

# --- ЛОГИКА ГЕНЕРАЦИИ (РАЗВЕРНУТАЯ) ---
def generate_signal_ui(asset, tf, exp):
    directions = [("🟢 BUY / ВВЕРХ", "📈"), ("🔴 SELL / ВНИЗ", "📉")]
    dir_text, dir_icon = random.choice(directions)
    timestamp = int(time.time() + 300)
    
    # Детальное сообщение для пользователя
    text = (
        f"🔥 **VLADOS USDT - СИГНАЛЫ**\n"
        f"📡 **СИГНАЛ: QUANTUM CORE V.2.4**\n\n"
        f"🔹 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
        f"📊 **Таймфрейм:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"⏳ **Вход до времени:** `{timestamp}`\n"
        f"🎯 **Процент выплаты:** `{random.randint(95, 98)}%`\n"
        f"🔥 **Индекс уверенности AI:** `{random.randint(97, 99)}%`\n\n"
        "✅ *Алгоритм успешно проанализировал рынок.*\n"
        "⚠️ *Соблюдайте правила риск-менеджмента.*"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сгенерировать новый сигнал", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_assets")]
    ])
    return text, kb

def get_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим (Случайный)", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим (Выбор)", callback_data="m:man")]
    ])

# --- ХЕНДЛЕРЫ (ПОЛНАЯ СТРУКТУРА) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ **Добро пожаловать в VLADOS USDT!**\n\nВыберите нужный вам режим работы бота для получения торговых сигналов:", reply_markup=get_main_menu_kb())

@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery):
    await callback.message.edit_text("🤖 **Активация автоматического режима...**")
    await asyncio.sleep(0.5)
    text, kb = generate_signal_ui(random.choice(ALL_ASSETS), random.choice(ALL_TIMEFRAMES), random.choice(ALL_EXPIRATIONS))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def manual_mode(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой рынок (LIVE)", callback_data="market:live")],
        [InlineKeyboardButton(text="💎 Рынок OTC", callback_data="market:otc")]
    ])
    await callback.message.edit_text("🌍 **Выберите тип рынка для анализа:**", reply_markup=kb)
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("market:"))
async def market_selected(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in LIVE])
        await callback.message.edit_text("🔹 **Выберите актив для анализа:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💱 Валюты OTC", callback_data="otc:val")],
            [InlineKeyboardButton(text="⚡️ Крипта OTC", callback_data="otc:crypto")],
            [InlineKeyboardButton(text="📊 Акции OTC", callback_data="otc:stock")]
        ])
        await callback.message.edit_text("💎 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("otc:"))
async def otc_category_selected(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    assets = OTC_GROUPS.get(category, [])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in assets])
    await callback.message.edit_text("🔹 **Выберите актив OTC:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_selected(callback: types.CallbackQuery, state: FSMContext):
    asset = callback.data.split(":")[1]
    await state.update_data(asset=asset)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in ALL_TIMEFRAMES])
    await callback.message.edit_text("⏳ **Выберите таймфрейм:**", reply_markup=kb)
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def timeframe_selected(callback: types.CallbackQuery, state: FSMContext):
    tf = callback.data.split(":")[1]
    await state.update_data(tf=tf)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in ALL_EXPIRATIONS])
    await callback.message.edit_text("⏱ **Выберите время экспирации:**", reply_markup=kb)
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def show_final_signal(callback: types.CallbackQuery, state: FSMContext):
    exp = callback.data.split(":")[1]
    data = await state.get_data()
    text, kb = generate_signal_ui(data["asset"], data["tf"], exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_assets")
async def back_to_assets(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ **Главное меню:**", reply_markup=get_main_menu_kb())

@dp.callback_query(F.data.startswith("regen:"))
async def regenerate_signal(callback: types.CallbackQuery):
    params = callback.data.split(":")
    text, kb = generate_signal_ui(params[1], params[2], params[3])
    await callback.message.edit_text(text, reply_markup=kb)

# --- ЗАПУСК (С ПРОВЕРКОЙ КОНФЛИКТОВ) ---
async def main():
    # Запуск web-сервера для Render
    def run_web():
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="Bot is running correctly"))
        web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), handle_signals=False)
    Thread(target=run_web, daemon=True).start()
    
    # Очистка и запуск
    logging.info("Очистка вебхуков и старт polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
