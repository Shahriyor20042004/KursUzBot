import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = "8300124535:AAG_WJ_ecd4dW4A1Yip2sp1j6tRMtO2O82w"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# 📊 Получаем курсы валют
def get_exchange_rates():
    url = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
    response = requests.get(url)
    data = response.json()
    rates = {item["Ccy"]: float(item["Rate"]) for item in data}
    return rates


def format_rates(rates):
    result = "💱 <b>Курсы валют (ЦБ РУз)</b>\n\n"
    for ccy in ["USD", "EUR", "RUB"]:
        if ccy in rates:
            result += f"🔹 {ccy}: {rates[ccy]:,.2f} сум\n"
    return result


# 🌐 Состояния FSM
class ConvertState(StatesGroup):
    waiting_for_amount = State()
    from_ccy = State()
    to_ccy = State()


# 🏁 /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Конвертировать валюту", callback_data="convert_menu")],
        [InlineKeyboardButton(text="📊 Курсы валют", callback_data="show_rates")],
        [InlineKeyboardButton(text="⚖️ Сравнение валют", callback_data="compare_rates")]
    ])
    await message.answer(
        "👋 Привет! Я бот для показа и конвертации валют.\n\n"
        "Выбери действие ниже 👇",
        reply_markup=keyboard
    )


# 📊 /rates — просмотр курсов валют
@dp.message(Command("rates"))
async def rates_handler(message: types.Message):
    rates = get_exchange_rates()
    await message.answer(format_rates(rates))


# 🔄 /convert — переход к меню конвертации
@dp.message(Command("convert"))
async def convert_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 USD ↔ 🇺🇿 UZS", callback_data="USD_UZS"),
            InlineKeyboardButton(text="🇪🇺 EUR ↔ 🇺🇿 UZS", callback_data="EUR_UZS")
        ],
        [InlineKeyboardButton(text="🇷🇺 RUB ↔ 🇺🇿 UZS", callback_data="RUB_UZS")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    await message.answer("Выбери направление конвертации 👇", reply_markup=keyboard)


# 📊 Показ курсов валют (через кнопку)
@dp.callback_query(lambda c: c.data == "show_rates")
async def show_rates(callback: types.CallbackQuery):
    await callback.answer()
    rates = get_exchange_rates()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    await callback.message.edit_text(format_rates(rates), reply_markup=keyboard)


# 💱 Главное меню конвертации (через кнопку)
@dp.callback_query(lambda c: c.data == "convert_menu")
async def show_convert_menu(callback: types.CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 USD ↔ 🇺🇿 UZS", callback_data="USD_UZS"),
            InlineKeyboardButton(text="🇪🇺 EUR ↔ 🇺🇿 UZS", callback_data="EUR_UZS")
        ],
        [InlineKeyboardButton(text="🇷🇺 RUB ↔ 🇺🇿 UZS", callback_data="RUB_UZS")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    await callback.message.edit_text("Выбери направление конвертации 👇", reply_markup=keyboard)


# 🔙 Назад в главное меню (исправлено)
@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Конвертировать валюту", callback_data="convert_menu")],
        [InlineKeyboardButton(text="📊 Курсы валют", callback_data="show_rates")],
        [InlineKeyboardButton(text="⚖️ Сравнение валют", callback_data="compare_rates")]
    ])
    await callback.message.edit_text(
        "👋 Привет! Я бот для показа и конвертации валют.\n\n"
        "Выбери действие ниже 👇",
        reply_markup=keyboard
    )


# ⚖️ Сравнение валют
@dp.callback_query(lambda c: c.data == "compare_rates")
async def compare_rates(callback: types.CallbackQuery):
    await callback.answer()

    rates = get_exchange_rates()
    usd = rates["USD"]
    eur = rates["EUR"]
    rub = rates["RUB"]

    text = (
        "🌍 <b>Сравнение валют:</b>\n\n"
        f"1 USD = {usd/eur:.3f} EUR = {usd/rub:.3f} RUB\n"
        f"1 EUR = {eur/usd:.3f} USD = {eur/rub:.3f} RUB\n"
        f"1 RUB = {rub/usd:.3f} USD = {rub/eur:.3f} EUR\n\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


# 💰 Выбор валюты
@dp.callback_query(lambda c: c.data.endswith("_UZS"))
async def choose_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    from_ccy = callback.data.split("_")[0]
    to_ccy = "UZS"
    await state.update_data(from_ccy=from_ccy, to_ccy=to_ccy)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 Поменять направление ({to_ccy} → {from_ccy})",
                              callback_data=f"{to_ccy}_{from_ccy}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    await callback.message.edit_text(
        f"Введите сумму в {from_ccy}:",
        reply_markup=keyboard
    )
    await state.set_state(ConvertState.waiting_for_amount)


# 🔄 Изменение направления конвертации
@dp.callback_query(lambda c: "_" in c.data)
async def switch_direction(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    from_ccy, to_ccy = callback.data.split("_")
    await state.update_data(from_ccy=from_ccy, to_ccy=to_ccy)
    await callback.message.edit_text(f"Введите сумму в {from_ccy}:")
    await state.set_state(ConvertState.waiting_for_amount)


# 💵 Получение суммы и конвертация
@dp.message(ConvertState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    from_ccy = data.get("from_ccy")
    to_ccy = data.get("to_ccy")

    try:
        amount = float(message.text.replace(",", "."))
        rates = get_exchange_rates()

        if from_ccy == "UZS":
            result = amount / rates[to_ccy]
        elif to_ccy == "UZS":
            result = amount * rates[from_ccy]
        else:
            result = amount * rates[from_ccy] / rates[to_ccy]

        await message.answer(
            f"💰 {amount:,.2f} {from_ccy} = <b>{result:,.2f} {to_ccy}</b>\n\n"
            f"🔁 Чтобы конвертировать снова — используй /convert"
        )

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")

    await state.clear()


# 🧭 Добавляем команды в меню
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🟢 Запустить бота"),
        BotCommand(command="rates", description="💱 Курсы валют"),
        BotCommand(command="convert", description="🔄 Конвертировать валюту")
    ]
    await bot.set_my_commands(commands)


# 🚀 Запуск
async def main():
    print("✅ Бот запущен")
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
