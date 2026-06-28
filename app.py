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

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = 8273386412  # Ваш ID для получения уведомлений о новых ID

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БАЗА ДАННЫХ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]

OTC_GROUPS = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC"],
    "crypto": ["Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", "Litecoin OTC"]
}

class FSM(StatesGroup):
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()
    registration = State()

# --- ЛОГИКА СИГНАЛОВ ---
def generate_signal_ui(asset, tf, exp):
    directions = [("🟢 BUY / ВВЕРХ", "📈"), ("🔴 SELL / ВНИЗ", "📉")]
    dir_text, dir_icon = random.choice(directions)

    import time
    timestamp = int(time.time() + 300)
    
    text = (
        f"🔥 **VLADOS USDT**\n"
        f"📡 **СИГНАЛ TEAM MASTER: QUANTUM CORE**\n\n"
        f"🔷 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
        f"📊 **ТФ:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"⏳ **Вход до:** `{timestamp}`\n"
        f"🎯 **Выплата:** `{random.randint(90, 96)}%`\n"
        f"🔥 **Индекс уверенности:** `{random.randint(93, 98)}%`\n\n"
        "⚠️ *Соблюдайте правила управления капиталом.*"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сгенерировать новый", callback_data=f"regen:{asset}:{tf}:{exp}")],
        [InlineKeyboardButton(text="🔙 Меню активов", callback_data="back_to_assets")]
    ])
    return text, kb

# --- ХЕНДЛЕРЫ ---
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ **Главное меню. Выберите режим:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Автоматический режим", callback_data="m:auto")],
        [InlineKeyboardButton(text="⚙️ Ручной режим", callback_data="m:man")]
    ]))
    await state.set_state(FSM.mode_selection)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇺🇦 UA", callback_data="lang:ua"), InlineKeyboardButton(text="🇩🇪 DE", callback_data="lang:de")]
    ])
    await message.answer("🌐 **Выберите язык / Select Language:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def select_lang(callback: types.CallbackQuery, state: FSMContext):
    text = ("📝 **ШАГ 1: РЕГИСТРАЦИЯ В СИСТЕМЕ**\n\nПосле завершения регистрации, пожалуйста, скопируйте ваш ID (8 цифр) и отправьте его сообщением в этот чат.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", 
            url="https://u3.shortink.io/register?utm_campaign=848831&utm_source=affiliate&utm_medium=sr&a=U7DMqgf943dAUl&al=1768608&ac=vladik_trading&cid=959248&code=WELCOME50"
        )
    ]])
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(FSM.registration)

# ОБРАБОТКА ВВЕДЕННОГО ID С ПОДТВЕРЖДЕНИЕМ
@dp.message(FSM.registration)
async def process_registration(message: types.Message, state: FSMContext):
    user_id_input = message.text.strip()
    
    if not user_id_input.isdigit():
        await message.answer("❌ **Неверный формат ID.** Пожалуйста, отправьте корректный ID, состоящий только из цифр.")
        return

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **Новый пользователь отправил ID на проверку!**\n\n"
                 f"👤 Пользователь: @{message.from_user.username or 'нет юзернейма'}\n"
                 f"🆔 Telegram ID: `{message.from_user.id}`\n"
                 f"📊 ID на платформе: `{user_id_input}`"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")

    await message.answer(
        f"✅ **ID `{user_id_input}` успешно принят на активацию!**\n"
        "Депозит проверяется. Выберите режим работы бота:", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Автомат", callback_data="m:auto")],
            [InlineKeyboardButton(text="⚙️ Ручной", callback_data="m:man")]
        ])
    )
    await state.set_state(FSM.mode_selection)

@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery, state: FSMContext):
    # Заглушка автоматического режима, переводящая пользователя на выбор рынка
    await callback.message.answer("🤖 Автоматический режим активирован.")
    await manual_mode(callback, state)

@dp.callback_query(F.data == "m:man")
async def manual_mode(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🌍 **Выберите рынок:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой", callback_data="market:live")],
        [InlineKeyboardButton(text="💎 OTC", callback_data="market:otc")]
    ]))
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("market:"))
async def market_selected(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}") ] for a in LIVE])
        await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💱 Валюты OTC", callback_data="otc:val")],
            [InlineKeyboardButton(text="⚡️ Крипта OTC", callback_data="otc:crypto")]
        ])
        await callback.message.edit_text("💎 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("otc:"))
async def otc_category_selected(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    assets = OTC_GROUPS.get(category, [])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in assets])
    await callback.message.edit_text("🔹 **Выберите OTC актив:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_selected(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(asset=callback.data.split(":")[1])
    tfs = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in tfs])
    await callback.message.edit_text("⏳ **Выберите интервал:**", reply_markup=kb)
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def timeframe_selected(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tf=callback.data.split(":")[1])
    exps = ["1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in exps])
    await callback.message.edit_text("⏱ **Выберите время экспирации:**", reply_markup=kb)
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def show_final_signal(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    asset = data.get("asset")
    tf = data.get("tf")
    exp = callback.data.split(":")[1]
    
    text, kb = generate_signal_ui(asset, tf, exp)
    await callback.message.edit_text(text, reply_markup=kb)

# --- ДОБАВЛЕННЫЕ ОБРАБОТЧИКИ ДЛЯ КНОПОК ПОД СИГНАЛОМ ---

# 1. Кнопка "Сгенерировать новый"
@dp.callback_query(F.data.startswith("regen:"))
async def regenerate_signal(callback: types.CallbackQuery):
    params = callback.data.split(":")
    asset = params[1]
    tf = params[2]
    exp = params[3]
    
    text, kb = generate_signal_ui(asset, tf, exp)
    await callback.message.edit_text(text, reply_markup=kb)

# 2. Кнопка "Меню активов" (Возврат к началу выбора рынка)
@dp.callback_query(F.data == "back_to_assets")
async def back_to_assets(callback: types.CallbackQuery, state: FSMContext):
    await manual_mode(callback, state)


# --- ЗАПУСК И ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def web_index(request):
    return web.Response(text="Bot is running!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.router.add_get('/', web_index)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
