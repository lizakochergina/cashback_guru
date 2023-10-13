from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db
from funcs import DataManager

TOKEN = '1859711813:AAHpBzR1-iV6wCpAZH1Y6D75GuRIrKjslwA'

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

emoji_categories = {
    'Еда и продукты': '🍜',
    'Дом и ремонт': '🛠',
    'Одежда, обувь, аксессуары':'🛍',
    'Путешествия': '🛩',
    'Аптеки и медицина': '💊',
    'Услуги и сервис': '📦',
    'Электроника': '📱',
    'Кафе, бары и рестораны': '🍸',
    'Книги, кино, искусство': '🩰',
    'Авто': '🚗',
    'Цветы и подарки': '💐',
    'Товары для детей': '🍼',
    'Такси и каршеринг': '🚕',
    'Товары для животных': '🦄'
}


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
    print('show rec for', user_id)

    last_seen_rec = await db.check_last_seen_rec(user_id)

    if last_seen_rec[1] == 0:
        rec_item_id = last_seen_rec[0]
        img_url, category, text_info, cashback, condition, exp_date_txt, brand = data_manager.get_item_data(last_seen_rec[0])
    else:
        rec_item_id = data_manager.get_recs(user_id)

        if rec_item_id is None:
            await bot.send_message(user_id, "Пока что на этом все!")
            return

        img_url, category, text_info, cashback, condition, exp_date_txt, brand = data_manager.get_item_data(rec_item_id)
        data_manager.write_last_seen(user_id, rec_item_id)
        await db.write_rec_id(user_id, rec_item_id)

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("💔", callback_data=f"button1:{rec_item_id}")
    button2 = InlineKeyboardButton("❤", callback_data=f"button2:{rec_item_id}")
    keyboard.add(button1, button2)

    brand_info = f'<b>{brand}</b>\n'
    text_info = (text_info + '\n') if text_info is not None else ''
    categ_info = emoji_categories[category] + ' ' + category + '\n'
    cond_info = ('❗' + ' ' + condition + '\n') if condition is not None else ''
    exp_info = ('⏳' + ' ' + exp_date_txt) if exp_date_txt is not None else ''
    msg_text = brand_info + text_info + categ_info + cond_info + exp_info

    with open(img_url, 'rb') as photo:
        photo = InputFile(photo)
        message = await bot.send_photo(user_id, photo, caption=msg_text, reply_markup=keyboard, parse_mode='HTML')
        data_manager.write_last_seen_msg_id(user_id, message.message_id)
        await db.write_msg_id(user_id, message.message_id)


@dp.callback_query_handler(lambda c: c.data == 'show_recommendations')
async def show_recs_from_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await show_recs(user_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button'))
async def process_callback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    button_number, item_id = callback_query.data.split(":")
    data_manager.mark_last_seen(user_id)
    await db.mark_last_rec(user_id)
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
    user_id = message.from_user.id
    if await db.user_exists(user_id):
        # send recs
        print('old user connects', user_id)
        last_msg_id = await db.get_last_msg_id(user_id)
        last_msg_id = last_msg_id[0]
        if last_msg_id != -1:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            await db.write_msg_id(user_id, -1)
            data_manager.write_last_seen_msg_id(user_id, -1)
        await bot.send_message(message.from_user.id, "Рад видеть тебя снова! Лови новые кэшбеки 💸💸💸")
        await show_recs(message.from_user.id)
    else:
        print('new user connects', user_id)
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
    if message.text.isalpha() and (message.text == "Женщина" or message.text == "Мужчина"):
        user_id = message.from_user.id
        async with state.proxy() as data:
            data['sex'] = message.text
            data_manager.add_sex(user_id, message.text)
        yes = KeyboardButton('Да')
        no = KeyboardButton('Нет')
        buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
        buttons.add(yes, no)
        await message.answer('Есть ли у тебя домашние животные?', reply_markup=buttons)
        await Profile.next()
    else:
        await message.answer("Пожалуйста, нажми на одну из кнопок")


# fill pets flag
@dp.message_handler(state=Profile.pets_flag)
async def get_pets(message, state):
    if message.text.isalpha() and (message.text == "Да" or message.text == "Нет"):
        user_id = message.from_user.id
        async with state.proxy() as data:
            val = 1 if message.text == 'Да' else 0
            data['pets_flag'] = val
            data_manager.add_pets(user_id, val)
        yes = KeyboardButton('Да')
        no = KeyboardButton('Нет')
        buttons = ReplyKeyboardMarkup(one_time_keyboard=True)
        buttons.add(yes, no)
        await message.answer('Есть ли у тебя дети?', reply_markup=buttons)
        await Profile.next()
    else:
        await message.answer("Пожалуйста, нажми на одну из кнопок")


# fill kids flag
@dp.message_handler(state=Profile.kids_flag)
async def get_kids(message, state):
    if message.text.isalpha() and (message.text == "Да" or message.text == "Нет"):
        user_id = message.from_user.id
        async with state.proxy() as data:
            val = 1 if message.text == 'Да' else 0
            data['kids_flag'] = val
            data['creation_time'] = message.date
            data_manager.add_kids(user_id, val)
            data_manager.add_time(user_id, message.date)
        await db.create_profile(state, user_id=message.from_user.id)

        await state.finish()

        msg = 'Еще чуть-чуть и мы начинаем показывать тебе супер выгодные предложения.'
        await bot.send_message(user_id, msg, reply_markup=ReplyKeyboardRemove())

        msg = 'Выбери несколько категорий, на основе которых мы построим тебе первые рекоммендации.'
        keyboard_page1 = await create_subjects_keyboard(user_id, page=1)
        await message.answer(text=msg, reply_markup=keyboard_page1)
        await db.save_current_page(user_id, page=1)
    else:
        await message.answer("Пожалуйста, нажми на одну из кнопок")


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
