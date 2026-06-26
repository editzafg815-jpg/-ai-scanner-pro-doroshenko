import asyncio
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ДАННЫЕ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]
OTC_DATA = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBPOTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC", "ZAR/USD OTC", "USD/CHF OTC", "USD/DZD OTC"],
    "crypto": ["Cardano OTC", "Bitcoin ETF OTC", "BNB OTC", "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC", "Chainlink OTC", "Bitcoin OTC"],
    "stock": ["American Express OTC", "FACEBOOK INC OTC", "Intel OTC", "VISA OTC", "Apple OTC", "Pfizer Inc OTC", "Cisco OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC"]
}

class FSM(StatesGroup):
    reg = State()
    check = State() # Состояние для проверки
    mode = State()
    market = State()
    cat = State()
    asset = State()
    tf = State()
    exp = State()

# --- ФУНКЦИИ ---
def sig_text(asset, tf, exp):
    dir_text, dir_icon = random.choice([("🟢 BUY / ВВЕРХ", "📈"), ("🔴 SELL / ВНИЗ", "📉")])
    text = (f"📡 **СИГНАЛ TEAM MASTER**\n\n"
            f"🔷 **Актив:** `{asset}`\n"
            f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
            f"📊 **ТФ:** `{tf}`\n"
            f"⏱ **Экспирация:** `{exp}`\n"
            f"⏳ **Вход до:** {(asyncio.get_event_loop().time() + 300):.0f}\n"
            f"🎯 **Выплата:** `{random.randint(90, 96)}%`\n"
            f"🔥 **Индекс уверенности:** `{random.randint(93, 98)}%`\n\n"
            "⚠️ *Соблюдайте риски.*")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 ПОЛУЧИТЬ КВАНТОВЫЙ СИГНАЛ", callback_data="m:auto")],
        [InlineKeyboardButton(text="👤 ПОДДЕРЖКА", url="https://t.me/support_link")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(m: types.Message):
    text = ("👑 **TEAM MASTER: QUANTUM CORE SYSTEM v4.5**\n\n"
            "Система инициализирована. Выберите язык:")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang")],
        [InlineKeyboardButton(text="🇺🇦 UA", callback_data="lang"), InlineKeyboardButton(text="🇩🇪 DE", callback_data="lang")]
    ])
    await m.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "lang")
async def reg(c: types.CallbackQuery, state: FSMContext):
    text = ("📝 **ШАГ 1: РЕГИСТРАЦИЯ**\n\n"
            "Зарегистрируйтесь по ссылке и отправьте ID (8273386412):")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url="https://u3.shortink.io/register?utm_campaign=848831&utm_source=affiliate&utm_medium=sr&a=U7DMqgf943dAUl&al=1768608&ac=vladik_trading&cid=959248&code=WELCOME50")],
        [InlineKeyboardButton(text="✅ Проверить регистрацию", callback_data="check_reg")]
    ])
    await c.message.edit_text(text, reply_markup=kb)
    await state.set_state(FSM.reg)

@dp.callback_query(F.data == "check_reg")
async def check_reg(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("🔄 Проверка регистрации... \n✅ Регистрация подтверждена! Теперь пополните депозит.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="💰 Проверить депозит", callback_data="check_dep")]
                             ]))
    await state.set_state(FSM.check)

@dp.callback_query(F.data == "check_dep")
async def check_dep(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("✅ **Депозит подтвержден. Выберите режим:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автомат", callback_data="m:auto")], 
        [InlineKeyboardButton(text="⚙️ Ручной", callback_data="m:man")]]))
    await state.set_state(FSM.mode)

# --- Остальная логика (авто/ручной) остается без изменений ---
@dp.callback_query(F.data == "m:auto")
async def auto(c: types.CallbackQuery):
    intervals = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    expirations = ["2 мин", "3 мин", "4 мин", "5 мин"]
    text, kb = sig_text(random.choice(LIVE), random.choice(intervals), random.choice(expirations))
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def man(c: types.CallbackQuery, state: FSMContext):
    await c.message.edit_text("🌍 Выберите рынок:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
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
async def tf_choice(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=c.data.split(":")[1])
    intervals = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f"tf:{i}")] for i in intervals])
    await c.message.edit_text("⏳ Интервал свечи:", reply_markup=kb)
    await state.set_state(FSM.tf)

@dp.callback_query(F.data.startswith("tf:"))
async def exp_choice(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=c.data.split(":")[1])
    expirations = ["2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in expirations])
    await c.message.edit_text("⌛️ Экспирация:", reply_markup=kb)
    await state.set_state(FSM.exp)

@dp.callback_query(F.data.startswith("exp:"))
async def final(c: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    text, kb = sig_text(d['asset'], d['tf'], c.data.split(":")[1])
    await c.message.edit_text(text, reply_markup=kb)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
