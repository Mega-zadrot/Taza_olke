from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton
def get_reply_keyboard(*bttns: list[str],sizes=(2,)):
    builder=ReplyKeyboardBuilder()
    for text in bttns:
        builder.button(text=text)
    return builder.adjust(*sizes).as_markup(resize_keyboard=True)
admin_reply_keyboard=get_reply_keyboard("Будущие события","Создать событие","Прошедшие события")

account_keyboard=get_reply_keyboard("Изменить сведения","Удалить аккаунт")

fsm_keyboard=get_reply_keyboard("Шаг назад","Отмена")

update_fsm_keyboard=get_reply_keyboard("Шаг назад","Отмена","Пропустить")

fsm_keyboard_age_limit=get_reply_keyboard("Шаг назад","Отмена","Без ограничения")

update_fsm_keyboard_age_limit=get_reply_keyboard("Шаг назад","Отмена","Без ограничения","Пропустить")

contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True)],[KeyboardButton(text="Шаг назад")],[KeyboardButton(text="Отмена")]],resize_keyboard=True)

update_contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True),KeyboardButton(text="Шаг назад")],[KeyboardButton(text="Отмена"),KeyboardButton(text="Пропустить")]],resize_keyboard=True)

yes_no_kb=get_reply_keyboard("Да","Нет","Шаг назад","Отмена")

search_fsm_kb=get_reply_keyboard("Пропустить","Отмена")

search_age_fsm_kb=get_reply_keyboard("Пропустить","Отмена","Без ограничения")