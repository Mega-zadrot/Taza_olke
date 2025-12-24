# python imports
import os
import asyncio
#framework imports
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
#idk
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
#code organisation imports
from kbds.commands import user_command_list
from handlers.admin_private import admin_private_router,admin_reply_keyboard
from handlers.user_private import user_private_router
from middlewares.db import DataBaseSession
from database.engine import session_maker,create_db,drop_db
from custom_filters.router_filters import TypeCheck
from kbds.commands import admin_command_list
from utils.time import daily_notifier
from database.queries import orm_read_tommorow_events,orm_user_list

bot = Bot(token=os.getenv("TOKEN"))
bot.my_admins_list=[]
dp = Dispatcher()
dp.include_router(admin_private_router)
dp.include_router(user_private_router)

async def on_startup(bot):
#    await create_db()
    print("run")
    await bot.set_my_commands(commands=user_command_list,scope=types.BotCommandScopeAllPrivateChats())
    await drop_db()

dp.startup.register(on_startup)
dp.update.middleware(DataBaseSession(session_pool=session_maker))
#PRAVA POLUCHAEM
@dp.message(Command("admin"),TypeCheck(['group']))
async def get_admins(message: types.Message,bot: Bot):
    admins_list=await bot.get_chat_administrators(message.chat.id)
    bot.my_admins_list=[member.user.id for member in admins_list if member.status == "creator" or member.status=="administrator"]
    if message.from_user.id in bot.my_admins_list:
        await message.delete()
    for admin_id in bot.my_admins_list:
        await bot.set_my_commands(commands=admin_command_list,scope=types.BotCommandScopeChat(chat_id=admin_id))
    if message.from_user.id in bot.my_admins_list:
        await bot.send_message(chat_id=message.from_user.id,text="Права получены введите /admin ",reply_markup=admin_reply_keyboard)

@daily_notifier
async def message_sender():
    async with session_maker() as session:
        events_for_tw=await orm_read_tommorow_events(session)
        if not events_for_tw:
            return
        else:
            for event in events_for_tw:
                users=await orm_user_list(session,event.id)
                if not users:
                    continue
                else:
                    for user in users:
                        await bot.send_message(chat_id=user.user_id,text=f"У вас завтра запись на {event.name.lower()}")

async def main():
    asyncio.create_task(message_sender())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())