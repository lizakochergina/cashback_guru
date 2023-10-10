from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db

TOKEN = ''

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


async def on_startup(_):
    await db.db_connect()


class Profile(StatesGroup):
    name = State()
    gender = State()
    age = State()
    kids_flag = State()
    pets_flag = State()


# Список предметов
subjects = ['Математика', 'Физика', 'Химия', 'Биология', 'Информатика']

# Словарь для хранения выборов пользователей
user_choices = {}


def create_subjects_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    selected_subjects = user_choices.get(user_id, [])  # Получаем предпочтения пользователя
    print(f'selected: {selected_subjects}')
    for subject in subjects:
        # Если предмет уже выбран, делаем кнопку неактивной
        print(subject)
        if subject in selected_subjects:
            keyboard.add(InlineKeyboardButton(f'✅ {subject}', callback_data=f'subject:{subject}:unselect'))
            print("selected")
        else:
            keyboard.add(InlineKeyboardButton(f'❌ {subject}', callback_data=f'subject:{subject}:select'))
            print("not_selected")
    return keyboard


@dp.message_handler(commands=['set_categories'])
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    user_choices.setdefault(user_id, [])  # Инициализируем предпочтения пользователя, если их нет
    await message.reply("Выбери свои любимые предметы:", reply_markup=create_subjects_keyboard(user_id))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject:'))
async def process_subject_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    subject, action = callback_query.data.split(':')[1:]
    print(f'action: {action}')
    print(f'subject: {subject}')
    selected_subjects = user_choices.get(user_id)
    print(type(selected_subjects))
    print(type(user_choices))
    if action == 'select':
        selected_subjects.append(subject)
        print(f'appended : {selected_subjects}')
    elif action == 'unselect':
        selected_subjects.remove(subject)
    user_choices[user_id] = selected_subjects
    print(user_choices)
    print(selected_subjects)
    new_keyboard = create_subjects_keyboard(user_id)
    if new_keyboard.inline_keyboard != callback_query.message.reply_markup.inline_keyboard:
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=new_keyboard)

    await bot.answer_callback_query(callback_query.id, f'Ты выбрал предметы: {", ".join(selected_subjects)}')


@dp.message_handler(commands=['get_recs'])
async def get_reccomendations(message: types.Message):
    if await db.user_exists(message.from_user.id):
        # send recs
        await bot.send_message(message.from_user.id, "Рад видеть тебя снова!")
    else:
        await bot.send_message(message.from_user.id, "Привет!\nДля начала мне нужно узнать кое-что о тебе:")
        await message.reply("Укажи свой возраст:\n")


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if await db.user_exists(message.from_user.id):
        # send recs
        await bot.send_message(message.from_user.id, "Рад видеть тебя снова!")
    else:
        await bot.send_message(message.from_user.id, "Привет!\nДля начала мне нужно узнать кое-что о тебе:")
        await message.reply("Укажи свой возраст:\n")



@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Описание бота и команд")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
