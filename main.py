from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db
from funcs import DataManager

TOKEN = '6436284246:AAEb8aEUhFvIegTMMa77mJ2gxYCQJDiuujc'

bot = Bot(token=TOKEN)
print('created bot')
dp = Dispatcher(bot, storage=MemoryStorage())
print('created dp')


async def on_startup(_):
    await db.db_connect()


print('dp connect')

data_manager = DataManager()
print('created data manager')


class Profile(StatesGroup):
    age = State()
    gender = State()
    pets_flag = State()
    kids_flag = State()


categories = ['Еда и продукты', 'Одежда, обувь, аксессуары', 'Дом и ремонт',
              'Цветы и подарки', 'Обучение', 'Аптеки и медицина', 'Авто',
              'Электроника', 'Кафе, бары и рестораны',
              'Услуги и сервис', 'Путешествия', 'Такси и каршеринг', 'Книги, кино, искусство']

categories_page1 = categories[:7]
categories_page2 = categories[7:]


async def create_subjects_keyboard(user_id, page):
    keyboard = InlineKeyboardMarkup()
    selected_categories = await db.get_categories(user_id)

    if page == 1:
        categories_to_display = categories_page1
        next_page = 2
    else:
        categories_to_display = categories_page2
        next_page = 1

    for category in categories_to_display:
        if category in selected_categories:
            keyboard.add(InlineKeyboardButton(f'✅ {category}', callback_data=f'subject:{category}:unselect'))
        else:
            keyboard.add(InlineKeyboardButton(f'❌ {category}', callback_data=f'subject:{category}:select'))

    if page == 1:
        keyboard.row(InlineKeyboardButton('Вперед ➡️', callback_data=f'page:{next_page}'),
                     InlineKeyboardButton(text="Готово 🏁", callback_data=f'subject:{""}:done'))
    else:
        keyboard.row(InlineKeyboardButton('⬅️ Назад', callback_data=f'page:{next_page}'),
                     InlineKeyboardButton(text="Готово 🏁", callback_data=f'subject:{""}:done'))

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('page:'))
async def process_page_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    page = int(callback_query.data.split(':')[1])
    keyboard = await create_subjects_keyboard(user_id, page)

    await db.save_current_page(user_id, page)

    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                        reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Выбрать любимые категории", state="*")
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    keyboard_page1 = await create_subjects_keyboard(user_id, page=1)
    await message.answer(text="Выбери свои любимые категории:", reply_markup=keyboard_page1)
    await db.save_current_page(user_id, page=1)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject:'))
async def process_subject_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    subject, action = callback_query.data.split(':')[1:]
    selected_subjects = await db.get_categories(user_id)
    if action == 'select':
        selected_subjects.append(subject)
    elif action == 'unselect':
        selected_subjects.remove(subject)
    elif action == "done":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await show_recs(user_id)

    await db.write_categories(user_id, selected_subjects)
    data_manager.add_categories(user_id, selected_subjects)
    current_page = await db.get_current_page(user_id)
    new_keyboard = await create_subjects_keyboard(user_id, page=current_page)
    if new_keyboard.inline_keyboard != callback_query.message.reply_markup.inline_keyboard:
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=new_keyboard)


async def show_recs(user_id):
    rec_item_id = data_manager.get_recs(user_id)

    if not rec_item_id:
        await bot.send_message(user_id, "Пока что на этом все!")
        return

    img_url, category, text_info = data_manager.get_item_data(rec_item_id)

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("💔", callback_data=f"button1:{rec_item_id}")
    button2 = InlineKeyboardButton("❤", callback_data=f"button2:{rec_item_id}")
    keyboard.add(button1, button2)

    with open(img_url, 'rb') as photo:
        photo = InputFile(photo)
        await bot.send_photo(user_id, photo, caption=text_info, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'show_recommendations')
async def show_recs_from_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await show_recs(user_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button'))
async def process_callback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    button_number, item_id = callback_query.data.split(":")
    if button_number[-1] == '1':
        db.write_feedback(user_id, int(item_id), 0, callback_query.message.date)
        data_manager.add_interaction(user_id, int(item_id), 0, callback_query.message.date)
    elif button_number[-1] == '2':
        db.write_feedback(user_id, int(item_id), 1, callback_query.message.date)
        data_manager.add_interaction(user_id, int(item_id), 1, callback_query.message.date)
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id)
    await show_recs_from_callback(callback_query)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if await db.user_exists(message.from_user.id):
        # send recs
        await bot.send_message(message.from_user.id, "Рад видеть тебя снова! Лови новые кэшбеки 💸💸💸")
        await show_recs(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, "Привет!\nДля начала мне нужно узнать кое-что о тебе.")
        await message.answer("Укажи свой возраст:\n")
        await Profile.age.set()


# fill age
@dp.message_handler(state=Profile.age)
async def get_age(message, state):
    if message.text.isdigit() and 1 <= int(message.text) <= 120:
        user_id = message.from_user.id
        async with state.proxy() as data:
            data['age'] = int(message.text)
            data_manager.add_age(user_id, int(message.text))
        female = KeyboardButton('Женщина')
        male = KeyboardButton('Мужчина')
        buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
        buttons.add(female, male)
        await message.answer('Выбери свой пол', reply_markup=buttons)
        await Profile.next()
    else:
        await message.answer('Пожалуйста, введи настоящий возраст')


# fill sex
@dp.message_handler(state=Profile.gender)
async def get_gender(message, state):
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['sex'] = message.text
        data_manager.add_sex(user_id, message.text)
    buttons = ReplyKeyboardRemove()
    yes = KeyboardButton('Да')
    no = KeyboardButton('Нет')
    buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add(yes, no)
    await message.answer('Есть ли у тебя домашние животные?', reply_markup=buttons)
    await Profile.next()


# fill pets flag
@dp.message_handler(state=Profile.pets_flag)
async def get_pets(message, state):
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['pets_flag'] = 1 if message.text == 'Да' else 0
        data_manager.add_kids(user_id, message.text)
    yes = KeyboardButton('Да')
    no = KeyboardButton('Нет')
    buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add(yes, no)
    await message.answer('Есть ли у тебя дети?', reply_markup=buttons)
    await Profile.next()


# fill kids flag
@dp.message_handler(state=Profile.kids_flag)
async def get_kids(message, state):
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['kids_flag'] = 1 if message.text == 'Да' else 0
        data['creation_time'] = message.date
        data_manager.add_pets(user_id, message.text)
        data_manager.add_time(user_id, message.date)
    await db.create_profile(state, user_id=message.from_user.id)
    # fill_categories = KeyboardButton("Выбрать любимые категории")
    # buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
    # buttons.add(fill_categories)
    msg = 'Осталось узнать твои предпочтения. Выбери несколько категорий, на основе которых мы построим тебе первые рекоммендации.'
    # await message.answer(msg, reply_markup=buttons)
    await state.finish()

    user_id = message.from_user.id
    keyboard_page1 = await create_subjects_keyboard(user_id, page=1)
    await message.answer(text=msg, reply_markup=keyboard_page1)
    await db.save_current_page(user_id, page=1)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Описание бота и команд")


@dp.message_handler(commands=['stats'])
async def process_help_command(message: types.Message):
    user_id = message.from_user.id
    total, liked, disliked = data_manager.get_stats(user_id)
    msg = "ты просмотрел(а) {} кэшбеков\n❤ {}\n💔 {}".format(total, liked, disliked)
    await bot.send_message(user_id, msg)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
