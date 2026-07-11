import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiohttp import web

# Берем токен из переменных окружения (в настройках Render добавь BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Кнопка разработчика (константа)
DEV_BUTTON = [InlineKeyboardButton(text="👨‍💻 Разработчик", url="https://t.me/andriddddd")]

# --- ФУНКЦИЯ ОТПРАВКИ СИГНАЛА ---
async def send_signal(chat_id, pair, direction, timeframe, expiration):
    text = (
        f"🔔 **Новый сигнал!**\n"
        f"📊 Пара: {pair}\n"
        f"📈 Направление: {direction}\n"
        f"⏱ Таймфрейм: {timeframe}\n"
        f"⏳ Время сделки: {expiration} мин.\n"
        f"🚀 Заходим!"
    )
    
    # Кнопки при отправке: Плюс/Минус и Разработчик
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Плюс", callback_data="res_plus"),
         InlineKeyboardButton(text="❌ Минус", callback_data="res_minus")],
        DEV_BUTTON
    ])
    
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    
    # Ждем 60 секунд для автоматического обновления статуса
    await asyncio.sleep(60)
    
    # Обновляем текст сообщения, добавляя место для итога
    try:
        updated_text = text + "\n\n🏁 **ИТОГ: Ожидаем...**"
        await msg.edit_text(text=updated_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[DEV_BUTTON]))
    except:
        pass # Если пользователь уже нажал кнопку, редактирование пропустим

# --- ОБРАБОТЧИК КНОПОК ИТОГА ---
@dp.callback_query(F.data.startswith("res_"))
async def process_result(callback: CallbackQuery):
    result = "✅ ПЛЮС" if callback.data == "res_plus" else "❌ МИНУС"
    
    # Заменяем "Ожидаем..." на реальный результат
    # Если минута еще не прошла, просто добавляем итог
    if "ИТОГ" not in callback.message.text:
        new_text = callback.message.text + f"\n\n🏁 **ИТОГ: {result}**"
    else:
        new_text = callback.message.text.replace("Ожидаем...", result)
    
    await callback.message.edit_text(text=new_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[DEV_BUTTON]))
    await callback.answer(f"Результат: {result}")

# --- КОМАНДА ДЛЯ ТЕСТА ---
@dp.message(Command("signal"))
async def cmd_signal(message: Message):
    # Пример вызова: /signal EURUSD ВВЕРХ 1 3
    args = message.text.split()
    if len(args) == 5:
        await send_signal(message.chat.id, args[1], args[2], args[3], args[4])

# --- ЗАГЛУШКА ДЛЯ ПОРТА (ДЛЯ RENDER) ---
async def health_check(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

async def main():
    print("Бот запущен...")
    # Запускаем заглушку порта перед ботом
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
