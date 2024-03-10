from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton
from aiogram import types




btn_main = KeyboardButton(text="Главное меню")

'''Main menu'''
buttons_main_menu = [
                    [KeyboardButton(text='Ввести данные'),
                    KeyboardButton(text='Вывести данные')],
                    [KeyboardButton(text='Обновить данные'),
                    KeyboardButton(text='Удалить данные')],
                    [KeyboardButton(text='Устроить засаду'),
                    btn_main],
                ]
main_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                keyboard=buttons_main_menu)




'''Week days menu'''
buttons_week_days = [
    [KeyboardButton(text="Понедельник"),
    KeyboardButton(text="Вторник")],
    [KeyboardButton(text="Среда"),
    KeyboardButton(text="Четверг")],
    [KeyboardButton(text="Пятница"),
    KeyboardButton(text="Суббота")],
    [KeyboardButton(text="Воскресенье"),
     btn_main]
     ]

week_days_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                     keyboard=buttons_week_days,
                                     input_field_placeholder="Выберите день недели")


buttons_end_input = [
    [KeyboardButton(text="Добавить дерево"),
     KeyboardButton(text="Выбрать другой день")],
    [btn_main]
]

buttons_end_input_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                             keyboard=buttons_end_input)