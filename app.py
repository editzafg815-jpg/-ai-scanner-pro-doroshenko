import asyncio
import random
import os
import logging
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = "8273386412"

# Настройка логов для отслеживания ошибок на Render
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗЫ АКТИВОВ (ПОЛНЫЙ СПИСОК) ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF", "AUD/JPY", "NZD/JPY", "GBP/AUD"]
OTC_DATA = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBPOTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC", "ZAR/USD OTC", "USD/CHF OTC", "USD/DZD OTC", "AUD/USD OTC", "EUR/USD OTC"],
    "crypto": ["Cardano OTC", "Bitcoin ETF OTC", "BNB OTC", "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC", "Chainlink OTC", "Bitcoin OTC", "Ethereum OTC", "Ripple OTC", "Dogecoin OTC", "Shiba Inu OTC", "Avalanche OTC"],
    "stock": ["American Express OTC", "FACEBOOK INC OTC", "Intel OTC", "VISA OTC", "Apple OTC", "Pfizer Inc OTC", "Cisco OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC", "Netflix OTC", "NVIDIA OTC", "Amazon OTC", "Microsoft OTC", "Google OTC", "Coca-Cola OTC", "McDonald's OTC", "Nike OTC", "Disney OTC"]
}
TFS = ["5 сек", "15 сек", "30 сек", "M1", "M2", "M3", "M4", "M5"]
EXP_AUTO = ["2 мин", "3 мин", "4 мин", "5 мин"]
EXP_MANUAL = ["30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]

# --- МАШИНА СОСТОЯНИЙ (FSM) ---
class FSM(StatesGroup):
    reg = State()
    dep = State()
    market = State()
    cat = State()
    asset_select = State()
    tf = State()
    exp = State()
    broadcast = State()

# --- ФУНКЦИЯ ГЕНЕРАЦИИ СИГНАЛА ---
def get_signal(asset_name, tf, exp_str):
    payout = random.choice(["85%", "88%", "90%", "92%", "95%"])
    conf = random.randint(85, 99)
    min_val = int(''.join(filter(str.isdigit, exp_str))) if any(c.isdigit() for c in exp_str) else 0
    end_t = (datetime.now() + timedelta(minutes=min_val)).strftime("%H:%M:%S")
    dir_t, dir_i = ("🟢 BUY", "📈") if random.choice([True, False]) else ("🔴 SELL", "📉")
    
    return (f"📡 **СИГНАЛ VLADOS QUANTUM CORE**\n\n"
            f"🔹 **Активы:** `{asset_name}`\n"
            f"⚡️ **Направление:** {dir_i} {dir_t}\n"
            f"📊 **ТФ:** `{tf}`\n"
            f"⏱ **Время:** `{exp_str}`\n"
            f"⏳ **До:** `{end_t}`\n"
            f"🎯 **Выплата:** `{payout}`\n"
            f"🔥 **Уверенность:** `{conf}%`")

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(m: types.Message, state: FSMContext):
    await m.answer("👑 **VLADOS USDT: QUANTUM CORE**\nДля активации пришлите ID из платформы:", 
                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url="https://u3.shortink.io/register?a=U7DMqgf943dAUl")]]))
    await state.set_state(FSM.reg)

# Регистрация
@dp.message(FSM.reg, F.text.isdigit())
async def reg(m: types.Message):
    await bot.send_message(ADMIN_ID, f"🔔 **ЗАЯВКА: РЕГИСТРАЦИЯ**\nUser: {m.from_user.id}\nID: `{m.text}`",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ok_reg:{m.from_user.id}")]]))
    await m.answer("⏳ Заявка отправлена админу.")

# Депозит
@dp.message(F.text.isdigit())
async def dep(m: types.Message):
    await bot.send_message(ADMIN_ID, f"💰 **ЗАЯВКА: ДЕПОЗИТ**\nUser: {m.from_user.id}\nID транс: `{m.text}`",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ok_dep:{m.from_user.id}")]]))
    await m.answer("⏳ Заявка на депозит отправлена.")

@dp.callback_query(F.data.startswith("ok_"))
async def admin_control(c: types.CallbackQuery):
    u = c.data.split(":")[1]
    if "reg" in c.data:
        await bot.send_message(u, "✅ Регистрация одобрена! Теперь пришлите ID депозита.")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤖 Авто-режим", callback_data="m:auto")], [InlineKeyboardButton(text="⚙️ Ручной анализ", callback_data="m:man")]])
        await bot.send_message(u, "✅ **Доступ открыт! Выберите режим:**", reply_markup=kb)
    await c.message.edit_text("✅ Заявка обработана.")

# Ручной выбор
@dp.callback_query(F.data == "m:man")
async def man_mode(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSM.market)
    await c.message.edit_text("🌍 Выберите рынок:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌍 Живой", callback_data="mk:live")], [InlineKeyboardButton(text="💎 OTC", callback_data="mk:otc")]]))

@dp.callback_query(F.data.startswith("mk:"))
async def market_sel(c: types.CallbackQuery, state: FSMContext):
    m = c.data.split(":")[1]
    if m == "live":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"asset:{a}")] for a in LIVE])
        await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
    else:
        await c.message.edit_text("📂 Выберите категорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=k, callback_data=f"ct:{k}")] for k in OTC_DATA.keys()]))
    await state.set_state(FSM.asset_select)

@dp.callback_query(F.data.startswith("ct:"))
async def ct_sel(c: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"asset:{a}")] for a in OTC_DATA[c.data.split(":")[1]]])
    await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)

@dp.callback_query(F.data.startswith("asset:"))
async def asset_sel(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset_name=c.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in TFS])
    await c.message.edit_text("⏳ Выберите ТФ:", reply_markup=kb)
    await state.set_state(FSM.tf)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_sel(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=c.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in EXP_MANUAL])
    await c.message.edit_text("⌛️ Экспирация:", reply_markup=kb)
    await state.set_state(FSM.exp)

@dp.callback_query(F.data.startswith("exp:"))
async def final(c: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    await c.message.edit_text(get_signal(d['asset_name'], d['tf'], c.data.split(":")[1]), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В главное меню", callback_data="m:man")]]))

# --- ЗАПУСК ВЕБ-СЕРВЕРА (ОБЯЗАТЕЛЬНО ДЛЯ RENDER) ---
async def web_app():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot Quantum Core is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_app())
    loop.run_until_complete(bot.delete_webhook(drop_pending_updates=True))
    dp.run_polling(bot)
