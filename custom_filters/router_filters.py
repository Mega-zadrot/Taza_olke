from aiogram.filters import Filter
from aiogram import types,Bot
class TypeCheck(Filter):
    def __init__(self,chat_types: list[str]):
        self.chat_types=chat_types
    async def __call__(self,message: types.Message):
        return message.chat.type in self.chat_types
class IsAdmin(Filter):
    def __init__(self):
        pass
    async def __call__(self,message: types.Message, bot: Bot):
        return message.from_user.id in bot.my_admins_list