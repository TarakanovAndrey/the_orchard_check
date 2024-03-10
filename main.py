# import gspread
# from aiogram import Bot, types
# from aiogram import Dispatcher
from dotenv import load_dotenv
import os
# import asyncio
# from aiogram.filters import CommandStart, Command
import push_button_menu as nav
# from aiogram import F, Router
from loguru import logger
# import pprint as pp
from google_sheets import create_google_sheet, client, add_row, get_rows
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





ADD_TREE_DAY = None


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(text=f"Привет, {message.from_user.full_name}!", reply_markup=nav.main_menu)


@router.message(F.text == "Главное меню")
async def bot_message_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Главное меню", reply_markup=nav.main_menu)


@router.message(F.text == 'Ввести данные') #  скрыть кнопки при вводе данных
async def bot_message_input_datas(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info("State", current_state)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)





@router.message(Form.weeks_day)
async def day(message: Message, state: FSMContext) -> None:
    await state.update_data(weeks_day=message.text)
    print(message.text)
    await state.set_state(Form.trees_name)
    await message.answer("Введите название дерева")


@router.message(Form.trees_name)
async def trees(message: Message, state: FSMContext) -> None:
    await state.update_data(trees_name=message.text)
    print(message.text)
    await state.set_state(Form.fruits_count)
    await message.answer("Введите количество плодов")



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

@router.message(F.text=="Выбрать другой день")
async def choice_day(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


@router.message(F.text == "Добавить дерево")
async def add_tree(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.weeks_day)
    await state.update_data(weeks_day=ADD_TREE_DAY)
    await state.set_state(Form.trees_name)
    await message.answer(text='Введите название дерева')



@router.message(F.text == 'Вывести данные')
async def bot_message_output_datas(message: Message, state: FSMContext):
    await state.set_state(CountByWeekDaysForm.day_datas)
    current_state = await state.get_state()
    if current_state is None: # а нужна ли эта конструкция
        return
    await message.answer(text='Выберите день недели', reply_markup=nav.week_days_menu)


@router.message(CountByWeekDaysForm.day_datas)
async def get_count_fruits_by_day(message: Message, state: FSMContext) -> None:
    # rows = get_rows(client, os.environ.get("GOOGLE_SHEET_NAME"), message.text)
    # await message.answer(text=f"{rows}", reply_markup=nav.week_days_menu)
    rows = get_rows(message.text)
    await message.answer(text=f'Данные за {message.text}:\n{rows}', reply_markup=nav.week_days_menu)

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
