from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db

TOKEN = '6436284246:AAEb8aEUhFvIegTMMa77mJ2gxYCQJDiuujc'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


async def on_startup(_):
    await db.db_connect()


class Profile(StatesGroup):
    age = State()
    gender = State()
    pets_flag = State()
    kids_flag = State()


# Список предметов
subjects = ['Математика', 'Физика', 'Химия', 'Биология', 'Информатика']


async def create_subjects_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    selected_subjects = await db.get_categories(user_id)
    print(selected_subjects)
    print(f'selected: {selected_subjects}')
    for subject in subjects:
        # Если предмет уже выбран, делаем кнопку неактивной
        if subject in selected_subjects:
            keyboard.add(InlineKeyboardButton(f'✅ {subject}', callback_data=f'subject:{subject}:unselect'))
        else:
            keyboard.add(InlineKeyboardButton(f'❌ {subject}', callback_data=f'subject:{subject}:select'))
    return keyboard


@dp.message_handler(lambda message: message.text == "Выбрать любимые категории",
                    state="*")
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    await message.reply("Выбери свои любимые предметы:", reply_markup=await create_subjects_keyboard(user_id))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject:'))
async def process_subject_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    subject, action = callback_query.data.split(':')[1:]
    selected_subjects = await db.get_categories(user_id)
    if action == 'select':
        selected_subjects.append(subject)
    elif action == 'unselect':
        selected_subjects.remove(subject)
    await db.write_categories(user_id, selected_subjects)
    new_keyboard = await create_subjects_keyboard(user_id)
    if new_keyboard.inline_keyboard != callback_query.message.reply_markup.inline_keyboard:
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=new_keyboard)

    await bot.answer_callback_query(callback_query.id, f'Ты выбрал предметы: {", ".join(selected_subjects)}')


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if await db.user_exists(message.from_user.id):
        # send recs
        await bot.send_message(message.from_user.id, "Рад видеть тебя снова!")
    else:
        await bot.send_message(message.from_user.id, "Привет!\nДля начала мне нужно узнать кое-что о тебе.")
        await message.answer("Укажи свой возраст:\n")
        await Profile.age.set()


# Заполнение возраста
@dp.message_handler(state=Profile.age)
async def get_age(message, state):
    if message.text.isdigit() and 1 <= int(message.text) <= 120:
        async with state.proxy() as data:
            data['age'] = int(message.text)
        female = KeyboardButton('Женщина')
        male = KeyboardButton('Мужчина')
        buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
        buttons.add(female, male)
        await message.answer('Выбери свой пол', reply_markup=buttons)
        await Profile.next()
    else:
        await message.answer('Пожалуйста, введи настоящий возраст')


# Заполнение гендера
@dp.message_handler(state=Profile.gender)
async def get_gender(message, state):
    async with state.proxy() as data:
        data['gender'] = message.text
    buttons = ReplyKeyboardRemove()
    yes = KeyboardButton('Да')
    no = KeyboardButton('Нет')
    buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add(yes, no)
    await message.answer('Есть ли у тебя домашние животные?', reply_markup=buttons)
    await Profile.next()


# Заполнение индикатора животных
@dp.message_handler(state=Profile.pets_flag)
async def get_pets(message, state):
    async with state.proxy() as data:
        data['pets_flag'] = message.text
    yes = KeyboardButton('Да')
    no = KeyboardButton('Нет')
    buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add(yes, no)
    await message.answer('Есть ли у тебя дети?', reply_markup=buttons)
    await Profile.next()


# Заполнение детей
@dp.message_handler(state=Profile.kids_flag)
async def get_kids(message, state):
    async with state.proxy() as data:
        data['kids_flag'] = message.text
        data['creation_time'] = message.date
    await db.create_profile(state, user_id=message.from_user.id)
    fill_categories = KeyboardButton("Выбрать любимые категории")
    buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add(fill_categories)
    await message.answer('Здорово! Осталось узнать твои предпочтения:', reply_markup=buttons)
    await state.finish()


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Описание бота и команд")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)