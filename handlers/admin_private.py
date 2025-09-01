from datetime import date
from aiogram import types, Router,Bot,F
from aiogram.filters import Command,StateFilter,or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime,date
from sqlalchemy.ext.asyncio import AsyncSession
#modules
from custom_filters.router_filters import TypeCheck,IsAdmin
from kbds.inline import get_inline_keyboard
from kbds.reply import (
    admin_reply_keyboard,
    update_fsm_keyboard,
    fsm_keyboard,
    yes_no_kb,
    fsm_keyboard_age_limit,
    update_fsm_keyboard_age_limit,
    fsm_keyboard_media,
    update_fsm_keyboard_media
)
from database.queries import (
orm_read_events_admin,
orm_add_event,
orm_delete_event,
orm_read_event_name,
orm_read_event,
orm_update_event,
orm_count_users,
orm_user_list,
orm_read_past_events_admin,
orm_read_association,
orm_update_balance,
orm_update_status,
orm_cancel_event,
orm_read_event_point
)
from utils.render import render_event,render_user
from utils.bonus import parse_price_for_postgres
from media.album import send_event

admin_private_router=Router()

admin_private_router.message.filter(TypeCheck(["private"]),IsAdmin())

#fsm class
class EventValue(StatesGroup):
    event_name=State()
    event_point=State()
    event_description=State()
    event_media=State()
    event_date=State()
    event_age=State()
    event_limit=State()
    event_city=State()
    are_you_sure=State()
    texts={
        "EventValue:event_name":"Введите имя",
        "EventValue:event_point":"Введите число баллов",
        "EventValue:event_description":"Введите описание",
        "EventValue:event_date":"Введите дату в формате yyyy-mm-dd",
        "EventValue:event_limit":"Введите число желаемых участников",
        "EventValue:event_age":"Введите минимальный возраст",
        "EventValue:event_city":"Введите город в котором запланирована акция",
        "EventValue:event_media":"Отправьте видео и фото"
        }
    
    list_of_states=[
        event_name,
        event_point,
        event_description,
        event_city,
        event_date,
        event_age,
        event_limit,
        event_media,
        are_you_sure
    ]

#Menu
@admin_private_router.message(Command("admin"))
async def check_priveliegies(message: types.Message):
    await message.answer("Приветствую вас админ! Что пожелаете сделать?\nВы можете: создать событие, редактировать событие, подтверждать присуствие, получать список людей зарегистрированых на ваше события\nК событиям созданые вами только вы имеете доступ",reply_markup=admin_reply_keyboard)

#select
@admin_private_router.message(StateFilter(None),Command("admin_future_events"))
@admin_private_router.message(StateFilter(None),F.text.casefold()=="будущие события")
async def read_events(message: types.Message,session: AsyncSession):
    events= await orm_read_events_admin(session,message.from_user.id)
    if not events:
        await message.answer("Нет событий")
    else:
        for event in events:
            user_num=await orm_count_users(session,event.id)
            await send_event(
                message=message,
                user_num=user_num,
                event=event)
            await message.answer(
                f"Действия с {event.name}",
                reply_markup=get_inline_keyboard(
                    data={"Удалить❌":f"edelete_{event.id}",
                          "Изменить🔁":f"eupdate_{event.id}",
                          "Отменить💔":f"cancel_{event.id}",
                          "Список📃":f"list_{event.id}"
                          }))
        await message.answer("Вот список событий")

#select past events
@admin_private_router.message(StateFilter(None),Command("admin_past_events"))
@admin_private_router.message(StateFilter(None),F.text.casefold()=="прошедшие события")
async def read_past_events(message: types.Message,session: AsyncSession):
    events= await orm_read_past_events_admin(session,message.from_user.id)
    if not events:
        await message.answer("Нет событий")
    else:
        for event in events:
            user_num=await orm_count_users(session,event.id)
            await send_event(
                message=message,
                user_num=user_num,
                event=event)
            await message.answer(
                f"Действия с {event.name}",
                reply_markup=get_inline_keyboard(
                    data={
                          "Список для подтверждения":f"list_{event.id}"
                          }))
        await message.answer("Вот список событий")

#delete
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("edelete_"))
async def delete_event(callback: types.CallbackQuery,session: AsyncSession):
    event_id=int(callback.data.split("_")[-1])
    event_name=await orm_read_event_name(session,event_id)
    if event_name is not None:
        await orm_delete_event(session,event_id)
        await callback.message.answer(f"Событие {event_name.lower()} было удалено")
        await callback.answer("Событие удалено")
    else:
        await callback.message.answer("Уже удалено")
#update
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("eupdate_"))
async def update_event(callback: types.CallbackQuery,session: AsyncSession,state: FSMContext):
    event_id=int(callback.data.split("_")[-1])
    event_for_change=await orm_read_event(session,event_id)
    if event_for_change is not None:
        await state.update_data(event_for_change = event_for_change)
        await callback.answer()
        await callback.message.answer("Введите новое название события",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_name)
        await state.update_data(id=event_id, event_media=None, count=0)
    else:
        await callback.message.answer("Событие было удалено")

#list
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("list_"))
async def list_event(callback: types.CallbackQuery,session: AsyncSession,state: FSMContext):
    event_id=int(callback.data.split("_")[-1])
    users=await orm_user_list(session,event_id)
    event= await orm_read_event(session,event_id)
    if event is not None:
        if users:
            if event.event_date <= date.today():
                for user in users:
                    await callback.message.answer(render_user(user),reply_markup=get_inline_keyboard(data={
                        "Присуствовал✅":f"confirm_yes_{user.user_id}_{event_id}",
                        "Не присуствовал🚫":f"confirm_no_{user.user_id}_{event_id}"
                    }))
                await callback.message.answer("Список пользователей")
            elif event.event_date > date.today():
                for user in users:
                    await callback.message.answer(render_user(user))
                await callback.message.answer("Список пользователей")
        else:
            await callback.message.answer("Никто еще не успел зарегистрироваться")
    else:
        await callback.message.answer("Событие было удалено")

#cancel
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("cancel_"))
async def cancel_event(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    event_id=int(callback.data.split("_")[-1])
    event_name=await orm_read_event_name(session,event_id)
    users=await orm_user_list(session,event_id)
    if event_name is not None and users:
        await orm_cancel_event(session,event_id)
        for user in users:
            await bot.send_message(chat_id=user.user_id,text=f"Событие {event_name.lower()} на которое вы зарегистрировались было отменено")
        await callback.message.answer("Событие было отменено(есть юзеры)")
    elif event_name is not None and not users:
        await callback.message.answer("Событие было отменено(нет юзеров)")
    else:
        await callback.message.answer("Событие было удалено")

#confirm
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("confirm_"))
async def confirm_presence(callback: types.CallbackQuery,session: AsyncSession):
    event_id=int(callback.data.split("_")[-1])
    status=callback.data.split("_")[1]
    user_id=int(callback.data.split("_")[2])
    association=await orm_read_association(session,user_id,event_id)
    event_point= await orm_read_event_point(session,event_id)
    if association is not None:
        if status=="yes" and association.was_there==True:
            await callback.message.answer("Уже подтверждено присуствие этого пользователя")
        elif status=="yes":
            await orm_update_status(session,association,True)
            await orm_update_balance(session,user_id,event_point)
            await callback.message.answer("Подтверждено присуствие этого пользователя")
# if was there False change to True + points if True dont do anything (send message) if None change to True + points
        elif status=="no" and association.was_there==False:
            await callback.message.answer("Уже подтверждено отсуствие этого пользователя")
        elif status=="no" and association.was_there==True:
            await orm_update_status(session,association,False)
            await orm_update_balance(session,user_id,-event_point)
            await callback.message.answer("Подтверждено отсуствие этого пользователя")
        elif status=="no" and association.was_there==None:
            await orm_update_status(session,association,False)
            await callback.message.answer("Подтверждено отсуствие этого пользователя")
    else:
        await callback.message.answer("Либо пользователь удалил свой аккаунт, либо событие было удалено")
# if was there False dont do anything(send message) if None change to False only if True change to false minus points

#FSM for creation and update
@admin_private_router.message(StateFilter(None),Command("create_event"))
@admin_private_router.message(StateFilter(None),F.text.casefold()=="создать событие")
async def create_event(message: types.Message,state: FSMContext):
    await message.answer(
        "Введите имя события(не больше 100 символов(на имя) и отвечайте только текстом на все в противном случае бот не будет вам отвечать)",
        reply_markup=fsm_keyboard)
    await state.set_state(EventValue.event_name)
    await state.update_data(creator_id=message.from_user.id, event_media=None, count=0)
    
#cancel fsm
@admin_private_router.message(StateFilter(*EventValue.list_of_states),F.text.casefold()=="отмена")
async def admin_cancel(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer("Все было отменено",reply_markup=admin_reply_keyboard)

#step backwards
@admin_private_router.message(StateFilter(*EventValue.list_of_states),F.text.casefold()=="шаг назад")
async def admin_step_backwards(message: types.Message,state: FSMContext):
    current_state=await state.get_state()
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if current_state == EventValue.event_name:
        await message.answer("Назад некуда идти")
        return
    elif current_state == EventValue.are_you_sure and event_for_change is not None:
        await state.set_state(EventValue.event_limit)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_limit"]}",reply_markup=update_fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.are_you_sure:
        await state.set_state(EventValue.event_limit)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_limit"]}",reply_markup=fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.event_limit and event_for_change is not None:
        await state.set_state(EventValue.event_age)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_age"]}",reply_markup=update_fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.event_limit:
        await state.set_state(EventValue.event_age)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_age"]}",reply_markup=fsm_keyboard_age_limit)
        return
    elif current_state == EventValue.event_city and event_for_change is not None:
        await state.set_state(EventValue.event_media)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_media"]}",reply_markup=update_fsm_keyboard_media)
        return
    elif current_state == EventValue.event_city:
        await state.set_state(EventValue.event_media)
        await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_media"]}",reply_markup=fsm_keyboard_media)
        return
    elif event_for_change is not None:
        previous=None
        for step in EventValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts[previous.state]}",reply_markup=update_fsm_keyboard)
            else:
                previous=step
    else:
        previous=None
        for step in EventValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"Ок вы вернулись на шаг назад \n{EventValue.texts[previous.state]}",reply_markup=fsm_keyboard)
            else:
                previous=step


@admin_private_router.message(EventValue.event_name,F.text)
async def name_event(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_name=event_for_change.name)
        await message.answer("Ок оставляем это имя, теперь отправьте новое количество баллов за это событие",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_point)
    else:   
        if len(message.text) <= 100:
            await state.update_data(event_name=message.text)
            await message.answer("Теперь отправьте количество баллов за это событие")
            await state.set_state(EventValue.event_point)
        else:
            await message.answer("Имя превысило 100 символов, повторите на этот раз с меньшим количеством")

@admin_private_router.message(EventValue.event_point,F.text)
async def point_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold() =="пропустить" and event_for_change is not None:
            await state.update_data(event_point=event_for_change.point)
            await message.answer("Ок оставляем это количество, теперь отправьте новое описание",reply_markup=update_fsm_keyboard)
            await state.set_state(EventValue.event_description)
        else:
            number_of_points = parse_price_for_postgres(message.text)
            await state.update_data(event_point=number_of_points)
            await message.answer("Теперь отправьте описание")
            await state.set_state(EventValue.event_description)
    except ValueError as e:
            await message.answer(str(e))    

@admin_private_router.message(EventValue.event_description,F.text)
async def desc_event(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_description=event_for_change.description)
        await message.answer("Ок оставляем это описание, теперь отправьте другие фото и видео до 10 штук",reply_markup=update_fsm_keyboard_media)
        await state.set_state(EventValue.event_media)
    else:
        if len(message.text) <= 700:
            await state.update_data(event_description=message.text)
            await message.answer("Теперь отправьте фото и видео до 10 штук",reply_markup=fsm_keyboard_media)
            await state.set_state(EventValue.event_media)
        else:
            await message.answer("Описание превысило 700 символов, повторите на этот раз с меньшим количеством")  
# 4 routes of behaviour: concatenate until 10 th object, finish before 10th(even on None), save current done       
@admin_private_router.message(EventValue.event_media,F.video)        
@admin_private_router.message(EventValue.event_media,F.photo)
async def get_media(message: types.Message,state: FSMContext):
    data=await state.get_data()
    media=data.get("event_media")
    count=data.get("count")
    if count == 10:
        await message.answer(f"Добавлено {count} из 10")
        await message.answer("Теперь отправьте местоположение (город) события",reply_markup=fsm_keyboard)
        await state.set_state(EventValue.event_city)
    else:
        if media is None:
            media=""
        if message.photo:
            media+=f"photo:{message.photo[-1].file_id},"
        else:
            media+=f"video:{message.video.file_id},"
        count += 1
        await state.update_data(event_media=media,count=count)
        await message.answer(f"Добавлено {count} из 10")
    
@admin_private_router.message(EventValue.event_media,F.text)
async def get_media2(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_media=event_for_change.album)
        await message.answer("Ок оставляем эти фото и видео, теперь отправьте другое местоположение",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_city)
    elif message.text.casefold()=="завершить" and event_for_change is not None:
        await message.answer("Теперь отправьте местоположение (город) события",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_city)
    elif message.text.casefold()=="завершить":
        await message.answer("Теперь отправьте местоположение (город) события",reply_markup=fsm_keyboard)
        await state.set_state(EventValue.event_city)

@admin_private_router.message(EventValue.event_city,F.text)
async def event_location(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_city=event_for_change.city)
        await message.answer("Ок оставляем это местоположение, теперь отправьте новую дату",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_date)
    else:
        if len(message.text) <= 100:
            await state.update_data(event_city=message.text.capitalize())
            await message.answer("Теперь отправьте дату в таком формате yyyy-mm-dd")
            await state.set_state(EventValue.event_date)
        else:
            await message.answer("Название города превысило 100 символов, повторите на этот раз с меньшим количеством")

@admin_private_router.message(EventValue.event_date,F.text)
async def date_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_date=event_for_change.event_date)
            await message.answer("Ок оставляем эту дату, теперь отправьте новый минимальный возраст участия",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_age)
            return
        elif event_for_change is not None:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate >= date.today():
                await state.update_data(event_date=edate)
                await message.answer("Теперь отправьте минимальный возраст участия",reply_markup=update_fsm_keyboard_age_limit)
                await state.set_state(EventValue.event_age)
            else:
                await message.answer("Дата не может быть в прошлом времени, повторите пожалуйста")
        else:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate >= date.today():
                await state.update_data(event_date=edate)
                await message.answer("Теперь отправьте минимальный возраст участия",reply_markup=fsm_keyboard_age_limit)
                await state.set_state(EventValue.event_age)
            else:
                await message.answer("Дата не может быть в прошлом времени, повторите пожалуйста")
    except ValueError:
        await message.answer("Была введена дата не в том формате, повторите еще раз(без точек,запятых,пробелов только цифры и -)")

@admin_private_router.message(EventValue.event_age,F.text)
async def age_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_age=event_for_change.required_age)
            await message.answer("Ок оставляем этот минимальный возраст, теперь отправьте новое число участников",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
            return
        elif message.text.casefold()=="без ограничения" and event_for_change is not None:
            await state.update_data(event_age=None)
            await message.answer("Теперь отправьте количество участников",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
        elif message.text.casefold()=="без ограничения":
            await state.update_data(event_age=None)
            await message.answer("Теперь отправьте количество участников",reply_markup=fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
        elif event_for_change is not None:
            age=int(message.text)
            if age < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            elif age > event_for_change.required_age:
                await message.answer("Нельзя вводить возраст больше того что есть")
            else:
                await state.update_data(event_age=age)
                await message.answer("Теперь отправьте количество участников")
                await state.set_state(EventValue.event_limit)
        else:
            age=int(message.text)
            if age < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            else:
                await state.update_data(event_age=age)
                await message.answer("Теперь отправьте количество участников")
                await state.set_state(EventValue.event_limit)
    except ValueError:
            await message.answer("Было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")    

@admin_private_router.message(EventValue.event_limit,F.text)
async def limit_event(message: types.Message,state: FSMContext,session: AsyncSession):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_limit=event_for_change.limit)
            await message.answer("Ок оставляем этот лимит")
            data = await state.get_data()
            await send_event(message=message,event=data)
            await message.answer("Вы довольны?",reply_markup=yes_no_kb)
            await state.set_state(EventValue.are_you_sure)
        elif message.text.casefold()=="без ограничения":
                await state.update_data(event_limit=None)
                data = await state.get_data()
                await send_event(message=message,event=data)
                await message.answer("Вы довольны?",reply_markup=yes_no_kb)
                await state.set_state(EventValue.are_you_sure)
        elif event_for_change is not None:
            event_limit=await orm_count_users(session,event_for_change.id)
            number_of_limit=int(message.text)
            if number_of_limit < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            elif number_of_limit < event_limit:
                await message.answer("Нельзя вводить лимит меньше того что есть")
            else:
                await state.update_data(event_limit=number_of_limit)
                data = await state.get_data()
                await send_event(message=message,event=data)
                await message.answer("Вы довольны?",reply_markup=yes_no_kb)
                await state.set_state(EventValue.are_you_sure)
        else:
            number_of_limit=int(message.text)
            if number_of_limit < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            else:
                await state.update_data(event_limit=number_of_limit)
                data = await state.get_data()
                await send_event(message=message,event=data)
                await message.answer("Вы довольны?",reply_markup=yes_no_kb)
                await state.set_state(EventValue.are_you_sure)
    except ValueError:
        await message.answer("Было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")

@admin_private_router.message(EventValue.are_you_sure,or_f(F.text.casefold()=="да",F.text.casefold()=="нет"))
async def are_you_sure_event(message: types.Message,state: FSMContext,session: AsyncSession):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="да" and event_for_change is not None:
        data = await state.get_data()
        await orm_update_event(session,data)
        await message.answer("Обновление совершено",reply_markup=admin_reply_keyboard)
        await state.clear()
    elif message.text.casefold()=="да":
        data = await state.get_data()
        await orm_add_event(session,data)
        await message.answer("Запись добавлена",reply_markup=admin_reply_keyboard)
        await state.clear()
    else:
        await message.answer("Запись/изменение не добавлено",reply_markup=admin_reply_keyboard)
        await state.clear()

@admin_private_router.message(EventValue.are_you_sure,F.text)
async def are_you_sure_event_duplicate(message: types.Message,state: FSMContext):
    await message.answer("Выберите один из двух вариантов")
