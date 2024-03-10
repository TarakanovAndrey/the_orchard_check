# import gspread
# from aiogram import Bot, types
# from aiogram import Dispatcher
import re

from dotenv import load_dotenv
import os

from numpy.core.defchararray import isdigit

# import asyncio
# from aiogram.filters import CommandStart, Command
import push_button_menu as nav
# from aiogram import F, Router
from loguru import logger
# import pprint as pp
from google_sheets import create_google_sheet, client, add_row, get_rows, is_exist, update_day_in_row, get_row_by_day_tree
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from aiogram.types.callback_query import CallbackQuery
from aiogram.methods import DeleteWebhook




import asyncio
import logging
import sys
from os import getenv
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)






load_dotenv()




logger.add(
    os.environ.get("LOG_FILE"),
    level='DEBUG',
    rotation="1 week",
    compression="zip",
)



router = Router()


WEEK_DAYS = ["Понедельник", "Вторник"]


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





ADD_TREE_DAY = None


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(text=f"Привет, {message.from_user.full_name}!", reply_markup=nav.main_menu)


@router.message(F.text == "Главное меню")
async def bot_message_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Главное меню", reply_markup=nav.main_menu)


'''Добавление новых данных в таблицу'''


@router.message(F.text == 'Ввести данные') #  скрыть кнопки при вводе данных
async def bot_message_input_datas(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info("State", current_state)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)

'''Проверка что день недели введен правильно (не зависит от регистра) и написан на кириллице'''
@router.message(lambda message: isinstance(message.text, str), Form.weeks_day)
async def invalid_weeks_day(message: Message, state: FSMContext):
    if (message.text).lower() not in ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']:
        await state.set_state(Form.weeks_day)
        await message.answer('Вы ввели неверное значение. Выберите день недели из меню', reply_markup=nav.week_days_menu)
    else:
        await day(message, state)

@router.message(Form.weeks_day)
async def day(message: Message, state: FSMContext) -> None:
    await state.update_data(weeks_day=message.text)
    print(message.text)
    await state.set_state(Form.trees_name)
    await message.answer("Введите название дерева")


'''Проверка название дерева (длина, кириллица) и что такого дерева и дня недели в базе нет'''
@router.message(lambda message: isinstance(message.text, str), Form.trees_name)
async def invalid_trees_name(message: Message, state: FSMContext):
    data = await state.get_data()
    day = data['weeks_day']
    trees_name = message.text
    if bool(re.search('[а-яА-Я]', message.text)) is False:
        await state.set_state(Form.trees_name)
        await message.reply(text="Название лучше сохранить на русском языке. Введите пожалуйст еще раз")
    elif len(message.text) > 20:
        await state.set_state(Form.trees_name)
        await message.reply(text=f'Данное значение слишком длинное. Установлено ограничение в 20 символов.')
    elif is_exist(day, trees_name) is False:
        await message.reply(f"Эти данные '{day} {trees_name}' уже есть в таблице. Не будем их снова добавлять. Введите название другого дерева или перейдите в главное меню")
        await state.set_state(Form.trees_name)
    else:
        await trees(message, state)

@router.message(Form.trees_name)
async def trees(message: Message, state: FSMContext) -> None:
    await state.update_data(trees_name=message.text)
    print(message.text)
    await state.set_state(Form.fruits_count)
    await message.answer("Введите количество плодов")


'''Проверка что введенные количество плодов является целым числом'''


@router.message(Form.fruits_count)
async def check_fruits_count(message: Message, state: FSMContext) -> None:
    if not isdigit(message.text):
        await message.reply(text=f'Данное значение не является целым числом. Введите заново')
        await state.set_state(Form.fruits_count)

    else:
        await fruits(message, state)


@router.message(Form.fruits_count)
async def fruits(message: Message, state: FSMContext) -> None:
    await state.update_data(fruits_count=message.text)
    print(message.text)
    data = await state.get_data()
    global ADD_TREE_DAY
    ADD_TREE_DAY = data['weeks_day']
    print(data)
    add_row(client, os.environ.get("GOOGLE_SHEET_NAME"), [data["weeks_day"], data["trees_name"], data["fruits_count"]])
    logger.info("Add row", data)
    current_state = await state.get_state()
    logger.info("Clear state", current_state)
    await message.answer("Вы ввели информацию по одному дереву", reply_markup=nav.buttons_end_input_menu) # можно добавить кнопки выхода и добавить
    await state.clear()

'''Выбор другого дня для добавления данных'''
@router.message(F.text=="Выбрать другой день")
async def choice_day(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


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
    current_state = await state.get_state()
    if current_state is None: # а нужна ли эта конструкция
        return
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


@router.message(CountByWeekDaysForm.day_datas)
async def get_count_fruits_by_day(message: Message, state: FSMContext) -> None:
    rows = get_rows(message.text)
    if rows:
        await message.answer(text=f'Данные за {message.text}:\n{rows}', reply_markup=nav.week_days_menu)
    else:
        await message.answer(text=f"Данные за {message.text} отсутствуют в таблице", reply_markup=nav.week_days_menu)



'''Обновление данных в таблице'''


@router.message(F.text == 'Обновить данные') #  скрыть кнопки при вводе данных
async def print_update_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(UpdateDatasForm.updates_day)
    await message.answer(text="Давайте найдем запись, которую вы хотите изменить.\nВыберите день недели",
                         reply_markup=nav.week_days_menu)


@router.message(UpdateDatasForm.updates_day)
async def get_datas_by_day(message: Message, state: FSMContext) -> None:
    rows = get_rows(message.text)
    if rows:
        await state.update_data(updates_day=message.text)
        await state.set_state(UpdateDatasForm.updates_tree)
        await message.answer(text=f"Данные за {message.text}\n{rows}\n\nЧтобы понять какую строку вы хотите изменить, укажите название дерева")
    else:
        await state.set_state(UpdateDatasForm.updates_day)
        await message.answer(text=f'День недели - {message.text}:\nВ таблице нет данных для этого дня. Выберите другой день', reply_markup=nav.week_days_menu)


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
        await message.answer(text="Выберите из меню какой параметр вы хотите изменить", reply_markup=nav.buttons_updates_menu)
    else:
        await state.set_state(UpdateDatasForm.updates_tree)
        await message.answer(text=f'День недели - {day}, дерево - {tree}:\nТакого дерева не записано в этот день.\nПовторите ввод названия дерева')


@router.message(UpdateDatasForm.wait_input_parametr)
async def get_param_for_update(message: Message, state: FSMContext) -> None:
    if message.text == "День недели":
        await state.set_state(UpdateDatasForm.updates_new_day)
        await message.answer(text='Выберите новый день из меню', reply_markup=nav.week_days_menu)
    elif message.text == "Название дерева":
        await state.set_state(UpdateDatasForm.updates_new_tree)
        await message.answer(text="Введите новое название дерева")
    elif message.text == "Количество фруктов":
        await state.set_state(UpdateDatasForm.updates_new_count)
        await message.answer(text="Введите новое значение для количества")


@router.message(lambda message: isinstance(message.text, str), UpdateDatasForm.updates_new_day)
async def invalid_weeks_day_for_update(message: Message, state: FSMContext):
    if (message.text).lower() not in ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']:
        await state.set_state(UpdateDatasForm.updates_new_day)
        await message.answer('Вы ввели неверное значение. Выберите день недели из меню', reply_markup=nav.week_days_menu)
    else:
        await update_by_new_day(message, state)


@router.message(UpdateDatasForm.updates_new_day)
async def update_by_new_day(message: Message, state: FSMContext) -> None:
    new_day = message.text
    await state.update_data(updates_new_day=new_day)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?", reply_markup=nav.buttons_yes_no_menu)


@router.message(UpdateDatasForm.wait_input_answer)
async def get_answer(message: Message, state: FSMContext) -> None:
    if message.text == 'ДА':
        await state.set_state(UpdateDatasForm.wait_input_parametr)
        await message.answer(text="Выберите новый параметр из меню", reply_markup=nav.buttons_updates_menu)
    elif message.text == 'НЕТ, СОХРАНИТЬ':
        data = await state.get_data()
        print(data)
        # await state.clear()


@router.message(UpdateDatasForm.updates_new_tree)
async def update_by_new_tree(message: Message, state: FSMContext) -> None:
    new_tree = message.text
    await state.update_data(updates_new_tree = new_tree)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?", reply_markup=nav.buttons_yes_no_menu)


@router.message(UpdateDatasForm.updates_new_count)
async def update_by_new_count(message: Message, state: FSMContext) -> None:
    new_count = message.text
    await state.update_data(updates_new_count = new_count)
    await state.set_state(UpdateDatasForm.wait_input_answer)
    await message.answer(text="Вы хотите изменить еще какие-либо данные?", reply_markup=nav.buttons_yes_no_menu)


'''Обработка случая, когда сообщения или команда не существует в боте'''


@router.message()
async def get_anything(message: Message) -> None:
    await message.answer(text='Я не понимаю чего ты от меня хочешь. Воспользуйся меню', reply_markup=nav.main_menu)




async def main():
    bot = Bot(token=os.environ.get("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


if __name__ == "__main__":
    # if True:
    #     create_google_sheet(client, os.environ.get("GOOGLE_SHEET_NAME"))

    asyncio.run(main())
