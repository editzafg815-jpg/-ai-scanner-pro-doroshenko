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
ADMIN_ID = 8273386412  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ДАННЫЕ ---
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF", "GBP/AUD", "NZD/JPY"]

OTC_GROUPS = {
    "val": ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC"],
    "crypto": ["Bitcoin OTC", "Ethereum OTC", "BNB OTC", "Solana OTC", "Cardano OTC", "Ripple OTC", "Dogecoin OTC", "Polkadot OTC", "Litecoin OTC"],
    "stock": ["Tesla OTC", "Apple OTC", "Facebook OTC", "Amazon OTC", "Google OTC", "Netflix OTC", "Nvidia OTC", "Microsoft OTC"]
}

class FSM(StatesGroup):
    registration = State()
    waiting_for_approve = State()
    mode_selection = State()
    market_selection = State()
    category_selection = State()
    asset_selection = State()
    timeframe_selection = State()
    expiration_selection = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def generate_signal_ui(asset, tf, exp):
    directions = [("🟢 BUY / ВВЕРХ", "📈"), ("🔴 SELL / ВНИЗ", "📉")]
    dir_text, dir_icon = random.choice(directions)

    # Заголовок изменен на твой: VLADOS USDT
    text = (
        f"📡 **СИГНАЛ VLADOS USDT: QUANTUM CORE**\n\n"
        f"🔷 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {dir_icon} {dir_text}\n"
        f"📊 **ТФ:** `{tf}`\n"
        f"⏱ **Экспирация:** `{exp}`\n"
        f"⏳ **Вход до:** {(asyncio.get_event_loop().time() + 300):.0f}\n"
        f"🎯 **Выплата:** `{random.randint(90, 96)}%`\n"
        f"🔥 **Индекс уверенности:** `{random.randint(93, 98)}%`\n\n"
        "⚠️ *Соблюдайте правила управления капиталом.*"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сгенерировать новый", callback_data="m:auto")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="👤 ПОДДЕРЖКА", url="https://t.me/support_link")]
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
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇺🇦 UA", callback_data="lang:ua"), InlineKeyboardButton(text="🇩🇪 DE", callback_data="lang:de")]
    ])
    text = (
        "👑 **TEAM MASTER: QUANTUM CORE SYSTEM v4.5**\n\n"
        "Система инициализирована. Мы анализируем рыночные данные 24/7.\n\n"
        "🌐 **Выберите язык интерфейса:**"
    )
    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSM.mode_selection)
    await callback.message.edit_text("✅ Выберите режим работы:", reply_markup=get_main_menu_kb())

@dp.callback_query(F.data.startswith("lang:"))
async def select_lang(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "📝 **ШАГ 1: РЕГИСТРАЦИЯ В СИСТЕМЕ**\n\n"
        "Для активации торгового ядра пройдите регистрацию по ссылке ниже. "
        "После этого внесите депозит, скопируйте ваш ID и пришлите его боту.\n\n"
        "⏳ *После отправки ID ваша заявка будет проверена модератором.*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url="https://u3.shortink.io/register?utm_campaign=848831&utm_source=affiliate&utm_medium=sr&a=U7DMqgf943dAUl&al=1768608&ac=vladik_trading&cid=959248&code=WELCOME50")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(FSM.registration)

@dp.message(FSM.registration)
async def process_registration(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    entered_id = message.text

    await state.update_data(user_platform_id=entered_id)
    await state.set_state(FSM.waiting_for_approve)

    await message.answer("⏳ **Ваша заявка отправлена на проверку.**\nОжидайте подтверждения регистрации и депозита разработчиком.")

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin:approve:{user_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"admin:decline:{user_id}")
        ]
    ])

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **НОВАЯ ЗАЯВКА НА АКТИВАЦИЮ**\n\n"
             f"👤 Пользователь: {username} (ID: `{user_id}`)\n"
             f"🆔 Введенный ID платформы: `{entered_id}`\n\n"
             f"Проверьте регистрацию и пополнение депозита!",
        reply_markup=admin_kb
    )

@dp.callback_query(F.data.startswith("admin:"))
async def admin_decision(callback: types.CallbackQuery):
    _, action, target_user_id = callback.data.split(":")
    target_user_id = int(target_user_id)
    
    target_state = dp.fsm.resolve_context(bot, chat_id=target_user_id, user_id=target_user_id)

    if action == "approve":
        await target_state.set_state(FSM.mode_selection)
        await bot.send_message(
            chat_id=target_user_id, 
            text="✅ **Ваш депозит и регистрация успешно подтверждены!**\nТорговое ядро активировано. Выберите режим работы:",
            reply_markup=get_main_menu_kb()
        )
        await callback.message.edit_text(callback.message.text + "\n\n🟢 **Одобрено!**")
    
    elif action == "decline":
        await target_state.set_state(FSM.registration)
        await bot.send_message(
            chat_id=target_user_id,
            text="❌ **Заявка отклонена.**\nМодератор не нашёл ваш ID или депозит. Пожалуйста, проверьте данные и пришлите правильный ID заново."
        )
        await callback.message.edit_text(callback.message.text + "\n\n🔴 **Отклонено.**")

@dp.callback_query(F.data == "m:auto")
async def auto_mode(callback: types.CallbackQuery):
    tf_list = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    exp_list = ["2 мин", "3 мин", "4 мин", "5 мин"]
    text, kb = generate_signal_ui(random.choice(LIVE), random.choice(tf_list), random.choice(exp_list))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "m:man")
async def manual_mode(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Живой рынок", callback_data="market:live")],
        [InlineKeyboardButton(text="💎 OTC рынок", callback_data="market:otc")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text("🌍 **Выберите рынок для анализа:**", reply_markup=kb)
    await state.set_state(FSM.market_selection)

@dp.callback_query(F.data.startswith("market:"))
async def market_selected(callback: types.CallbackQuery, state: FSMContext):
    if "live" in callback.data:
        kb_list = [[InlineKeyboardButton(text=asset, callback_data=f"a:{asset}")] for asset in LIVE]
        kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data="m:man")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
        await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
        await state.set_state(FSM.asset_selection)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Валюты", callback_data="cat:val")],
            [InlineKeyboardButton(text="🪙 Крипта", callback_data="cat:crypto")],
            [InlineKeyboardButton(text="📊 Акции", callback_data="cat:stock")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="m:man")]
        ])
        await callback.message.edit_text("📂 **Выберите категорию OTC:**", reply_markup=kb)
        await state.set_state(FSM.category_selection)

@dp.callback_query(F.data.startswith("cat:"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    kb_list = [[InlineKeyboardButton(text=a, callback_data=f"a:{a}")] for a in OTC_GROUPS[cat]]
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data="market:otc")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text("🔹 **Выберите актив:**", reply_markup=kb)
    await state.set_state(FSM.asset_selection)

@dp.callback_query(F.data.startswith("a:"))
async def asset_selected(callback: types.CallbackQuery, state: FSMContext):
    asset = callback.data.split(":")[1]
    await state.update_data(asset=asset)
    
    tfs = ["5 сек", "15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "4 мин", "5 мин"]
    kb_list = [[InlineKeyboardButton(text=t, callback_data=f"tf:{t}")] for t in tfs]
    
    back_callback = "market:live" if not asset.endswith("OTC") else f"cat:{[k for k, v in OTC_GROUPS.items() if asset in v][0]}"
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text("⏳ **Выберите интервал свечи:**", reply_markup=kb)
    await state.set_state(FSM.timeframe_selection)

@dp.callback_query(F.data.startswith("tf:"))
async def tf_selected(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tf = callback.data.split(":")[1]
    await state.update_data(tf=tf)
    
    exps = ["2 мин", "3 мин", "4 мин", "5 мин"]
    kb_list = [[InlineKeyboardButton(text=e, callback_data=f"exp:{e}")] for e in exps]
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"a:{data['asset']}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text("⌛️ **Выберите экспирацию:**", reply_markup=kb)
    await state.set_state(FSM.expiration_selection)

@dp.callback_query(F.data.startswith("exp:"))
async def show_final_signal(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text, kb = generate_signal_ui(data['asset'], data['tf'], callback.data.split(":")[1])
    await callback.message.edit_text(text, reply_markup=kb)

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is running!"))
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logging.info("Starting bot...")
    asyncio.run(main())
