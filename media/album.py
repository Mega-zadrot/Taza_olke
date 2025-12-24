from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message,ReplyKeyboardRemove
from utils.render import render_event, render_my_event, render_request, render_report
from kbds.inline import get_inline_keyboard
from kbds.reply import admin_reply_keyboard,user_reply_keyboard
from database.models import Event, Request, Report
from database.queries import orm_count_users
async def send_event(event: dict | Event, message: Message, state: bool | None = "no",user_num: int = 0):
    if isinstance(event,Event):
        if event.album is not None and state=="no":
            album=MediaGroupBuilder(caption=render_event(event,user_num))
            for media_piece in event.album.split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())

        elif event.album is not None and state != "no":
            album=MediaGroupBuilder(caption=render_my_event(event,state))
            for media_piece in event.album.split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())

        elif event.album is None and state=="no":
            await message.answer(render_event(event,user_num))

        elif event.album is None and state != "no":
            await message.answer(render_my_event(event,state))

    elif isinstance(event, dict):
        if event["event_media"] is not None:
            album=MediaGroupBuilder(caption=render_event(event))
            for media_piece in event["event_media"].split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())
        else:
            await message.answer(render_event(event))

async def send_request(request: dict | Request, message: Message):
    if isinstance(request, Request):
        if request.album is not None:
            album=MediaGroupBuilder(caption=render_request(request))
            for media_piece in request.album.split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())
        else:
            await message.answer(render_request(request))
    elif isinstance(request, dict):
        if request["request_album"] is not None:
            album=MediaGroupBuilder(caption=render_request(request))
            for media_piece in request["request_album"].split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())
        else:
            await message.answer(render_request(request))

async def send_report(report: dict | Report, message: Message):
    if isinstance(report, Report):
        if report.album is not None:
            album=MediaGroupBuilder(caption=render_report(report))
            for media_piece in report.album.split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())
            print(message)
        else:
            await message.answer(render_report(report))
    elif isinstance(report, dict):
        if report["report_media"] is not None:
            album=MediaGroupBuilder(caption=render_report(report))
            for media_piece in report["report_media"].split(","):
                if media_piece:
                    type,file_id=media_piece.split(":",1)
                    album.add(type=type,media=file_id)
            await message.answer_media_group(album.build())
        else:
            await message.answer(render_report(report))

async def send_requests(requests,message):
    for request in requests:
        await send_request(message=message,request=request)
        if request.status=="В ожидании":
            await message.answer(
            f"Действия с {request.name.casefold()}",
                reply_markup=get_inline_keyboard(
                data={"Рассмотреть🔎":f"check_{request.id}"}))
        elif request.status=="Рассматривается":
            await message.answer(
            f"Действия с {request.name.casefold()}",
                reply_markup=get_inline_keyboard(
                data={"Отклонить❌":f"decline_{message.from_user.id}_{message.from_user.username}_{request.id}","Обработать✔":f"process_{message.from_user.id}_{message.from_user.username}_{request.id}"}))
        elif request.status=="Обработано":
            await message.answer(
            f"Действия с {request.name.casefold()}",
            reply_markup=get_inline_keyboard(data={"отчет📄":f"get_report_{request.id}"}))
        elif request.status=="Отклонено":
            await message.answer(
            f"Действия с {request.name.casefold()}",
            reply_markup=get_inline_keyboard(data={"комментарий💬":f"get_comment_{request.id}"}))
    await message.answer("Вот список заявок",reply_markup=admin_reply_keyboard)

async def send_events(events,message,session):
    for event in events:
        user_num=await orm_count_users(session,event.id)
        await send_event(message=message,user_num=user_num,event=event)
        await message.answer(
            f"Действия с {event.name.casefold()}",
            reply_markup=get_inline_keyboard(
                data={"Зарегистрироваться✅":f"register_{event.id}"}))
    await message.answer("Вот список событий",reply_markup=user_reply_keyboard)
