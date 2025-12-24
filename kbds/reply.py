from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton

def get_reply_keyboard(*bttns: list[str],sizes=(2,)):
    builder=ReplyKeyboardBuilder()
    for text in bttns:
        builder.button(text=text)
    return builder.adjust(*sizes).as_markup(resize_keyboard=True)

search_report_status_kb=get_reply_keyboard("Отказ","Отчет","Отмена","Пропустить")

re_contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True)],[KeyboardButton(text="Отмена")]],resize_keyboard=True)

re_update_contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True)],[KeyboardButton(text="Отмена")],[KeyboardButton(text="Пропустить")]],resize_keyboard=True)

search_request_status_kb=get_reply_keyboard("В ожидании","Рассматривается","Отклонено","Обработано","Отмена","Пропустить")

request_yes_no_kb=get_reply_keyboard("Да","Нет","Отмена")

request_keyboard_album=get_reply_keyboard("Отмена","Завершить")

request_keyboard_album_update=get_reply_keyboard("Отмена","Завершить","Пропустить")

request_update_keyboard=get_reply_keyboard("Отмена","Пропустить")

request_keyboard=get_reply_keyboard("Отмена")

user_reply_keyboard=get_reply_keyboard("Мой аккаунт","Создать заявку","Мои активные заявки","Мои неактивные заявки","Мои прошедшие акции","Мои грядущие акции","Грядущие акции","Искать акции","Помощь")

admin_reply_keyboard=get_reply_keyboard("Будущие события","Создать событие","Прошедшие события","Искать заявки","Искать отчеты")

account_keyboard=get_reply_keyboard("Изменить сведения","Удалить аккаунт")

fsm_keyboard=get_reply_keyboard("Шаг назад","Отмена")

update_fsm_keyboard=get_reply_keyboard("Шаг назад","Отмена","Пропустить")

fsm_keyboard_age_limit=get_reply_keyboard("Шаг назад","Отмена","Без ограничения")

fsm_keyboard_media=get_reply_keyboard("Шаг назад","Отмена","Завершить")

update_fsm_keyboard_age_limit=get_reply_keyboard("Шаг назад","Отмена","Без ограничения","Пропустить")

update_fsm_keyboard_media=get_reply_keyboard("Шаг назад","Отмена","Завершить","Пропустить")

contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True)],[KeyboardButton(text="Шаг назад")],[KeyboardButton(text="Отмена")]],resize_keyboard=True)

update_contact_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поделиться номером",request_contact=True)],[KeyboardButton(text="Шаг назад")],[KeyboardButton(text="Отмена")],[KeyboardButton(text="Пропустить")]],resize_keyboard=True)

yes_no_kb=get_reply_keyboard("Да","Нет","Шаг назад","Отмена")

search_fsm_kb=get_reply_keyboard("Пропустить","Отмена")

search_age_fsm_kb=get_reply_keyboard("Пропустить","Отмена","Без ограничения")