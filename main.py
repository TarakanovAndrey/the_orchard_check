import re
import gspread
from dotenv import load_dotenv
import os
from numpy.core.defchararray import isdigit
import push_button_menu as nav
from loguru import logger
from google_sheets import (create_google_sheet, authorization, add_row, get_rows,
                           is_exist, update_row, get_row_by_day_tree, clear_table, is_datas_exists)
from aiogram.methods import DeleteWebhook
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message


load_dotenv()


logger.add(
    os.environ.get("LOG_FILE"),
    level='DEBUG',
    rotation="1 week",
    compression="zip",
)


client = authorization(os.environ.get('SCOPES'))
router = Router()


WEEK_DAYS = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
ADD_TREE_DAY = None


class Form(StatesGroup):
    weeks_day = State()
    trees_name = State()
    fruits_count = State()


class CountByWeekDaysForm(StatesGroup):
    day_datas = State()


class UpdateDatasForm(StatesGroup):
    updates_day = State()
    updates_tree = State()
    updates_count = State()
    wait_input_parametr = State()
    wait_input_answer = State()
    updates_new_day = State()
    updates_new_tree = State()
    updates_new_count = State()


class ClearDatasForm(StatesGroup):
    wait_answer_by_delete = State()


'''Команда START - запуск бота'''


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    text = f"Привет, {message.from_user.full_name}!"
    await message.answer(text=text)
    await message.answer(text="Я слышал, что из вашего сада стали пропадать фрукты...\n"
                              "Я помогу вам внимательно контроллировать их количество.\n"
                              "Меню очень простое и интуитивно понятное.\n"
                              "Уверен, что вы справитесь. Удачи!",
                         reply_markup=nav.main_menu)


'''Вывод главного меню'''


@router.message(F.text == "Главное меню")
async def bot_message_main_menu(message: Message, state: FSMContext):
    await state.clear()
    text = "Выберите действие в главном меню ниже"
    await message.answer(text=text, reply_markup=nav.main_menu)


'''ДОБАВЛЕНИЕ НОВЫХ ДАННЫХ В ТАБЛИЦУ'''
'''Ввод дня'''


@router.message(F.text == 'Ввести данные')
async def bot_message_input_datas(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    current_state = await state.get_state()
    logger.info("State", current_state)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


'''Ввод и проверка что день недели введен правильно (не зависит от регистра) и написан на кириллице'''


@router.message(lambda message: isinstance(message.text, str), Form.weeks_day)
async def invalid_weeks_day(message: Message, state: FSMContext):
    if message.text.lower() not in WEEK_DAYS:
        await state.set_state(Form.weeks_day)
        text = (f"Это некорректное значение дня недели. "
                f"Пожалуйста, выберите день недели из меню ниже")
        await message.answer(text=text, reply_markup=nav.week_days_menu)
    else:
        await day(message, state)


@router.message(Form.weeks_day)
async def day(message: Message, state: FSMContext) -> None:
    await state.update_data(weeks_day=message.text)
    await state.set_state(Form.trees_name)
    text = "Пожалуйста, введите с помощью клавиатуры название дерева"
    await message.answer(text=text)


'''Проверка название дерева (длина, кириллица) и что такого дерева и дня недели в базе нет'''


@router.message(Form.trees_name)
async def invalid_trees_name(message: Message, state: FSMContext):
    data = await state.get_data()
    day = data['weeks_day']
    trees_name = message.text
    if bool(re.search('[а-яА-Я]', message.text)) is False:
        await state.set_state(Form.trees_name)
        await message.reply(text="Название лучше сохранить на "
                                 "русском языке. Введите пожалуйст еще раз")
    elif len(message.text) > 20:
        await state.set_state(Form.trees_name)
        await message.reply(text=f'Данное значение слишком длинное. '
                                 f'Установлено ограничение в 20 символов.')
    elif is_exist(day, trees_name) is False:
        await message.answer(f"Эти данные '{day} {trees_name}' уже есть в "
                             f"таблице. Не будем их снова добавлять. Введите "
                             f"название другого дерева или перейдите в главное меню")
        await state.set_state(Form.trees_name)
    else:
        await trees(message, state)


@router.message(Form.trees_name)
async def trees(message: Message, state: FSMContext) -> None:
    await state.update_data(trees_name=message.text)
    await state.set_state(Form.fruits_count)
    await message.answer("Введите количество плодов")


'''Проверка что введенные количество плодов является целым числом'''


@router.message(Form.fruits_count)
async def check_fruits_count(message: Message, state: FSMContext) -> None:
    if not isdigit(message.text) and not isinstance(message.text, int):
        await message.reply(text=f'Данное значение не является целым числом. Введите заново')
        await state.set_state(Form.fruits_count)
    else:
        await fruits(message, state)


@router.message(Form.fruits_count)
async def fruits(message: Message, state: FSMContext) -> None:
    await state.update_data(fruits_count=message.text)
    data = await state.get_data()
    row = [data["weeks_day"], data["trees_name"], data["fruits_count"]]
    row_to_str = f"""{data["weeks_day"]} {data["trees_name"]} {data["fruits_count"]}"""
    global ADD_TREE_DAY
    ADD_TREE_DAY = data['weeks_day']

    add_row(row)
    logger.info("Add row", data)
    current_state = await state.get_state()
    logger.info("Clear state", current_state)
    text = f"Вы добавили и сохранили следующую строку:\n{row_to_str}"
    await message.answer(text=text, reply_markup=nav.buttons_end_input_menu)
    await state.clear()


'''Выбор другого дня для добавления данных'''


@router.message(F.text == "Выбрать другой день")
async def choice_day(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    text = 'Выберите день недели'
    await message.answer(text=text, reply_markup=nav.week_days_menu)


'''Добавление новых данных к дню, с которым сейчас работаете'''


@router.message(F.text == "Добавить дерево")
async def add_tree(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    await state.update_data(weeks_day=ADD_TREE_DAY)
    await state.set_state(Form.trees_name)
    await message.answer(text='Введите название дерева')


'''Вывод данных по дню'''


@router.message(F.text == 'Вывести данные')
async def bot_message_output_datas(message: Message, state: FSMContext):
    await state.set_state(CountByWeekDaysForm.day_datas)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


@router.message(CountByWeekDaysForm.day_datas)
async def invalid_output_weeks_day(message: Message, state: FSMContext):
    if message.text.lower() not in WEEK_DAYS:
        await state.set_state(CountByWeekDaysForm.day_datas)
        text = 'Вы ввели неверное значение. Выберите день недели из меню'
        await message.answer(text=text, reply_markup=nav.week_days_menu)
    else:
        await get_count_fruits_by_day(message)


@router.message(CountByWeekDaysForm.day_datas)
async def get_count_fruits_by_day(message: Message) -> None:
    rows = get_rows(message.text)
    if rows:
        await message.answer(text=f'Данные для дня недели {message.text}:\n{rows}',
                             reply_markup=nav.week_days_menu)
    else:
        await message.answer(text=f"Данные для дня недели {message.text} отсутствуют в таблице",
                             reply_markup=nav.week_days_menu)


'''Обновление данных в таблице'''


@router.message(F.text == 'Обновить данные')
async def print_update_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(UpdateDatasForm.updates_day)
    text = "Давайте найдем запись, которую вы хотите изменить.\nВыберите день недели"
    await message.answer(text=text, reply_markup=nav.week_days_menu)


@router.message(UpdateDatasForm.updates_day)
async def invalid_updates_weeks_day(message: Message, state: FSMContext):
    if message.text.lower() not in WEEK_DAYS:
        await state.set_state(UpdateDatasForm.updates_day)
        text = 'Вы ввели неверное значение. Выберите день недели из меню'
        await message.answer(text=text, reply_markup=nav.week_days_menu)
    else:
        await get_datas_by_day(message, state)


@router.message(UpdateDatasForm.updates_day)
async def get_datas_by_day(message: Message, state: FSMContext) -> None:
    rows = get_rows(message.text)
    if rows:
        await state.update_data(updates_day=message.text)
        await state.set_state(UpdateDatasForm.updates_tree)
        await message.answer(text=f"Данные за {message.text}\n{rows}\n\nЧтобы "
                                  f"понять какую строку вы хотите изменить, "
                                  f"укажите название дерева")
    else:
        await state.set_state(UpdateDatasForm.updates_day)
        await message.answer(text=f'День недели - {message.text}:\nВ таблице '
                                  f'нет данных для этого дня. Выберите другой день',
                             reply_markup=nav.week_days_menu)


@router.message(UpdateDatasForm.updates_tree)
async def get_row_for_update(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    day = state_data['updates_day']
    tree = message.text
    row = get_row_by_day_tree(day, tree)
    if row:
        await state.update_data(updates_tree=message.text)
        await state.set_state(UpdateDatasForm.wait_input_parametr)
        await message.answer(text=f"Строка в которой вы хотите обновить данные:\n{row}")
        await message.answer(text="Выберите из меню какой параметр вы хотите изменить",
                             reply_markup=nav.buttons_updates_menu)
    else:
        await state.set_state(UpdateDatasForm.updates_tree)
        await message.answer(text=f'День недели - {day}, дерево - {tree}:\nТакого дерева '
                                  f'не записано в этот день.\nПовторите ввод названия дерева')


@router.message(UpdateDatasForm.wait_input_parametr)
async def get_param_for_update(message: Message, state: FSMContext) -> None:
    if message.text == "День недели":
        await state.set_state(UpdateDatasForm.updates_new_day)
        await message.answer(text='Выберите новый день из меню',
                             reply_markup=nav.week_days_menu)
    elif message.text == "Название дерева":
        await state.set_state(UpdateDatasForm.updates_new_tree)
        await message.answer(text="Введите новое название дерева")
    elif message.text == "Количество фруктов":
        await state.set_state(UpdateDatasForm.updates_new_count)
        await message.answer(text="Введите новое значение для количества")
    elif message.text == "Найти другую строку":
        await state.set_state(UpdateDatasForm.updates_day)
        await message.answer(text='Выберите другой день из меню',
                             reply_markup=nav.week_days_menu)
        await state.clear()


@router.message(UpdateDatasForm.updates_new_day)
async def invalid_weeks_day_for_update(message: Message, state: FSMContext):
    if message.text.lower() not in WEEK_DAYS:
        await state.set_state(UpdateDatasForm.updates_new_day)
        text = (f"Это некорректное значение дня недели. "
                f"Пожалуйста, выберите день недели из меню ниже")
        await message.answer(text=text, reply_markup=nav.week_days_menu)
    else:
        await update_by_new_day(message, state)


@router.message(UpdateDatasForm.updates_new_day)
async def update_by_new_day(message: Message, state: FSMContext) -> None:
    new_day = message.text
    await state.update_data(updates_new_day=new_day)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?",
                         reply_markup=nav.buttons_yes_no_menu)


@router.message(UpdateDatasForm.wait_input_answer)
async def get_answer(message: Message, state: FSMContext) -> None:
    if message.text == 'ДА':
        await state.set_state(UpdateDatasForm.wait_input_parametr)
        await message.answer(text="Выберите новый параметр из меню",
                             reply_markup=nav.buttons_updates_menu)
    elif message.text == 'НЕТ, СОХРАНИТЬ':
        data = await state.get_data()
        update_row(data)
        await state.clear()
        await message.answer(text='Данные сохранены', reply_markup=nav.main_menu)


'''Проверка для названия дерева и наличия новых дня и дерева в таблице'''


@router.message(UpdateDatasForm.updates_new_tree)
async def invalid_new_trees_name(message: Message, state: FSMContext):
    data = await state.get_data()
    day_new = None
    day_current = None
    trees_name = message.text

    if data.get('updates_new_day'):
        day_new = data['updates_new_day']
    if data.get('updates_day'):
        day_current = data['updates_day']

    if bool(re.search('[а-яА-Я]', message.text)) is False:
        await state.set_state(UpdateDatasForm.updates_new_tree)
        await message.reply(text="Название лучше сохранить на русском языке. "
                                 "Введите пожалуйст еще раз")
    elif len(message.text) > 20:
        await state.set_state(UpdateDatasForm.updates_new_tree)
        await message.reply(text=f'Данное значение слишком длинное. '
                                 f'Установлено ограничение в 20 символов.')
    elif not day_new and is_exist(day_current, trees_name) is False:
        await message.reply(text=f"Эти данные '{day_current} {trees_name}' уже есть в "
                            f"таблице. Выберите другой параметр",
                            reply_markup=nav.buttons_updates_menu)
        await state.set_state(UpdateDatasForm.wait_input_parametr)
    elif day_new in data and is_exist(day_new, trees_name) is False:
        await message.reply(text=f"Эти данные '{day_new} {trees_name}' уже есть в "
                            f"таблице. Выберите другой параметр",
                            reply_markup=nav.buttons_updates_menu)
        await state.set_state(UpdateDatasForm.wait_input_parametr)
    else:
        await update_by_new_tree(message, state)


@router.message(UpdateDatasForm.updates_new_tree)
async def update_by_new_tree(message: Message, state: FSMContext) -> None:
    new_tree = message.text
    await state.update_data(updates_new_tree=new_tree)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?",
                         reply_markup=nav.buttons_yes_no_menu)


@router.message(UpdateDatasForm.updates_new_count)
async def update_by_new_count(message: Message, state: FSMContext) -> None:
    new_count = message.text
    await state.update_data(updates_new_count=new_count)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?", reply_markup=nav.buttons_yes_no_menu)


'''Очищение таблицы (кроме заголовков)'''


@router.message(F.text == "Удалить данные")
async def response_to_delete_datas(message: Message, state: FSMContext) -> None:
    await message.answer(text="Данное действие приведен к полному удалению "
                              "всех данных. Вы уверены, что хотите все удалить?",
                         reply_markup=nav.buttons_yes_no_menu)
    await state.set_state(ClearDatasForm.wait_answer_by_delete)


@router.message(ClearDatasForm.wait_answer_by_delete)
async def clear_datas(message: Message, state: FSMContext):
    check_data_exists = is_datas_exists(os.environ.get("GOOGLE_SHEET_NAME"))
    if message.text == "ДА" and check_data_exists:
        clear_table()
        await message.answer(text="Все данные были удалены",
                             reply_markup=nav.main_menu)
    elif message.text == "ДА" and not check_data_exists:
        await message.answer(text="Таблица пустая, так как данные еще не вносились",
                             reply_markup=nav.main_menu)
    elif message.text == "НЕТ, СОХРАНИТЬ":
        await message.answer(text="Данные не были удалены",
                             reply_markup=nav.main_menu)

    await state.clear()


'''Обработка случая, когда сообщения или команда не существует в боте'''


@router.message()
async def get_anything(message: Message) -> None:
    await message.answer(text='Я не знаю таких команд. '
                              'Пожалуйста, воспользуйтесь меню',
                         reply_markup=nav.main_menu)


async def main():
    bot = Bot(token=os.environ.get("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        sheet = client.open(os.environ.get("GOOGLE_SHEET_NAME"))
    except gspread.exceptions.SpreadsheetNotFound:
        create_google_sheet(client, os.environ.get("GOOGLE_SHEET_NAME"))

    asyncio.run(main())
