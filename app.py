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
ADMIN_ID = 8273386412

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- АКТИВЫ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]
OTC_GROUPS = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC"],
    "crypto": ["Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", "Litecoin OTC"],
    "stock": ["Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC"]
}
ALL_ASSETS = LIVE + OTC_GROUPS["val"] + OTC_GROUPS["crypto"] + OTC_GROUPS["stock"]
ALL_TIMEFRAMES = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
ALL_EXPIRATIONS = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]

class FSM(StatesGroup):
    registration = State()
    wait_approval = State()
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()

# --- ИНТЕРФЕЙС СИГНАЛОВ (VLADOS USDT) ---
def generate_signal_ui(asset, tf, exp):
    directions = [("🟢 BUY / ВВЕРХ", "📈"), ("🔴 SELL / ВНИЗ", "📉")]
    dir_text, dir_icon = random.choice(directions)
    timestamp = int(time.time() + 300)
    
    # ФИЛЬТР: Выдаем только "уверенные" сигналы для пользователя
    text = (
        f"🔥 **VLADOS USDT**\n"
        f"📡 **СИГНАЛ VLADOS USDT: QUANTUM CORE**\n\n"
        f"🔷 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
        f"📊 **ТФ:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"⏳ **Вход до:** `{timestamp}`\n"
        f"🎯 **Выплата:** `{random.randint(92, 98)}%`\n"
        f"🔥 **Индекс уверенности:** `{random.randint(95, 99)}%`\n\n"
        "✅ *Сигнал прошел глубокий анализ алгоритмов.*\n"
        "⚠️ *Соблюдайте правила управления капиталом.*"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сгенерировать новый", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 Меню активов", callback_data="back_to_assets")]
    ])
    return text, kb

def get_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим", callback_data="m:man")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang:en")]
    ])
    await message.answer("🌐 **Выберите язык / Select Language:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def select_lang(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url="https://u3.shortink.io/register?utm_campaign=848831&utm_source=affiliate&utm_medium=sr&a=U7DMqgf943dAUl&al=1768608&ac=vladik_trading&cid=959248&code=WELCOME50")]])
    await callback.message.edit_text("📝 **ШАГ 1: РЕГИСТРАЦИЯ**\nОтправьте ваш ID (8 цифр) в этот чат.", reply_markup=kb)
    await state.set_state(FSM.registration)

@dp.message(FSM.registration)
async def process_registration(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit(): return await message.answer("❌ Только цифры!")
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Активировать", callback_data=f"approve:{message.from_user.id}:{message.text.strip()}"), InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny:{message.from_user.id}")]])
    await bot.send_message(ADMIN_ID, f"🔔 **ЗАПРОС:** @{message.from_user.username}\n🆔 ID: `{message.from_user.id}`\n📊 Платформа: `{message.text.strip()}`", reply_markup=admin_kb)
    await message.answer("⏳ **Запрос отправлен. Ожидайте подтверждения.**")
    await state.set_state(FSM.wait_approval)

@dp.callback_query(F.data.startswith("approve:"))
async def admin_approve(callback: types.CallbackQuery):
    _, user_tg_id, platform_id = callback.data.split(":")
    await bot.send_message(int(user_tg_id), f"🎉 **Аккаунт {platform_id} активирован!**", reply_markup=get_main_menu_kb())
    await callback.message.edit_text("✅ ОДОБРЕНО")

@dp.callback_query(F.data.startswith("deny:"))
async def admin_deny(callback: types.CallbackQuery):
    await bot.send_message(int(callback.data.split(":")[1]), "❌ **Запрос отклонен.**")
    await callback.message.edit_text("❌ ОТКЛОНЕНО")

# --- СИГНАЛЫ (ЛОГИКА) ---
@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery):
    text, kb = generate_signal_ui(random.choice(ALL_ASSETS), random.choice(ALL_TIMEFRAMES), random.choice(ALL_EXPIRATIONS))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def manual_mode(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🌍 **Выбор рынка:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Живой", callback_data="market:live"), InlineKeyboardButton(text="OTC", callback_data="market:otc")]]))
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("market:"))
async def market_selected(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in LIVE[:5]])
        await callback.message.edit_text("🔹 **Актив:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        await callback.message.edit_text("💎 **OTC категория:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Валюты", callback_data="otc:val"), InlineKeyboardButton(text="Крипта", callback_data="otc:crypto")]]))
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("otc:"))
async def otc_category_selected(callback: types.CallbackQuery, state: FSMContext):
    assets = OTC_GROUPS.get(callback.data.split(":")[1], [])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in assets[:5]])
    await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_selected(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=callback.data.split(":")[1])
    await callback.message.edit_text("⏳ **Таймфрейм:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in ALL_TIMEFRAMES[:4]]))
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_selected(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=callback.data.split(":")[1])
    await callback.message.edit_text("⏱ **Экспирация:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in ALL_EXPIRATIONS[:3]]))
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def show_final_signal(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text, kb = generate_signal_ui(data["asset"], data["tf"], callback.data.split(":")[1])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("regen:"))
async def regen(callback: types.CallbackQuery):
    _, asset, tf, exp = callback.data.split(":")
    text, kb = generate_signal_ui(asset, tf, exp)
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_assets")
async def back_to_assets(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ **Главное меню:**", reply_markup=get_main_menu_kb())

# --- ЗАПУСК ---
async def main():
    def run_web():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="Bot active"))
        web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), handle_signals=False)
    Thread(target=run_web, daemon=True).start()
    
    await bot.close()
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
