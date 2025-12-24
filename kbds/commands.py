from aiogram.types import BotCommand
user_params=[
    ("help","помощь в навигации")
    ]

admin_params=[
    ("admin","админские команды")
    ]

user_command_list=[BotCommand(command=val1,description=val2) for val1, val2 in user_params]

admin_command_list = user_command_list + [
    BotCommand(command=val1,description=val2) for val1, val2 in admin_params
]