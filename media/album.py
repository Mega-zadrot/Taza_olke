from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message
from utils.render import render_event, render_my_event
from database.models import Event
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