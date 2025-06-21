from aiogram.types import BotCommand
user_params=[("help","помощь в навигации"),("my_account","сведения о вашем аккаунте"),("create_account","создать аккаунт"),("delete_account","удалить аккаунт"),("change_account","обновить сведения"),("my_past_events","акции в которых вы приняли участие"),("events","доступные акции"),("my_future_events","ваши регистрации")]
user_command_list=[BotCommand(command=val1,description=val2) for val1, val2 in user_params]
admin_command_list = user_command_list + [
    BotCommand(command="admin", description="список админских команд")
]