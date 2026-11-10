import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, BufferedInputFile
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = Path("gift_bot.sqlite3")

if not BOT_TOKEN:
    raise RuntimeError(
        "Не найден BOT_TOKEN. Создай переменную окружения BOT_TOKEN "
        "со значением токена от @BotFather."
    )

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


class TransferForm(StatesGroup):
    recipient = State()
    gift = State()


def db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                updated_at TEXT
            )
        """)


def remember_user(user):
    if not user:
        return
    with db() as conn:
        conn.execute("""
            INSERT INTO users(user_id, username, first_name, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                updated_at=excluded.updated_at
        """, (
            user.id,
            (user.username or "").lower(),
            user.first_name or "Пользователь",
            datetime.now().isoformat(timespec="seconds")
        ))


def find_user(username):
    username = username.lstrip("@").lower()
    with db() as conn:
        row = conn.execute(
            "SELECT user_id, first_name FROM users WHERE username=?",
            (username,)
        ).fetchone()
    return row


def load_font(size, bold=False):
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fit_text(draw, text, font, max_width):
    text = str(text)
    while text and draw.textbbox((0, 0), text, font=font)[2] > max_width:
        text = text[:-2] + "…" if len(text) > 2 else text[:-1]
    return text


def make_gift_card(sender, recipient, gift_name):
    """Creates a clearly labelled visual card; it does not transfer a Telegram gift."""
    width, height = 1080, 1180
    image = Image.new("RGB", (width, height), (35, 29, 31))
    px = image.load()

    # Warm dark gradient background
    top = (65, 43, 43)
    bottom = (25, 25, 31)
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(width):
            px[x, y] = color

    draw = ImageDraw.Draw(image)
    # Main card
    draw.rounded_rectangle((90, 65, 990, 1115), radius=58,
                           fill=(157, 119, 105), outline=(208, 170, 143), width=5)
    draw.rounded_rectangle((115, 90, 965, 1090), radius=44,
                           outline=(225, 195, 170), width=2)

    # Decorative stars
    for x, y, r in [(190, 220, 13), (870, 250, 17), (210, 850, 15),
                    (860, 900, 12), (540, 165, 9), (510, 960, 11)]:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(220, 187, 157))

    title_font = load_font(46, True)
    gift_font = load_font(56, True)
    label_font = load_font(31)
    value_font = load_font(35, True)
    small_font = load_font(23, True)

    draw.text((150, 135), "ВИЗУАЛЬНАЯ ПЕРЕДАЧА", font=title_font, fill=(255, 244, 230))
    draw.text((150, 220), "🎁", font=load_font(100, True), fill=(255, 222, 140))
    # A gift icon is also represented by a simple drawn present for fonts without emoji.
    draw.rounded_rectangle((410, 300, 670, 515), radius=28,
                           fill=(232, 139, 54), outline=(255, 220, 160), width=8)
    draw.rectangle((520, 300, 565, 515), fill=(111, 48, 119))
    draw.rectangle((410, 385, 670, 430), fill=(111, 48, 119))
    draw.arc((470, 245, 550, 350), 180, 360, fill=(111, 48, 119), width=22)
    draw.arc((530, 245, 610, 350), 180, 360, fill=(111, 48, 119), width=22)

    gift_text = fit_text(draw, gift_name, gift_font, 770)
    draw.text((150, 570), gift_text, font=gift_font, fill=(255, 246, 232))

    draw.text((150, 700), "ОТПРАВИТЕЛЬ", font=small_font, fill=(238, 211, 190))
    draw.text((150, 740), fit_text(draw, sender, value_font, 780),
              font=value_font, fill=(255, 255, 255))

    draw.text((150, 825), "НОВЫЙ ВЛАДЕЛЕЦ ВИЗУАЛЬНОЙ КАРТОЧКИ",
              font=small_font, fill=(238, 211, 190))
    draw.text((150, 865), fit_text(draw, recipient, value_font, 780),
              font=value_font, fill=(255, 255, 255))

    timestamp = datetime.now().strftime("%d.%m.%Y • %H:%M")
    draw.text((150, 970), timestamp, font=label_font, fill=(255, 236, 218))
    draw.rounded_rectangle((145, 1025, 935, 1070), radius=18,
                           fill=(112, 78, 69))
    disclaimer = "НЕ ПЕРЕМЕЩАЕТ И НЕ СОЗДАЁТ ПОДАРОК В TELEGRAM"
    draw.text((170, 1033), fit_text(draw, disclaimer, small_font, 740),
              font=small_font, fill=(255, 239, 225))

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    remember_user(message.from_user)
    await message.answer(
        "🎁 Привет! Это бот визуальных передач подарков.\n\n"
        "Команда /transfer создаёт красивую карточку и отправляет её "
        "в этот чат — так её увидят участники общего чата.\n\n"
        "Важно: карточка декоративная. Она не передаёт настоящий подарок "
        "Telegram и не меняет профиль получателя."
    )


@dp.message(Command("transfer"))
async def transfer_start(message: Message, state: FSMContext):
    remember_user(message.from_user)
    await state.set_state(TransferForm.recipient)
    await message.answer(
        "Кому передаём подарок визуально?\n"
        "Отправь @username или имя получателя."
    )


@dp.message(TransferForm.recipient)
async def get_recipient(message: Message, state: FSMContext):
    remember_user(message.from_user)
    recipient = (message.text or "").strip()
    if not recipient or len(recipient) > 64:
        await message.answer("Укажи имя или @username (до 64 символов).")
        return
    await state.update_data(recipient=recipient)
    await state.set_state(TransferForm.gift)
    await message.answer("Как называется подарок? Например: Snoop Dogg #421630")


@dp.message(TransferForm.gift)
async def get_gift(message: Message, state: FSMContext, bot: Bot):
    remember_user(message.from_user)
    gift_name = (message.text or "").strip()
    if not gift_name or len(gift_name) > 80:
        await message.answer("Название должно быть от 1 до 80 символов.")
        return

    data = await state.get_data()
    recipient = data["recipient"]
    sender = message.from_user.full_name or "Отправитель"
    image_bytes = make_gift_card(sender, recipient, gift_name)
    photo = BufferedInputFile(image_bytes, filename="visual_gift_transfer.png")

    caption = (
        f"🎁 Визуальная передача подарка\n"
        f"От: {sender}\n"
        f"Кому: {recipient}\n"
        f"Подарок: {gift_name}\n\n"
        f"Это только изображение-карточка. Настоящий подарок Telegram "
        f"не перемещён и в профиль не добавлен."
    )

    await message.answer_photo(photo, caption=caption)

    # If the recipient has previously opened the bot, send them a private copy too.
    # Otherwise the group/chat card remains visible to everyone in this conversation.
    if recipient.startswith("@"):
        known = find_user(recipient)
        if known and known[0] != message.from_user.id:
            try:
                await bot.send_photo(
                    known[0],
                    BufferedInputFile(image_bytes, filename="visual_gift_transfer.png"),
                    caption=caption
                )
            except Exception:
                logging.info("Could not send a private copy to recipient %s", recipient)

    await state.clear()
    await message.answer(
        "✅ Карточка создана!\n"
        "Чтобы получатель получил её в личку от бота, ему нужно сначала "
        "открыть бота и нажать Start. В общем чате карточку видят все."
    )


@dp.message()
async def remember_and_help(message: Message):
    remember_user(message.from_user)
    if message.text and message.text.startswith("/"):
        await message.answer("Используй /transfer, чтобы создать карточку передачи.")


async def main():
    init_db()
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
