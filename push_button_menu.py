from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton


btn_main = KeyboardButton(text="Главное меню")

'''Main menu'''
buttons_main_menu = [
                    [KeyboardButton(text='Ввести данные'),
                    KeyboardButton(text='Вывести данные')],
                    [KeyboardButton(text='Обновить данные'),
                    KeyboardButton(text='Удалить данные')],
                    [btn_main],
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


'''Added tree menu'''
buttons_end_input = [
    [KeyboardButton(text="Добавить дерево"),
     KeyboardButton(text="Выбрать другой день")],
    [btn_main]
]

buttons_end_input_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                             keyboard=buttons_end_input)


'''Updated menu'''
buttons_update = [
    [KeyboardButton(text="День недели"),
     KeyboardButton(text="Название дерева")],
    [KeyboardButton(text="Количество фруктов"), KeyboardButton(text="Найти другую строку")], [btn_main]
]

buttons_updates_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                             keyboard=buttons_update)


buttons_yes_no = [
    [KeyboardButton(text="ДА")],
     [KeyboardButton(text="НЕТ, СОХРАНИТЬ")]
]

buttons_yes_no_menu = ReplyKeyboardMarkup(resize_keyboard=True,
                                             keyboard=buttons_yes_no)
