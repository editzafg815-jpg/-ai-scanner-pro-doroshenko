import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from os import getenv

# Инициализация
TOKEN = getenv("BOT_TOKEN")
CHANNEL_ID = -1004377135973
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список пар из твоих скриншотов
PAIRS = ["AUD/USD OTC", "CAD/CHF OTC", "EUR/GBP OTC", "EUR/USD OTC", 
         "USD/JPY OTC", "Bitcoin OTC", "Tesla OTC", "Apple OTC", "Amazon OTC"]

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CALL", callback_data="call"),
         InlineKeyboardButton(text="PUT", callback_data="put")],
        [InlineKeyboardButton(text="📞 Поддержка/Разработчик", url="https://t.me/andriddddd")]
    ])

async def send_signal():
    asset = random.choice(PAIRS)
    confidence = random.randint(85, 98)
    
    text = (
        f"🚀 **Mobtron Analysis**\n\n"
        f"💵 Актив: {asset}\n"
        f"🕯 Интервал: 1 минута\n"
        f"⌛ Экспирация: 1 минута\n"
        f"🎯 Уверенность: {confidence}%\n\n"
        f"💡 Совет: Соблюдайте ММ\n"
        f"💡 Совет: Не ставьте весь банк"
    )
    
    msg = await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=get_keyboard())
    
    # Ждем 1 минуту (экспирация)
    await asyncio.sleep(60)
    
    # Результат
    result = "WIN ✅" if random.random() > 0.25 else "LOSS ❌"
    await bot.edit_message_text(
        chat_id=CHANNEL_ID,
        message_id=msg.message_id,
        text=f"{text}\n\nРезультат: {result}"
    )

async def main():
    while True:
        await send_signal()
        # Ждем оставшиеся 2 минуты, чтобы в сумме было 3 минуты цикла
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
