from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton
def get_reply_keyboard(*bttns: list[str],sizes=(2,)):
    builder=ReplyKeyboardBuilder()
    for text in bttns:
        builder.button(text=text)
    return builder.adjust(*sizes).as_markup(resize_keyboard=True)
admin_reply_keyboard=get_reply_keyboard("просмотреть будущие события","создать событие","просмотреть прошедшие события")

account_keyboard=get_reply_keyboard("изменить сведения","удалить аккаунт")

fsm_keyboard=get_reply_keyboard("шаг назад","отмена")

update_fsm_keyboard=get_reply_keyboard("шаг назад","отмена","пропустить")

fsm_keyboard_age_limit=get_reply_keyboard("шаг назад","отмена","без ограничения")

update_fsm_keyboard_age_limit=get_reply_keyboard("шаг назад","отмена","без ограничения","пропустить")

contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="поделиться номером",request_contact=True)],[KeyboardButton(text="шаг назад")],[KeyboardButton(text="отмена")]],resize_keyboard=True)

update_contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="поделиться номером",request_contact=True),KeyboardButton(text="шаг назад")],[KeyboardButton(text="отмена"),KeyboardButton(text="пропустить")]],resize_keyboard=True)

yes_no_kb=get_reply_keyboard("да","нет","шаг назад","отмена")