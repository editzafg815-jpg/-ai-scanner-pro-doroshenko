import asyncio
import random
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from os import getenv

# Инициализация
TOKEN = getenv("BOT_TOKEN")
CHANNEL_ID = -1004377135973
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список твоих пар
PAIRS = ["AUD/USD OTC", "CAD/CHF OTC", "EUR/GBP OTC", "EUR/USD OTC", 
         "USD/JPY OTC", "Bitcoin OTC", "Tesla OTC", "Apple OTC", "Amazon OTC"]

def get_keyboard():
    # Кнопки CALL/PUT убраны, осталась только Поддержка
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Поддержка/Разработчик", url="https://t.me/andriddddd")]
    ])

async def send_signal():
    asset = random.choice(PAIRS)
    confidence = random.randint(88, 97)
    
    # Логика "псевдо-анализа" (привязка к активу, чтобы не было чистого рандома)
    if "USD" in asset or "Bitcoin" in asset:
        direction_text = "ВВЕРХ (CALL) 🟢"
    else:
        direction_text = "ВНИЗ (PUT) 🔴"
        
    # Формируем сообщение
    text = (
        f"👑 **СИГНАЛ МАСТЕРА** 👑\n\n"
        f"💵 Актив: {asset}\n"
        f"🕯 Интервал: 1 минута\n"
        f"🎯 Прогноз: {direction_text}\n"
        f"📈 Уверенность: {confidence}%\n\n"
        f"💡 Совет: Соблюдайте ММ. Не ставьте весь банк."
    )
    
    msg = await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=get_keyboard(), parse_mode="Markdown")
    
    # Экспирация 1 минута
    await asyncio.sleep(60)
    
    # Результат с "проходимостью" 65%
    result = "WIN ✅" if random.randint(1, 100) <= 65 else "LOSS ❌"
    
    await bot.edit_message_text(
        chat_id=CHANNEL_ID,
        message_id=msg.message_id,
        text=f"{text}\n\nРезультат: {result}",
        parse_mode="Markdown"
    )

async def main():
    while True:
        await send_signal()
        # Ждем 2 минуты до начала нового цикла (всего 3 минуты)
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
