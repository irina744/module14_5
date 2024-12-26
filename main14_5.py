from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from config import api
from keyboards import *
import crud_functions
from crud_functions import initiate_db, get_all_products, add_product, is_included, add_user

bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

initiate_db()

add_product('Product 1', 'Описание продукта 1', 100)
add_product('Product 2', 'Описание продукта 2', 200)
add_product('Product 3', 'Описание продукта 3', 300)
add_product('Product 4', 'Описание продукта 4', 400)


@dp.message_handler(text='Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()
    for product in products:
        product_id, title, description, price = product
        await message.answer(f"{product_id}. Название: {title} | Описание: {description} | Цена: {price}")
        image_path = f'files/product{product_id}.jpeg'
        with open(image_path, 'rb') as imj:
            await message.answer_photo(imj,
                                       f'Product{product_id}: {title} | Description: {description} | Price: {price}')
    await message.answer('Выберите продукт для покупки:', reply_markup=kb2)


@dp.callback_query_handler(text='product_buying')
async def send_confirm_message(call):
    await call.message.answer('Вы успешно приобрели продукт!')


@dp.message_handler(text='Рассчитать')
async def main_menu(message):
    await message.answer('Выберите опцию:', reply_markup=kb1)


@dp.callback_query_handler(text='formulas')
async def get_formulas(call):
    await call.message.answer('10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5')
    await call.answer()


@dp.message_handler(commands=['start'])
async def send_welcome(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью.', reply_markup=kb)


@dp.message_handler(text='Информация')
async def all_messages(message):
    await message.answer('ВВедите команду /start, чтобы начать общение')


class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = 1000


@dp.message_handler(text='Регистрация')
async def registration(message: types.Message):
    await message.answer('Введите имя пользователя')
    await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state):
    if not is_included(message.text):
        await state.update_data(username=message.text)
        await message.answer('Введите email')
        await RegistrationState.email.set()
    else:
        await message.answer('Пользователь существует, введите другое имя')
        await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state):
    await state.update_data(email=message.text)
    await message.answer('Введите свой вщзраст')
    await RegistrationState.age.set()


@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state):
    await state.update_data(age=message.text)
    await state.update_data(balance=1000)
    data = await state.get_data()
    add_user(data['username'], data['email'], data['age'], data['balance'])
    await message.answer('Регистрация прошла успешно')
    await state.finish()


@dp.callback_query_handler(text='calories')
async def set_age(call):
    await call.message.answer('введите свой возраст')
    await UserState.age.set()


@dp.message_handler(state=UserState.age)
async def set_growth(message, state):
    await state.update_data(age=message.text)
    await message.answer('введите свой рост')
    await UserState.growth.set()


@dp.message_handler(state=UserState.growth)
async def send_calories(message, state):
    await state.update_data(growth=message.text)
    await message.answer('введите свой вес')
    await UserState.weight.set()


@dp.message_handler(state=UserState.weight)
async def send_calories(message, state):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    age = float(data['age'])
    growth = float(data['growth'])
    weight = float(data['weight'])
    cal = 10 * weight + 6.25 * growth - 5 * age + 5
    await message.answer(f'Ваша норма калорий {cal}')
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
