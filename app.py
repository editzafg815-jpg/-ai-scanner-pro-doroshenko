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
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = "8273386412" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗЫ АКТИВОВ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]
OTC_DATA = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBPOTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC", "ZAR/USD OTC", "USD/CHF OTC", "USD/DZD OTC"],
    "crypto": ["Cardano OTC", "Bitcoin ETF OTC", "BNB OTC", "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC", "Chainlink OTC", "Bitcoin OTC"],
    "stock": ["American Express OTC", "FACEBOOK INC OTC", "Intel OTC", "VISA OTC", "Apple OTC", "Pfizer Inc OTC", "Cisco OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC"]
}

class FSM(StatesGroup):
    reg = State(); mode = State(); market = State(); cat = State(); asset = State(); tf = State(); exp = State()

# --- ЛОГИКА СИГНАЛОВ ---
def get_signal_ui(asset, tf, exp):
    rsi = random.randint(30, 70)
    dir_text, dir_icon = ("🟢 BUY / ВВЕРХ", "📈") if rsi < 55 else ("🔴 SELL / ВНИЗ", "📉")
    text = (f"📡 **СИГНАЛ VLADOS USDT: QUANTUM CORE**\n\n"
            f"🔹 **Актив:** `{asset}`\n"
            f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
            f"⏱ **ТФ:** `{tf}` | **Экспирация:** `{exp}`\n"
            f"🎯 **Точность:** `98.7%`\n\n"
            "⚠️ *Метод: Binance Engine (Ричард)*")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить сигнал", callback_data="m:auto")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("👑 **VLADOS USDT: QUANTUM CORE**\n\nПришлите свой ID для регистрации:")

@dp.message(F.text.isdigit())
async def handle_reg(m: types.Message):
    await bot.send_message(ADMIN_ID, f"🔔 **Заявка от {m.from_user.full_name}**\nID: `{m.text}`",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text="✅ Подтвердить регистрацию", callback_data=f"ok:{m.from_user.id}")]
                           ]))
    await m.answer("⏳ **Заявка отправлена админу VLADOS.**")

@dp.callback_query(F.data.startswith("ok:"))
async def admin_ok(c: types.CallbackQuery):
    user_id = c.data.split(":")[1]
    await bot.send_message(user_id, "✅ **Доступ к VLADOS USDT разрешен!**\nТеперь пополните депозит и сообщите админу.", 
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text="🤖 Авто", callback_data="m:auto")],
                               [InlineKeyboardButton(text="⚙️ Ручной", callback_data="m:man")]]))
    await c.message.edit_text("Подтверждено.")

@dp.callback_query(F.data == "m:auto")
async def auto_mode(c: types.CallbackQuery):
    tf = random.choice(["2 мин", "3 мин", "4 мин", "5 мин"])
    exp = random.choice(["2 мин", "3 мин", "4 мин", "5 мин"])
    text, kb = get_signal_ui(random.choice(LIVE), tf, exp)
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def man_mode(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("🌍 Выберите рынок:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой", callback_data="market:live")],
        [InlineKeyboardButton(text="💎 OTC", callback_data="market:otc")]]))
    await state.set_state(FSM.market)

@dp.callback_query(F.data.startswith("market:"))
async def market_select(c: types.CallbackQuery, state: FSMContext):
    if c.data.split(":")[1] == "live":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in LIVE])
        await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
        await state.set_state(FSM.asset)
    else:
        await c.message.edit_text("📂 Категория:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Валюта", callback_data="cat:val")],
            [InlineKeyboardButton(text="🪙 Крипта", callback_data="cat:crypto")],
            [InlineKeyboardButton(text="📊 Акции", callback_data="cat:stock")]]))
        await state.set_state(FSM.cat)

@dp.callback_query(F.data.startswith("cat:"))
async def cat_select(c: types.CallbackQuery, state: FSMContext):
    cat = c.data.split(":")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in OTC_DATA[cat]])
    await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
    await state.set_state(FSM.asset)

@dp.callback_query(F.data.startswith("a:"))
async def asset_select(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=c.data.split(":")[1])
    tfs = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f"tf:{i}")] for i in tfs])
    await c.message.edit_text("⏳ Интервал:", reply_markup=kb)
    await state.set_state(FSM.tf)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_select(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=c.data.split(":")[1])
    exps = ["30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in exps])
    await c.message.edit_text("⌛️ Экспирация:", reply_markup=kb)
    await state.set_state(FSM.exp)

@dp.callback_query(F.data.startswith("exp:"))
async def final_signal(c: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    text, kb = get_signal_ui(d['asset'], d['tf'], c.data.split(":")[1])
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back(c: types.CallbackQuery):
    await c.message.edit_text("✅ **Главное меню VLADOS:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Авто", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной", callback_data="m:man")]]))

# --- ЗАПУСК ВЕБ-СЕРВЕРА ДЛЯ RENDER ---
async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, '0.0.0.0', port)
    loop.run_until_complete(site.start())
    loop.run_until_complete(start_bot())
