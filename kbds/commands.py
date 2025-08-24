from aiogram.types import BotCommand
user_params=[
    ("help","помощь в навигации"),
    ("my_account","сведения о вашем аккаунте"),
    ("create_account","создать аккаунт"),
    ("delete_account","удалить аккаунт"),
    ("change_account","обновить сведения"),
    ("my_past_events","акции в которых вы приняли участие"),
    ("events","доступные акции"),
    ("search_events","поиск событий"),
    ("my_future_events","ваши регистрации")]

admin_params=[
    ("admin","админские команды"),
    ("admin_past_events","просмотреть прошедшие события созданые вами"),
    ("admin_future_events","просмотреть грядущие события созданые вами"),
    ("create_event","создать акцию")
]

user_command_list=[BotCommand(command=val1,description=val2) for val1, val2 in user_params]

admin_command_list = user_command_list + [
    BotCommand(command=val1,description=val2) for val1, val2 in admin_params
]