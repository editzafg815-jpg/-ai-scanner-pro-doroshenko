import os
import asyncio
import hashlib
import logging
import random
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- 1. КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8836797898:AAHhtUHiRWoYmsFJ16ur4-UxkgKkB5rwJnw"
ADMIN_ID = 8273386412
PLATFORM_URL = "https://u3.shortink.io/register?utm_campaign=848831&utm_source=affiliate&utm_medium=sr&a=U7DMqgf943dAUl&al=1768608&ac=vladik_trading&cid=959248&code=WELCOME50"
SUPPORT_URL = "https://t.me/andriddddd"

# --- БАЗЫ АКТИВОВ (ПОДЕЛЕНЫ НА ТРИ ГРУППЫ КАК В СКРИНШОТЕ) ---
LIVE_CURRENCIES = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD"]

OTC_GROUPS = {
    "currency": [
        "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "USD/CAD OTC",
        "EUR/GBP OTC", "EUR/JPY OTC", "USD/CHF OTC", "GBP/JPY OTC"
    ],
    "crypto": [
        "Bitcoin OTC", "Ethereum OTC", "Cardano OTC", "BNB OTC", "Polkadot OTC", 
        "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC"
    ],
    "stock": [
        "Tesla OTC", "Apple OTC", "Google OTC", "Alibaba OTC", "Intel OTC", 
        "VISA OTC", "American Express OTC", "FACEBOOK INC OTC"
    ]
}

# Все пары для автоматического режима (живой рынок)
ALL_PAIRS = LIVE_CURRENCIES + OTC_GROUPS["currency"] + OTC_GROUPS["crypto"] + OTC_GROUPS["stock"]

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CORE] - %(message)s')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SignalStates(StatesGroup):
    choosing_market = State()  
    choosing_cat = State()     
    choosing_asset = State()   
    choosing_exp = State()     

# --- 3. МАТЕМАТИЧЕСКИЙ АНАЛИЗАТОР (ТЕПЕРЬ ДАЕТ И ВВЕРХ, И ВНИЗ) ---
class MathAnalyzer:
    def get_signal(self, asset: str):
        now = datetime.now()
        h = hashlib.md5(f"{now.strftime('%H%M%S')}:{asset}:{random.randint(1, 1000)}".encode()).hexdigest()
        trend_val = int(h[:4], 16) % 100 
        
        # Исправлено: 50% шанс получить BUY (ВВЕРХ) или SELL (ВНИЗ)
        if trend_val > 50:
            direction = "📈 🟢 BUY / ВВЕРХ"
        else:
            direction = "📉 🔴 SELL / ВНИЗ"
            
        tf = "M5" if trend_val % 2 == 0 else "M1"
        duration = 2 + (trend_val % 4)
        finish_time = (now + timedelta(minutes=duration)).strftime("%H:%M:%S")
        payout = "92%" if trend_val > 30 else "87%"
        confidence = 88 + (trend_val % 12)
        if confidence > 98: confidence = 95
        return direction, tf, duration, finish_time, payout, confidence

analyzer = MathAnalyzer()

# --- 4. КЛАВИАТУРЫ ---
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇺🇦 UA", callback_data="lang:ua"), InlineKeyboardButton(text="🇩🇪 DE", callback_data="lang:de")]
    ])

def register_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url=PLATFORM_URL)]
    ])

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 ПОЛУЧИТЬ КВАНТОВЫЙ СИГНАЛ", callback_data="get_sig")],
        [InlineKeyboardButton(text="⚙️ РУЧНОЙ РЕЖИМ (ОТС)", callback_data="manual_mode")],
        [InlineKeyboardButton(text="👨‍💻 ПОДДЕРЖКА", url=SUPPORT_URL)]
    ])

# Клавиатура авто-сигнала (Перекрытие и Назад вместо Поддержки)
def signal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ПОЛУЧИТЬ КВАНТОВЫЙ СИГНАЛ", callback_data="get_sig")],
        [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back_to_main")]
    ])

# --- 5. ХЕНДЛЕРЫ СТАРТА И ВЕРИФИКАЦИИ ---

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(
        "👑 **VLADOS USDT: QUANTUM CORE SYSTEM v4.5**\n\n"
        "Система инициализирована. Мы анализируем рыночные данные 24/7 для поиска оптимальных точек входа.\n\n"
        "🌐 **Выберите язык / Select your language:**", 
        reply_markup=lang_kb()
    )

@dp.callback_query(F.data.startswith("lang:"))
async def select_lang(c: types.CallbackQuery):
    await c.message.edit_text(
        "📝 **ШАГ 1: РЕГИСТРАЦИЯ В СИСТЕМЕ**\n\n"
        "Для обеспечения синхронизации вашего торгового аккаунта с нашим квантовым ядром, вы обязаны пройти регистрацию по партнерской ссылке.\n\n"
        "После завершения регистрации, пожалуйста, скопируйте ваш ID и отправьте его в этот чат.",
        reply_markup=register_kb()
    )

@dp.message(F.text.isdigit())
async def auth_request(m: types.Message):
    user_id = m.from_user.id
    username = f"@{m.from_user.username}" if m.from_user.username else "Нет юзернейма"
    provided_id = m.text
    
    await m.answer("⏳ **Ваш ID отправлен на верификацию.** Ожидайте подтверждения администратором...")
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_accept:{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_decline:{user_id}")
        ]
    ])
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **НОВАЯ ЗАЯВКА НА ТОРГОВОГО РОБОТА!**\n\n"
             f"👤 Пользователь: {username} (TG ID: `{user_id}`)\n"
             f"🆔 Указанный ID платформы: `{provided_id}`\n\n"
             f"Выберите действие:",
        reply_markup=admin_markup
    )

@dp.callback_query(F.data.startswith("adm_accept:"))
async def admin_accept(c: types.CallbackQuery):
    target_user_id = int(c.data.split(":")[1])
    await c.answer("Пользователь одобрен!")
    await c.message.edit_text(c.message.text + "\n\n🟢 **Одобрено!** Пользователь получил доступ.")
    
    try:
        await bot.send_message(chat_id=target_user_id, text="✅ **Синхронизация успешна! Доступ активен.**", reply_markup=main_kb())
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

@dp.callback_query(F.data.startswith("adm_decline:"))
async def admin_decline(c: types.CallbackQuery):
    target_user_id = int(c.data.split(":")[1])
    await c.answer("Пользователь отклонен.")
    await c.message.edit_text(c.message.text + "\n\n🔴 **Отклонено.** Доступ заблокирован.")
    
    try:
        await bot.send_message(chat_id=target_user_id, text="❌ **Ошибка: ID не найден в базе данных квантового ядра.**")
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

# --- 6. АВТОМАТИЧЕСКИЙ РЕЖИМ (ЖИВОЙ РЫНОК С КНОПКОЙ НАЗАД) ---
@dp.callback_query(F.data == "get_sig")
async def get_sig(c: types.CallbackQuery):
    asset = random.choice(ALL_PAIRS)
    direction, tf, duration, finish, payout, conf = analyzer.get_signal(asset)
    
    signal = (
        f"📡 **СИГНАЛ VLADOS USDT**\n\n"
        f"🔹 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {direction}\n"
        f"📊 **ТФ:** `{tf}`\n"
        f"⏱ **Экспирация:** `{duration} мин`\n"
        f"⏳ **Вход до:** `{finish}`\n"
        f"🎯 **Выплата:** `{payout}`\n"
        f"🔥 **Индекс уверенности:** `{conf}%`\n\n"
        "⚠️ *Соблюдайте риски.*"
    )
    await c.message.edit_text(signal, reply_markup=signal_kb())

# --- 7. РУЧНОЙ РЕЖИМ (ВЫБОР ИЗ ТРЕХ СПИСКОВ) ---
@dp.callback_query(F.data == "manual_mode")
async def manual_mode(c: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Валюта (OTC)", callback_data="m_cat:currency")],
        [InlineKeyboardButton(text="🪙 Крипта (OTC)", callback_data="m_cat:crypto")],
        [InlineKeyboardButton(text="📊 Акции (OTC)", callback_data="m_cat:stock")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    await c.message.edit_text("📂 **РУЧНОЙ РЕЖИМ.** Выберите категорию активов для анализа:", reply_markup=kb)
    await state.set_state(SignalStates.choosing_cat)

@dp.callback_query(SignalStates.choosing_cat, F.data.startswith("m_cat:"))
async def manual_select_asset(c: types.CallbackQuery, state: FSMContext):
    cat = c.data.split(":")[1]
    assets = OTC_GROUPS[cat]
    
    buttons = []
    for i in range(0, len(assets), 2):
        row = [InlineKeyboardButton(text=assets[i], callback_data=f"m_as:{assets[i]}")]
        if i + 1 < len(assets):
            row.append(InlineKeyboardButton(text=assets[i+1], callback_data=f"m_as:{assets[i+1]}"))
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="manual_mode")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("🔹 **Выберите торговый актив:**", reply_markup=kb)
    await state.set_state(SignalStates.choosing_asset)

@dp.callback_query(SignalStates.choosing_asset, F.data.startswith("m_as:"))
async def manual_select_exp(c: types.CallbackQuery, state: FSMContext):
    asset = c.data.split(":")[1]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 мин", callback_data=f"m_ex:{asset}:1"), InlineKeyboardButton(text="2 мин", callback_data=f"m_ex:{asset}:2")],
        [InlineKeyboardButton(text="3 мин", callback_data=f"m_ex:{asset}:3"), InlineKeyboardButton(text="5 мин", callback_data=f"m_ex:{asset}:5")],
        [InlineKeyboardButton(text="🔙 К выбору актива", callback_data="manual_mode")]
    ])
    await c.message.edit_text(f"⏳ **Актив:** `{asset}`\nВыберите время экспирации:", reply_markup=kb)
    await state.set_state(SignalStates.choosing_exp)

@dp.callback_query(SignalStates.choosing_exp, F.data.startswith("m_ex:"))
async def manual_final_signal(c: types.CallbackQuery, state: FSMContext):
    _, asset, exp = c.data.split(":")
    direction, tf, _, finish, payout, conf = analyzer.get_signal(asset)
    
    finish = (datetime.now() + timedelta(minutes=int(exp))).strftime("%H:%M:%S")
    
    signal = (
        f"📡 **СИГНАЛ VLADOS USDT**\n\n"
        f"🔹 **Актив:** `{asset}`\n"
        f"⚡️ **Направление:** {direction}\n"
        f"📊 **ТФ:** `M1`\n"
        f"⏱ **Экспирация:** `{exp} мин`\n"
        f"⏳ **Вход до:** `{finish}`\n"
        f"🎯 **Выплата:** `{payout}`\n"
        f"🔥 **Индекс уверенности:** `{conf}%`\n\n"
        "⚠️ *Соблюдайте риски.*"
    )
    
    # Кнопка назад возвращает строго в ручной режим
    manual_signal_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 ОБНОВИТЬ СИГНАЛ", callback_data=f"m_as:{asset}")],
        [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="manual_mode")]
    ])
    
    await c.message.edit_text(signal, reply_markup=manual_signal_kb)
    await state.clear()

# --- 8. НАВИГАЦИЯ НАЗАД В ГЛАВНОЕ МЕНЮ ---
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(c: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text(
        "👑 **VLADOS USDT: QUANTUM CORE SYSTEM v4.5**\n\n"
        "Система инициализирована. Мы анализируем рыночные данные 24/7.",
        reply_markup=main_kb()
    )

# --- 9. WEB СЕРВЕР И ЗАПУСК ---
async def web_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()

async def main():
    await asyncio.gather(web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
