import os
import logging
import asyncio
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("ОШИБКА: Задайте BOT_TOKEN и GEMINI_API_KEY в Render!")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Ты — экспертный ИИ-аналитик бота Master Trade 👑📊🚀.
Отвечай на любые вопросы по финансовым рынкам, трейдингу, тех-анализу и новостям.

Правила:
1. ОБЯЗАТЕЛЬНО используй много ярких эмодзи (📊, 🚀, 📈, 📉, ⚠️, 🧠, 💡, 🛡️, 💎, 🔥, 💰, 🎯) в КАЖДОМ ответе.
2. При вопросе "стоит ли торговать сейчас" — объясни фазу рынка (флэт/тренд), роль новостей и правила риск-менеджмента 🛡️.
3. Отвечай четко, понятно и по делу 🎯.
4. На нецелевые вопросы отвечай: "Я аналитический ассистент Master Trade 👑. Отвечаю только на темы рынка и трейдинга! 📊📈"
5. Запрещено упоминать администраторов, контакты или сторонние каналы 🚫.
6. В конце сложных разборов пиши: "⚠️ Аналитика носит информационный характер и не является рекомендацией."
"""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_news_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌐 Все новости", callback_query_data="news_all"),
            InlineKeyboardButton(text="💱 Форекс", callback_query_data="news_forex"),
        ],
        [
            InlineKeyboardButton(text="🪙 Криптовалюта", callback_query_data="news_crypto"),
            InlineKeyboardButton(text="📈 Акции", callback_query_data="news_stocks"),
        ],
        [
            InlineKeyboardButton(text="🛢️ Сырьевые товары", callback_query_data="news_commodities")
        ]
    ])

def generate_news_image_url(prompt_text: str) -> str:
    encoded_prompt = urllib.parse.quote(f"financial trading chart news {prompt_text} realistic 8k neon")
    seed = os.urandom(4).hex()
    return f"https://pollinations.ai/p/{encoded_prompt}?width=800&height=450&seed={seed}"

@dp.message(CommandStart())
async def start_cmd(message: Message):
    welcome_text = (
        "Привет! 👋 Добро пожаловать в **Master Trade** 👑📊🚀\n\n"
        "Выберите нужный раздел или просто напишите свой вопрос в чат! 👇"
    )
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📰 Раздел Новостей 🚀", callback_query_data="menu_news")],
        [InlineKeyboardButton(text="🧠 ИИ Помощник 📊", callback_query_data="menu_ai")]
    ])
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("menu_"))
async def handle_menu(callback: CallbackQuery):
    if callback.data == "menu_news":
        await callback.message.edit_text(
            "📰 **Раздел Новостей** 📊🔥\nВыберите категорию рыночных новостей ниже: 👇",
            reply_markup=get_news_keyboard(),
            parse_mode="Markdown"
        )
    elif callback.data == "menu_ai":
        await callback.message.edit_text(
            "🧠 **ИИ-помощник Master Trade** 👑📊\n\n"
            "Задайте любой вопрос по рынку, трейдингу, паттернам или сигналам прямо в этот чат! 👇🚀"
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("news_"))
async def handle_news_categories(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    
    cat_names = {
        "all": "Все рынки 🌐🔥",
        "forex": "Форекс 💱📈",
        "crypto": "Криптовалюта 🪙🚀",
        "stocks": "Акции 📈💎",
        "commodities": "Сырьевые товары 🛢️💰"
    }
    
    await callback.message.answer(f"⏳ Генерирую свежую сводку: **{cat_names.get(category)}**... 🚀")
    
    prompt = (
        f"Сформируй 2 актуальные главные новости для категории: {category}. "
        "Каждая новость должна содержать заголовки, разбор влияния на рынок и итоговый вердикт с огромным количеством эмодзи."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        
        img_url = generate_news_image_url(f"{category} market news")
        
        await callback.message.answer_photo(
            photo=img_url,
            caption=f"📰 **Новости: {cat_names.get(category)}** 🚀\n\n{response.text}",
            reply_markup=get_news_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка при получении новостей: {e}")
        
    await callback.answer()

@dp.message(F.text)
async def handle_ai_query(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=message.text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        if response.text:
            await message.answer(response.text)
    except Exception as e:
        logging.error(f"Ошибка Gemini API: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
