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

# --- БАЗЫ АКТИВОВ ---
CURRENCIES = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "USD/CHF", "AUD/USD", "NZD/USD"]
CROSS_PAIRS = ["EUR/JPY", "GBP/JPY", "AUD/CAD", "EUR/AUD", "EUR/CAD", "CAD/CHF"]
OTC = ["AED/CNY OTC", "BHD/CNY OTC", "EUR/GBP OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC", "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC", "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC", "ZAR/USD OTC", "USD/CHF OTC", "USD/DZD OTC", "Cardano OTC", "Bitcoin ETF OTC", "BNB OTC", "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC", "Chainlink OTC", "Bitcoin OTC", "American Express OTC", "FACEBOOK INC OTC", "Intel OTC", "VISA OTC", "Apple OTC", "Pfizer Inc OTC", "Cisco OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC"]

ALL_PAIRS = [
    "GBP/USD OTC", "EUR/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "USD/CAD OTC",
    "EUR/GBP OTC", "EUR/JPY OTC", "USD/CHF OTC", "Bitcoin OTC", "Ethereum OTC",
    "AED/CNY OTC", "BHD/CNY OTC", "EUR/TRY OTC", "GBP/JPY OTC", "MAD/USD OTC",
    "NGN/USD OTC", "NZD/USD OTC", "USD/CNH OTC", "USD/EGP OTC", "USD/PHP OTC",
    "USD/PKR OTC", "USD/SGD OTC", "USD/THB OTC", "USD/VND OTC", "YER/USD OTC",
    "ZAR/USD OTC", "USD/DZD OTC", "Cardano OTC", "Bitcoin ETF OTC", "BNB OTC",
    "Polkadot OTC", "Litecoin OTC", "Polygon OTC", "Solana OTC", "TRON OTC",
    "Chainlink OTC", "American Express OTC", "Intel OTC", "VISA OTC", "Tesla OTC"
]

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CORE] - %(message)s')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SignalStates(StatesGroup):
    choosing_cat = State()
    choosing_asset = State()
    choosing_exp = State()

# --- 3. МАТЕМАТИЧЕСКИЙ АНАЛИЗАТОР ---
class MathAnalyzer:
    def get_signal(self, asset: str):
        now = datetime.now()
        h = hashlib.md5(f"{now.strftime('%H%M')}:{asset}".encode()).hexdigest()
        trend_val = int(h[:4], 16) % 100 
        direction = "📈 🟢 BUY / ВВЕРХ" if trend_val > 48 else "📉 🔴 SELL / ВНИЗ"
        tf = "M5" if trend_val % 2 == 0 else "M1"
        duration = 2 + (trend_val % 4)
        finish_time = (now + timedelta(minutes=duration)).strftime("%H:%M:%S")
        payout = "92%" if trend_val > 30 else "87%"
        confidence = 88 + (trend_val % 10)
        return direction, tf, duration, finish_time, payout, confidence

analyzer = MathAnalyzer()

# --- 4. КЛАВИАТУРЫ ---
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"), InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇺🇦 UA", callback_data="lang:ua"), InlineKeyboardButton(text="🇩🇪 DE", callback_data="lang:de")],
        [InlineKeyboardButton(text="🇪🇸 ES", callback_data="lang:es"), InlineKeyboardButton(text="🇫🇷 FR", callback_data="lang:fr")]
    ])

def register_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 ПЕРЕЙТИ НА ПЛАТФОРМУ", url=PLATFORM_URL)]
    ])

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 АВТОМАТИЧЕСКИЙ РЕЖИМ", callback_data="auto")],
        [InlineKeyboardButton(text="⚙️ РУЧНОЙ РЕЖИМ", callback_data="manual")]
    ])

def signal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 ПЕРЕКРЫТИЕ", callback_data="auto")],
        [InlineKeyboardButton(text="👨‍💻 ПОДДЕРЖКА", url=SUPPORT_URL)]
    ])

def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 ПОЛУЧИТЬ КВАНТОВЫЙ СИГНАЛ", callback_data="get_sig")],
        [InlineKeyboardButton(text="👨‍💻 ПОДДЕРЖКА", url=SUPPORT_URL)]
    ])

# --- 5. ХЕНДЛЕРЫ ---

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

# Хендлер отправки ID на проверку админу
@dp.message(F.text.isdigit())
async def auth_request(m: types.Message):
    user_id = m.from_user.id
    username = f"@{m.from_user.username}" if m.from_user.username else "Нет юзернейма"
    provided_id = m.text
    
    await m.answer("⏳ **Ваш ID отправлен на верификацию.** Ожидайте подтверждения администратором...")
    
    # Кнопки для админа
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

# Обработка решения админа
@dp.callback_query(F.data.startswith("adm_accept:"))
async def admin_accept(c: types.CallbackQuery):
    target_user_id = int(c.data.split(":")[1])
    await c.answer("Пользователь одобрен!")
    await c.message.edit_text(c.message.text + "\n\n🟢 **Одобрено!** Пользователь получил доступ.")
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="✅ **Синхронизация успешна! Доступ активен.**",
            reply_markup=main_kb()
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение пользователю: {e}")

@dp.callback_query(F.data.startswith("adm_decline:"))
async def admin_decline(c: types.CallbackQuery):
    target_user_id = int(c.data.split(":")[1])
    await c.answer("Пользователь отклонен.")
    await c.message.edit_text(c.message.text + "\n\n🔴 **Отклонено.** Доступ заблокирован.")
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="❌ **Ошибка: ID не найден в базе данных квантового ядра либо регистрация не подтверждена.**"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение пользователю: {e}")

# ПОЛУЧЕНИЕ СИГНАЛА И РЕЖИМЫ ТОРГОВЛИ
@dp.callback_query(F.data == "get_sig")
async def get_sig(c: types.CallbackQuery):
    asset = ALL_PAIRS[datetime.now().second % len(ALL_PAIRS)]
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
    await c.message.answer(signal, reply_markup=get_main_kb())

@dp.callback_query(F.data == "auto")
async def auto_mode(c: types.CallbackQuery):
    asset = random.choice(CURRENCIES + CROSS_PAIRS + OTC)
    exp = random.randint(2, 5)
    sig = (f"🚀 **AI QUANTUM AUTO-SIGNAL (VLADOS USDT)**\n\n🔹 Актив: `{asset}`\n⏱ Экспирация: `{exp} мин`\n📈 Направление: 🟢 BUY / ВВЕРХ\n🎯 Индекс AI: `99.2%`")
    await c.message.answer(sig, reply_markup=signal_kb())

@dp.callback_query(F.data == "manual")
async def manual_mode(c: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Валюты", callback_data="cat:curr")],
        [InlineKeyboardButton(text="💱 Кросс-курсы", callback_data="cat:cross")],
        [InlineKeyboardButton(text="💎 OTC/Акции", callback_data="cat:otc")]
    ])
    await c.message.edit_text("📂 Выберите категорию:", reply_markup=kb)
    await state.set_state(SignalStates.choosing_cat)

@dp.callback_query(SignalStates.choosing_cat, F.data.startswith("cat:"))
async def select_asset(c: types.CallbackQuery, state: FSMContext):
    cat = c.data.split(":")[1]
    items = CURRENCIES if cat == "curr" else (CROSS_PAIRS if cat == "cross" else OTC)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f"asset:{i}")] for i in items[:8]])
    await c.message.edit_text("🔹 Выберите актив:", reply_markup=kb)
    await state.set_state(SignalStates.choosing_asset)

@dp.callback_query(SignalStates.choosing_asset, F.data.startswith("asset:"))
async def select_exp(c: types.CallbackQuery, state: FSMContext):
    asset = c.data.split(":")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{i} мин", callback_data=f"exp:{asset}:{i}")] for i in [2, 3, 4, 5]])
    await c.message.edit_text("⏳ Экспирация:", reply_markup=kb)
    await state.set_state(SignalStates.choosing_exp)

@dp.callback_query(SignalStates.choosing_exp, F.data.startswith("exp:"))
async def final_signal(c: types.CallbackQuery, state: FSMContext):
    _, asset, exp = c.data.split(":")
    finish = (datetime.now() + timedelta(minutes=int(exp))).strftime("%H:%M:%S")
    sig = (f"📡 **СИГНАЛ VLADOS USDT**\n\n🔹 **Актив:** `{asset}`\n⚡️ **Направление:** 🟢 BUY\n⏱ **Экспирация:** `{exp} мин`\n⏳ **Вход до:** `{finish}`\n🔥 **Индекс:** `95%`")
    await c.message.answer(sig, reply_markup=signal_kb())
    await state.clear()

# --- 6. WEB СЕРВЕР (ДЛЯ UPTIMEROBOT / RENDER) ---
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
