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
dp = Dispatcher(bot, storage=MemoryStorage())


async def on_startup(_):
    await db.db_connect()

data_manager = DataManager()


class Profile(StatesGroup):
    age = State()
    gender = State()
    pets_flag = State()
    kids_flag = State()


categories = ['Еда и продукты', 'Одежда, обувь', 'Дом и ремонт', 'Еда с доставкой',
              'Цветы и подарки', 'Обучение', 'Аптеки и медицина', 'Авто', 'Красота и парфюмерия',
              'Электроника', 'Кафе, бары и рестораны', 'Товары для животных', 'Спорт', 'Уход за собой',
              'Хобби и равлечения', 'Услуги и сервис', 'Путешествия', 'Такси и каршеринг',
              'Ювелирные изледия и часы', 'Товары для детей', 'Оптика', 'Книги, кино, искусство']


async def create_subjects_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    selected_categories = await db.get_categories(user_id)
    for category in categories:
        # Если предмет уже выбран, делаем кнопку неактивной
        if category in selected_categories:
            keyboard.add(InlineKeyboardButton(f'✅ {category}', callback_data=f'subject:{category}:unselect'))
        else:
            keyboard.add(InlineKeyboardButton(f'❌ {category}', callback_data=f'subject:{category}:select'))
    keyboard.add(InlineKeyboardButton(text="Готово", callback_data=f'subject:{""}:done'))
    return keyboard


@dp.callback_query_handler(lambda c: c.data == 'show_recommendations')
async def show_recommendations(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    rec_item_id = data_manager.get_first_recs(user_id)

    img_url, category, text_info = data_manager.get_item_data(rec_item_id)
    # img_url = 'pics/nutella.png'
    # text_info = 'Nutella\n\nNutella - ореховая паста с какао и снеки с Nutella.\n\nКэшбек 10%\n\nЧтобы получить бонусы, после покупки добавьте чек в приложение Тинькофф: нажмите на транзакцию и отсканируйте QR-код с чека.\nУсловия:\nАкция действует на все товары Nutella во всех офлайн- и онлайн-магазинах, кроме маркетплейсов «Мегамаркет», «Яндекс Маркет», Ozon, Wildberries.\nМаксимум за всё время акции — 500 бонусов.\nБонусы рассчитываются в течение 10 дней после покупки.'

    print(img_url)
    with open(img_url, 'rb') as photo:
        photo = InputFile(photo)
        await bot.send_photo(user_id, photo, caption=text_info)

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("💔", callback_data=f"button1:{rec_item_id}")
    button2 = InlineKeyboardButton("❤", callback_data=f"button2:{rec_item_id}")
    keyboard.add(button1, button2)

    await bot.send_message(user_id, "Пожалуйста, оцени качество рекомендации.", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button'))
async def process_callback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    button_number, item_id = callback_query.data.split(":")
    if button_number[-1] == '1':
        db.write_feedback(user_id, int(item_id), -1, callback_query.message.date)
    elif button_number[-1] == '2':
        db.write_feedback(user_id, int(item_id), 1, callback_query.message.date)
    await show_recommendations(callback_query)


@dp.message_handler(lambda message: message.text == "Выбрать любимые категории",
                    state="*")
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    keyboard = await create_subjects_keyboard(user_id)
    await message.answer(text="Выбери свои любимые категории:", reply_markup=keyboard)


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
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="Показать рекомендации", callback_data="show_recommendations"))
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=keyboard)
    await db.write_categories(user_id, selected_subjects)
    new_keyboard = await create_subjects_keyboard(user_id)
    if new_keyboard.inline_keyboard != callback_query.message.reply_markup.inline_keyboard:
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=new_keyboard)
    # await bot.answer_callback_query(callback_query.id, f'Ты выбрал предметы: {", ".join(selected_subjects)}')


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
