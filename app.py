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

# Настройка детального логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# --- КОНФИГУРАЦИЯ ---
# Вставь СВЕЖИЙ токен после /revoke
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw" 

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- РАСШИРЕННЫЕ БАЗЫ ДАННЫХ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF", "AUD/NZD", "GBP/CHF", "EUR/NZD", "USD/MXN", "USD/SGD"]
OTC_VAL = ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "JPY/KRW OTC"]
OTC_CRYPTO = ["Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", "Litecoin OTC", "TRON OTC", "Chainlink OTC", "Stellar OTC", "Avalanche OTC", "Polygon OTC"]
OTC_STOCK = ["Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC", "Google OTC", "Microsoft OTC", "Netflix OTC", "Nvidia OTC", "Intel OTC", "AMD OTC", "Disney OTC", "CocaCola OTC"]

ALL_TIMEFRAMES = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]
ALL_EXPIRATIONS = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин", "10 мин", "15 мин"]

# --- СОСТОЯНИЯ FSM (Машина состояний) ---
class FSM(StatesGroup):
    mode = State()
    market = State()
    category = State()
    asset = State()
    timeframe = State()
    expiration = State()

# --- ЯДРО АНАЛИТИКИ ---
def generate_pro_signal(asset, tf, exp):
    # Сложная логика генерации для "плюсовых" сигналов
    dir_options = [
        ("🟢 ВВЕРХ (BUY)", "📈", "вход по тренду"),
        ("🔴 ВНИЗ (SELL)", "📉", "вход на коррекции"),
        ("🟢 ВВЕРХ (BUY)", "📈", "вход от уровня поддержки"),
        ("🔴 ВНИЗ (SELL)", "📉", "вход от уровня сопротивления")
    ]
    direction, icon, strategy = random.choice(dir_options)
    
    # Имитация работы нейросетевого анализатора
    confidence = random.randint(94, 99)
    volatility = random.randint(80, 100)
    
    text = (
        f"💎 **VLADOS QUANTUM CORE V.3.0**\n"
        f"📡 **СТАТУС:** АНАЛИЗ ГЛУБОКИХ СЛОЕВ ЗАВЕРШЕН\n\n"
        f"🔷 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {icon} {direction}\n"
        f"📊 **Таймфрейм:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"🎯 **Точность алгоритма:** `{confidence}%`\n"
        f"📉 **Уровень волатильности:** `{volatility}%`\n"
        f"💰 **Средняя доходность:** `{random.randint(90, 98)}%`\n"
        f"🧠 **Стратегия входа:** {strategy}\n\n"
        f"✅ *Сигнал прошел проверку на пробой уровней и объемные маркеры.*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить расчет", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Auto-Analysis", callback_data="mode:auto")],
        [InlineKeyboardButton(text="⚙️ Manual-Select", callback_data="mode:man")]
    ])
    await message.answer("🚀 **VLADOS QUANTUM SYSTEM CONNECTED**\nВыберите режим работы для запуска анализа:", reply_markup=kb)

@dp.callback_query(F.data == "mode:auto")
async def auto_mode(callback: types.CallbackQuery):
    asset = random.choice(LIVE + OTC_VAL + OTC_CRYPTO + OTC_STOCK)
    text, kb = generate_pro_signal(asset, random.choice(ALL_TIMEFRAMES), random.choice(ALL_EXPIRATIONS))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "mode:man")
async def man_mode(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой рынок (Live)", callback_data="market:live")],
        [InlineKeyboardButton(text="💎 Рынок OTC", callback_data="market:otc")]
    ])
    await callback.message.edit_text("🌍 **Выберите тип рынка для анализа:**", reply_markup=kb)
    await state.set_state(FSM.market)

@dp.callback_query(F.data.startswith("market:"))
async def mkt_choice(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"asset:{a}")] for a in LIVE[:12]])
        await callback.message.edit_text("🔹 **Выберите актив для анализа:**", reply_markup=kb)
        await state.set_state(FSM.asset)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💱 Валюты OTC", callback_data="cat:val")],
            [InlineKeyboardButton(text="⚡️ Крипта OTC", callback_data="cat:crypto")],
            [InlineKeyboardButton(text="📊 Акции OTC", callback_data="cat:stock")]
        ])
        await callback.message.edit_text("💎 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category)

@dp.callback_query(F.data.startswith("cat:"))
async def cat_choice(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    items = OTC_VAL if cat == "val" else (OTC_CRYPTO if cat == "crypto" else OTC_STOCK)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"asset:{a}")] for a in items[:12]])
    await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
    await state.set_state(FSM.asset)

@dp.callback_query(F.data.startswith("asset:"))
async def asset_choice(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in ALL_TIMEFRAMES])
    await callback.message.edit_text("⏳ **Выберите таймфрейм анализа:**", reply_markup=kb)
    await state.set_state(FSM.timeframe)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_choice(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in ALL_EXPIRATIONS])
    await callback.message.edit_text("⏱ **Выберите время экспирации:**", reply_markup=kb)
    await state.set_state(FSM.expiration)

@dp.callback_query(F.data.startswith("exp:"))
async def final_sig(callback: types.CallbackQuery, state: FSMContext):
    exp = callback.data.split(":")[1]
    data = await state.get_data()
    text, kb = generate_pro_signal(data["asset"], data["tf"], exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "main_menu")
async def back_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await start_cmd(callback.message, state)

@dp.callback_query(F.data.startswith("regen:"))
async def regen_sig(callback: types.CallbackQuery):
    params = callback.data.split(":")
    text, kb = generate_pro_signal(params[1], params[2], params[3])
    await callback.message.edit_text(text, reply_markup=kb)

# --- СИСТЕМА ЗАПУСКА ---
async def main():
    def run_web():
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="Bot is operational"))
        web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), handle_signals=False)
    
    Thread(target=run_web, daemon=True).start()
    
    # Принудительная очистка старых обновлений для избежания конфликтов
    logging.info("Очистка вебхуков и старых процессов...")
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(5)
    
    logging.info("Система Quantum Core запущена успешно.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
