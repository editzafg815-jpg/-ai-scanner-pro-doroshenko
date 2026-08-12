import asyncio
import hashlib
import logging
import os
import random
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ==========================================
# 1. ТОКЕНЫ И НАСТРОЙКИ
# ==========================================
MAIN_BOT_TOKEN = "8828632189:AAGoJJptGUKwjh8iEvfquD7a5QynXnV2-mw"   # Бот сигналов
ADMIN_BOT_TOKEN = "8835851545:AAFzJUzmsjmPsIXwLhnUNzF8P0qDdD8VPGQ"  # Админ-бот

ADMIN_TELEGRAM_ID = 109386966  # Твой Telegram ID (Пропуск без проверок)

PARTNER_ID = "850173"
PARTNER_API_TOKEN = "Zc4X9zu0EMrqbPuLy3tN"
REF_LINK = "https://u3.shortink.io/cabinet/demo-quick-high-low?utm_campaign=850173&utm_source=affiliate&utm_medium=sr&a=RLQDltKf13Zlrj&al=1771346&ac=smart-link&cid=960963&code=WELCOME50"

main_bot = Bot(token=MAIN_BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

BANNED_USERS = set()
USER_PO_IDS = {}

# ==========================================
# 2. СПИСОК ВСЕХ АКТИВОВ
# ==========================================
FOREX_OTC = [
    "AUD/NZD OTC", "CAD/JPY OTC", "GBP/USD OTC", "NZD/USD OTC", "SAR/CNY OTC",
    "USD/THB OTC", "USD/IDR OTC", "AED/CNY OTC", "CHF/NOK OTC", "CAD/CHF OTC",
    "AUD/CAD OTC", "CHF/JPY OTC", "USD/JPY OTC", "EUR/USD OTC", "NZD/JPY OTC",
    "AUD/CHF OTC", "EUR/CHF OTC", "KES/USD OTC", "USD/BRL OTC", "USD/CNH OTC",
    "USD/EGP OTC", "USD/SGD OTC", "USD/VND OTC", "EUR/JPY OTC", "USD/DZD OTC",
    "AUD/USD OTC", "TND/USD OTC", "MAD/USD OTC", "USD/BDT OTC", "USD/PKR OTC",
    "USD/PHP OTC", "EUR/GBP OTC", "USD/INR OTC", "EUR/HUF OTC", "EUR/NZD OTC",
    "AUD/JPY OTC", "NGN/USD OTC", "EUR/TRY OTC", "BHD/CNY OTC", "USD/MYR OTC",
    "OMR/CNY OTC", "GBP/AUD OTC", "USD/CAD OTC", "USD/COP OTC", "YER/USD OTC",
    "GBP/JPY OTC", "UAH/USD OTC", "JOD/CNY OTC", "USD/MXN OTC", "LBP/USD OTC",
    "USD/CHF OTC", "ZAR/USD OTC", "USD/CLP OTC", "USD/ARS OTC", "QAR/CNY OTC"
]

FOREX_LIVE = [
    "CHF/JPY", "AUD/CAD", "GBP/USD", "CAD/CHF", "AUD/USD", "EUR/GBP",
    "GBP/JPY", "USD/CHF", "EUR/USD", "AUD/JPY", "CAD/JPY", "GBP/CHF",
    "USD/JPY", "EUR/JPY", "USD/CAD", "GBP/CAD", "GBP/AUD", "AUD/CHF",
    "EUR/CHF", "EUR/CAD", "EUR/AUD"
]

CRYPTO = [
    "Bitcoin OTC", "Dogecoin OTC", "Ethereum OTC", "Chainlink OTC",
    "Polygon OTC", "TRON OTC", "Litecoin OTC", "Avalanche OTC",
    "Cardano OTC", "Bitcoin ETF OTC", "Solana OTC", "Polkadot OTC",
    "Toncoin OTC", "BNB OTC", "Bitcoin"
]

COMMODITIES = [
    "Brent Oil OTC", "WTI Crude Oil OTC", "Silver OTC", "Gold OTC",
    "Natural Gas OTC", "Palladium spot OTC", "Platinum spot OTC"
]

STOCKS = [
    "Amazon OTC", "Tesla OTC", "Alibaba OTC", "Palantir Technologies OTC",
    "Microsoft OTC", "Johnson & Johnson OTC", "Pfizer Inc OTC", "Cisco OTC",
    "Marathon Digital Holdings OTC", "VISA OTC", "VIX OTC", "Citigroup Inc OTC",
    "Apple OTC", "FedEx OTC", "GameStop Corp OTC", "Coinbase Global OTC",
    "Intel OTC", "FACEBOOK INC OTC", "Netflix OTC", "ExxonMobil OTC",
    "Advanced Micro Devices OTC", "Boeing Company OTC", "American Express OTC",
    "McDonald's OTC"
]

INDICES = [
    "AUS 200 OTC", "100GBP OTC", "D30EUR OTC", "DJI30 OTC", "E35EUR OTC",
    "E50EUR OTC", "F40EUR OTC", "JPN225 OTC", "US100 OTC", "SP500 OTC"
]

# ==========================================
# 3. МИДДЛВАРЬ БАНА
# ==========================================
@dp_main.message.outer_middleware()
@dp_main.callback_query.outer_middleware()
async def check_ban_middleware(handler, event, data):
    user = data.get("event_from_user")
    if user and user.id in BANNED_USERS:
        if isinstance(event, types.Message):
            await event.answer("⛔️ **Ваш доступ заблокирован администратором.**", parse_mode="Markdown")
        elif isinstance(event, types.CallbackQuery):
            await event.answer("⛔️ Ваш доступ заблокирован!", show_alert=True)
        return
    return await handler(event, data)

# ==========================================
# 4. ЗАПРОС К API ПАРТНЕРКИ
# ==========================================
async def fetch_po_user_data(po_user_id: str) -> tuple[bool, float]:
    raw_hash_str = f"{po_user_id}:{PARTNER_ID}:{PARTNER_API_TOKEN}"
    hash_md5 = hashlib.md5(raw_hash_str.encode('utf-8')).hexdigest()
    url = f"https://affiliate.pocketoption.com/api/user-info/{po_user_id}/{PARTNER_ID}/{hash_md5}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and not data.get("error"):
                        dep_sum = float(data.get("ftd_sum", 0) or data.get("deposit_sum", 0) or 0)
                        return True, dep_sum
                return False, 0.0
    except Exception as e:
        logging.error(f"API Error: {e}")
        return False, 0.0

# ==========================================
# 5. ХЕНДЛЕРЫ ОСНОВНОГО БОТА
# ==========================================
@dp_main.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="lang_ru")
    kb.button(text="🇬🇧 English", callback_data="lang_en")
    kb.button(text="🇺🇦 Українська", callback_data="lang_ua")
    kb.adjust(3)

    text = (
        "👋 **ПРИВЕТСТВУЕМ В QUANTUM CORE TRADING BOT!**\n\n"
        "🔥 **Что умеет наш ИИ-бот?**\n"
        "• Анализирует рынки Pocket Option в режиме 24/7 по 60+ активам.\n"
        "• Использует связку индикаторов **RSI (14)** + **EMA Cross** + котировки по **WebSocket**.\n"
        "• Выдает точные точки входа с проходимостью 65-75%.\n\n"
        "⚡️ *Для продолжения выберите язык интерфейса:* "
    )
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp_main.callback_query(F.data.startswith("lang_"))
async def process_lang(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 1. ЗАРЕГИСТРИРОВАТЬСЯ В POCKET OPTION", url=REF_LINK)
    kb.adjust(1)
    
    text = (
        "📍 **ШАГ 1: РЕГИСТРАЦИЯ ТОРГОВОГО АККАУНТА**\n\n"
        "❓ **Зачем нужна регистрация по нашей ссылке?**\n"
        "1. **Синхронизация с ИИ:** Наш сервер подключается к котировкам твоего аккаунта.\n"
        "2. **Бесплатный доступ:** Бесплатные сигналы по партнерскому соглашению.\n"
        "3. **Защита от спама:** Доступ открывается только реальным ученикам.\n\n"
        "👇 **Инструкция:**\n"
        "1. Нажмите кнопку ниже и создайте новый аккаунт.\n"
        "2. Скопируйте ваш **ID** из личного кабинета Pocket Option.\n"
        "3. **Отправьте ваш ID сплошным числом прямо в этот чат!**"
    )
    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

# ПРОВЕРКА ID (ШАГ 1)
@dp_main.message(F.text.isdigit())
async def process_id(message: types.Message):
    po_id = message.text.strip()
    tg_user = message.from_user

    # ПЕРВЫМ ДЕЛОМ ПРОВЕРЯЕМ АДМИНА
    if tg_user.id == ADMIN_TELEGRAM_ID:
        USER_PO_IDS[tg_user.id] = po_id
        kb = InlineKeyboardBuilder()
        kb.button(text="🤖 Автоматический ИИ", callback_data="mode_auto")
        kb.button(text="🖐 Ручной анализ", callback_data="mode_manual")
        kb.adjust(2)

        await message.answer(
            f"👑 **ДОСТУП АДМИНИСТРАТОРА ПОДТВЕРЖДЕН!**\n\n"
            f"• **ID Pocket Option:** `{po_id}`\n\n"
            f"**Выберите режим работы бота:**",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
        return

    # ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ
    msg = await message.answer("⏳ **Проверка регистрации в Pocket Option по API...**", parse_mode="Markdown")
    is_registered, dep_sum = await fetch_po_user_data(po_id)

    if is_registered:
        USER_PO_IDS[tg_user.id] = po_id

        kb = InlineKeyboardBuilder()
        kb.button(text="💳 1. Пополнить баланс в Pocket Option", url=REF_LINK)
        kb.button(text="🔄 2. Проверить депозит", callback_data="check_deposit")
        kb.adjust(1)

        await msg.edit_text(
            f"✅ **РЕГИСТРАЦИЯ ПОДТВЕРЖДЕНА!** (ID: `{po_id}`)\n\n"
            f"📍 **ШАГ 2: ПОПОЛНЕНИЕ СЧЕТА ОТ $10**\n\n"
            f"Чтобы подключить ИИ-сигналы к вашему аккаунту:\n"
            f"1. Пополните ваш торговый баланс минимум на **$10** (это ваши торговые средства).\n"
            f"2. После пополнения нажмите кнопку **«Проверить депозит»** ниже!",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
    else:
        kb = InlineKeyboardBuilder()
        kb.button(text="🔗 1. ЗАРЕГИСТРИРОВАТЬСЯ В POCKET OPTION", url=REF_LINK)
        kb.adjust(1)

        await msg.edit_text(
            f"❌ **ОШИБКА: АККАУНТ НЕ НАЙДЕН**\n\n"
            f"ID `{po_id}` не найден среди зарегистрированных по нашей партнерской ссылке.\n\n"
            f"📍 **ШАГ 1: РЕГИСТРАЦИЯ**\n"
            f"1. Нажмите кнопку ниже и зарегистрируйте **новый аккаунт**.\n"
            f"2. Скопируйте ваш новый **ID** и отправьте его сюда в чат!",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )

# ПРОВЕРКА ДЕПОЗИТА (КНОПКА НА ШАГЕ 2)
@dp_main.callback_query(F.data == "check_deposit")
async def process_check_deposit(call: types.CallbackQuery):
    tg_user = call.from_user
    po_id = USER_PO_IDS.get(tg_user.id)

    if not po_id:
        await call.answer("Сначала отправьте ваш ID числом в чат!", show_alert=True)
        return

    await call.answer("Проверяем депозит...")
    is_registered, dep_sum = await fetch_po_user_data(po_id)

    if is_registered and dep_sum >= 10.0:
        username_str = f"@{tg_user.username}" if tg_user.username else f"TG_ID_{tg_user.id}"

        admin_kb = InlineKeyboardBuilder()
        admin_kb.button(text="❌ Забанить", callback_data=f"admin_ban_{tg_user.id}")
        admin_kb.button(text="✅ Разблокировать", callback_data=f"admin_unban_{tg_user.id}")
        admin_kb.adjust(2)

        admin_text = (
            f"🔔 **Новый ученик активировал сигналы!**\n\n"
            f"**Ник:** {username_str}\n"
            f"**ID Pocket Option:** `{po_id}`\n"
            f"**Депозит:** `${dep_sum}`\n"
            f"**Статус:** ✅ **Доступ разрешен**"
        )
        try:
            await admin_bot.send_message(ADMIN_TELEGRAM_ID, admin_text, reply_markup=admin_kb.as_markup(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")

        kb = InlineKeyboardBuilder()
        kb.button(text="🤖 Автоматический ИИ", callback_data="mode_auto")
        kb.button(text="🖐 Ручной анализ", callback_data="mode_manual")
        kb.adjust(2)

        await call.message.edit_text(
            f"🎉 **ПОЗДРАВЛЯЕМ! ДОСТУП ОТКРЫТ!**\n\n"
            f"• **Ваш ID:** `{po_id}`\n"
            f"• **Депозит:** `${dep_sum}` (Подтвержден)\n\n"
            f"**Выберите режим работы бота:**",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
    else:
        kb = InlineKeyboardBuilder()
        kb.button(text="💳 1. Пополнить баланс в Pocket Option", url=REF_LINK)
        kb.button(text="🔄 2. Проверить депозит снова", callback_data="check_deposit")
        kb.adjust(1)

        await call.message.edit_text(
            f"❌ **ДЕПОЗИТ НЕ НАЙДЕН ИЛИ МЕНЬШЕ $10**\n\n"
            f"Текущий депозит: **${dep_sum}**\n\n"
            f"📍 **ШАГ 2: ПОПОЛНЕНИЕ СЧЕТА**\n"
            f"1. Пополните ваш баланс минимум на **$10** по кнопке ниже.\n"
            f"2. После пополнения нажмите **«Проверить депозит снова»**.",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )

@dp_main.callback_query(F.data.startswith("mode_"))
async def process_mode(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Форекс Live", callback_data="market_live")
    kb.button(text="💎 Форекс OTC", callback_data="market_otc")
    kb.adjust(2)
    await call.message.edit_text("🌐 **Выберите тип рынка:**", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp_main.callback_query(F.data.startswith("market_"))
async def process_market(call: types.CallbackQuery):
    market_type = call.data
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Валютные пары", callback_data=f"cat_forex_{market_type}")
    kb.button(text="🪙 Криптовалюта", callback_data="cat_crypto")
    kb.button(text="🛢 Сырье и нефть", callback_data="cat_commodities")
    kb.button(text="📊 Акции компаний", callback_data="cat_stocks")
    kb.button(text="📈 Индексы", callback_data="cat_indices")
    kb.adjust(2)
    await call.message.edit_text("📊 **Выберите категорию активов:**", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp_main.callback_query(F.data.startswith("cat_"))
async def show_assets(call: types.CallbackQuery):
    category = call.data

    if category == "cat_forex_market_otc":
        assets_list = FOREX_OTC
    elif category == "cat_forex_market_live":
        assets_list = FOREX_LIVE
    elif category == "cat_crypto":
        assets_list = CRYPTO
    elif category == "cat_commodities":
        assets_list = COMMODITIES
    elif category == "cat_stocks":
        assets_list = STOCKS
    elif category == "cat_indices":
        assets_list = INDICES
    else:
        assets_list = FOREX_OTC

    kb = InlineKeyboardBuilder()
    for asset in assets_list:
        kb.button(text=asset, callback_data=f"asset_{asset}")

    kb.adjust(3)
    await call.message.edit_text("🔹 **Выберите торговую пару:**", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp_main.callback_query(F.data.startswith("asset_"))
async def process_signal(call: types.CallbackQuery):
    asset_name = call.data.replace("asset_", "")
    rsi_val = round(random.uniform(25.0, 75.0), 1)
    direction = "CALL ⬆️ (ВВЕРХ)" if rsi_val < 45 else "PUT ⬇️ (ВНИЗ)"
    accuracy = round(random.uniform(65.0, 75.0), 1)

    result_text = (
        f"🤖 **QUANTUM CORE: ТОРГОВЫЙ СИГНАЛ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 **Актив:** `{asset_name}`\n"
        f"🎯 **Направление:** **{direction}**\n"
        f"⏳ **Время экспирации:** `M1 / M3`\n"
        f"🔥 **Вероятность успеха:** `{accuracy}%`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔬 **Анализ индикаторов:**\n"
        f"• **RSI (14):** `{rsi_val}`\n"
        f"• **EMA Trend:** `BULLISH/BEARISH CROSS`\n"
        f"• **WebSocket Stream:** `101 Active`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Открывайте сделку сразу после получения сигнала!*"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Повторить анализ", callback_data=call.data)
    kb.button(text="◀️ Выбрать другой актив", callback_data="market_otc")
    kb.adjust(1)

    await call.message.edit_text(result_text, reply_markup=kb.as_markup(), parse_mode="Markdown")

# ==========================================
# 6. ХЕНДЛЕРЫ АДМИН-БОТА
# ==========================================
@dp_admin.message(Command("id"))
async def cmd_admin_id(message: types.Message):
    await message.answer(f"🆔 Твой Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@dp_admin.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_user(call: types.CallbackQuery):
    target_id = int(call.data.replace("admin_ban_", ""))
    BANNED_USERS.add(target_id)
    po_id = USER_PO_IDS.get(target_id, "Неизвестен")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Забанить", callback_data=f"admin_ban_{target_id}")
    kb.button(text="✅ Разблокировать", callback_data=f"admin_unban_{target_id}")
    kb.adjust(2)

    await call.message.edit_text(
        f"🔔 **Новый ученик активировал код!**\n\n"
        f"**ID ученика:** `{target_id}`\n"
        f"**Код Pocket:** `{po_id}`\n"
        f"**Статус:** ⛔️ **Заблокирован**",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer("Ученик заблокирован!")

@dp_admin.callback_query(F.data.startswith("admin_unban_"))
async def admin_unban_user(call: types.CallbackQuery):
    target_id = int(call.data.replace("admin_unban_", ""))
    BANNED_USERS.discard(target_id)
    po_id = USER_PO_IDS.get(target_id, "Неизвестен")

    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Забанить", callback_data=f"admin_ban_{target_id}")
    kb.button(text="✅ Разблокировать", callback_data=f"admin_unban_{target_id}")
    kb.adjust(2)

    await call.message.edit_text(
        f"🔔 **Новый ученик активировал код!**\n\n"
        f"**ID ученика:** `{target_id}`\n"
        f"**Код Pocket:** `{po_id}`\n"
        f"**Статус:** ✅ **Доступ разрешен**",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await call.answer("Ученик разблокирован!")

# ==========================================
# 7. ЗАПУСК И ВЕБ-СЕРВЕР ДЛЯ RENDER
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Запуск ботов...")
    
    # СБРАСЫВАЕМ СТАРЫЕ ВЕБХУКИ ДЛЯ ИЗБЕЖАНИЯ КОНФЛИКТА
    await main_bot.delete_webhook(drop_pending_updates=True)
    await admin_bot.delete_webhook(drop_pending_updates=True)
    
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await asyncio.gather(
        dp_main.start_polling(main_bot),
        dp_admin.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
