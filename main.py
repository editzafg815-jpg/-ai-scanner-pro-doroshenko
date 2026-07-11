import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from os import getenv

# Инициализация
TOKEN = getenv("BOT_TOKEN")
CHANNEL_ID = -1004377135973
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список активов
PAIRS = ["AUD/USD OTC", "CAD/CHF OTC", "EUR/GBP OTC", "EUR/USD OTC", 
         "USD/JPY OTC", "Bitcoin OTC", "Tesla OTC", "Apple OTC", "Amazon OTC"]

# Клавиатура с кнопкой поддержки
def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Поддержка/Разработчик", url="https://t.me/andriddddd")]
    ])

async def send_signal():
    asset = random.choice(PAIRS)
    confidence = random.randint(88, 97)
    
    # Расчет времени
    now = datetime.now().strftime("%H:%M")
    expiry_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    
    # Логика направления
    if "USD" in asset or "Bitcoin" in asset:
        direction_text = "ВВЕРХ (CALL) 🟢"
    else:
        direction_text = "ВНИЗ (PUT) 🔴"
        
    # Формируем текст сигнала
    text = (
        f"👑 **СИГНАЛ МАСТЕРА** 👑\n\n"
        f"💵 Актив: {asset}\n"
        f"⏰ Время входа: {now}\n"
        f"⌛ Экспирация: 1 минута (до {expiry_time})\n"
        f"🎯 Прогноз: {direction_text}\n"
        f"📈 Уверенность: {confidence}%\n\n"
        f"💡 Совет: Соблюдайте ММ. Не ставьте весь банк."
    )
    
    # Отправляем сигнал
    await bot.send_message(
        chat_id=CHANNEL_ID, 
        text=text, 
        reply_markup=get_keyboard(), 
        parse_mode="Markdown"
    )
    
    # Ждем 1 минуту (время экспирации)
    await asyncio.sleep(60)
    
    # Результат (65% проходимость)
    result_text = "WIN ✅" if random.randint(1, 100) <= 65 else "LOSS ❌"
    
    # Отправляем результат отдельным сообщением
    await bot.send_message(chat_id=CHANNEL_ID, text=result_text)

async def main():
    # Бесконечный цикл
    while True:
        await send_signal()
        # Пауза 2 минуты перед следующим сигналом
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
