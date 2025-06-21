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
from kbds.reply import admin_reply_keyboard,update_fsm_keyboard,fsm_keyboard,yes_no_kb,fsm_keyboard_age_limit,update_fsm_keyboard_age_limit
from database.queries import (
orm_read_events,
orm_add_event,
orm_delete_event,
orm_read_event_name,
orm_read_event,
orm_update_event,
orm_count_users,
orm_user_list,
orm_read_past_events,
orm_read_association,
orm_update_balance,
orm_update_status,
orm_cancel_event,
orm_read_event_point
)
from utils.render import render_event,render_user

admin_private_router=Router()

admin_private_router.message.filter(TypeCheck(["private"]),IsAdmin())

#fsm class
class EventValue(StatesGroup):
    event_name=State()
    event_point=State()
    event_description=State()
    event_date=State()
    event_age=State()
    event_limit=State()
    are_you_sure=State()
    texts={
        "EventValue:event_name":"введите имя",
        "EventValue:event_point":"введите число баллов",
        "EventValue:event_description":"введите описание",
        "EventValue:event_date":"введите дату в формате yyyy-mm-dd",
        "EventValue:event_limit":"введите число желаемых участников",
        "EventValue:event_age":"введите минимальный возраст"
        }
    
    list_of_states=[
        event_name,
        event_point,
        event_description,
        event_date,
        event_age,
        event_limit,
        are_you_sure
    ]

#Menu
@admin_private_router.message(Command("admin"))
async def check_priveliegies(message: types.Message):
    await message.answer("Приветствую вас админ! Что пожелаете сделать?",reply_markup=admin_reply_keyboard)

#select
@admin_private_router.message(F.text=="просмотреть будущие события")
async def read_events(message: types.Message,session: AsyncSession):
    events= await orm_read_events(session)
    if not events:
        await message.answer("нет событий")
    else:
        for event in events:
            user_num=await orm_count_users(session,event.id)
            await message.answer(
                render_event(event,user_num),
                reply_markup=get_inline_keyboard(
                    data={"удалить":f"edelete_{event.id}",
                          "изменить":f"eupdate_{event.id}",
                          "отменить":f"cancel_{event.id}",
                          "список":f"list_{event.id}"
                          }))
        await message.answer("вот список событий")

#select past events
@admin_private_router.message(F.text=="просмотреть прошедшие события")
async def read_past_events(message: types.Message,session: AsyncSession):
    events= await orm_read_past_events(session)
    if not events:
        await message.answer("нет событий")
    else:
        for event in events:
            user_num=await orm_count_users(session,event.id)
            await message.answer(
                render_event(event,user_num),
                reply_markup=get_inline_keyboard(
                    data={
                          "список для подтверждения":f"list_{event.id}"
                          }))
        await message.answer("вот список событий")

#delete
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("edelete_"))
async def delete_event(callback: types.CallbackQuery,session: AsyncSession):
    event_id=int(callback.data.split("_")[-1])
    event_name=await orm_read_event_name(session,event_id)
    if event_name is not None:
        await orm_delete_event(session,event_id)
        await callback.message.answer(f"событие {event_name.lower()} было удалено")
        await callback.answer("событие удалено")
    else:
        await callback.message.answer("уже удалено")
#update
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("eupdate_"))
async def update_event(callback: types.CallbackQuery,session: AsyncSession,state: FSMContext):
    event_id=int(callback.data.split("_")[-1])
    event_for_change=await orm_read_event(session,event_id)
    if event_for_change is not None:
        await state.update_data(event_for_change = event_for_change)
        await callback.answer()
        await callback.message.answer("введите новое название события",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_name)
        await state.update_data(id=event_id)
    else:
        await callback.message.answer("событие было удалено")

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
                        "присуствовал":f"confirm_yes_{user.user_id}_{event_id}",
                        "не присуствовал":f"confirm_no_{user.user_id}_{event_id}"
                    }))
                await callback.message.answer("список юзеров")
            elif event.event_date > date.today():
                for user in users:
                    await callback.message.answer(render_user(user))
                await callback.message.answer("список юзеров")
        else:
            await callback.message.answer("никто еще не успел зарегистрироваться")
    else:
        await callback.message.answer("событие было удалено")

#cancel
@admin_private_router.callback_query(StateFilter(None),F.data.startswith("cancel_"))
async def cancel_event(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    event_id=int(callback.data.split("_")[-1])
    event_name=await orm_read_event_name(session,event_id)
    users=await orm_user_list(session,event_id)
    if event_name is not None and users:
        await orm_cancel_event(session,event_id)
        for user in users:
            await bot.send_message(chat_id=user.user_id,text=f"событие {event_name.lower()} на которое вы зарегистрировались было отменено")
        await callback.message.answer("событие было отменено(есть юзеры)")
    elif event_name is not None and not users:
        await callback.message.answer("событие было отменено(нет юзеров)")
    else:
        await callback.message.answer("событие было удалено")

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
            await callback.message.answer("уже подтверждено присуствие этого пользователя")
        elif status=="yes":
            await orm_update_status(session,association,True)
            await orm_update_balance(session,user_id,event_point)
            await callback.message.answer("подтверждено присуствие этого пользователя")
# if was there False change to True + points if True dont do anything (send message) if None change to True + points
        elif status=="no" and association.was_there==False:
            await callback.message.answer("уже подтверждено отсуствие этого пользователя")
        elif status=="no" and association.was_there==True:
            await orm_update_status(session,association,False)
            await orm_update_balance(session,user_id,-event_point)
            await callback.message.answer("подтверждено отсуствие этого пользователя")
        elif status=="no" and association.was_there==None:
            await orm_update_status(session,association,False)
            await callback.message.answer("подтверждено отсуствие этого пользователя")
    else:
        await callback.message.answer("либо пользователь удалил свой аккаунт либо событие было удалено")
# if was there False dont do anything(send message) if None change to False only if True change to false minus points

#FSM for creation and update
@admin_private_router.message(StateFilter(None),F.text=="создать событие")
async def create_event(message: types.Message,state: FSMContext):
    await message.answer(
        "Введите имя события(не больше 200 символов(на имя) и отвечайте только текстом на все в противном случае бот не будет вам отвечать)",
        reply_markup=fsm_keyboard)
    await state.set_state(EventValue.event_name)
    
#cancel fsm
@admin_private_router.message(StateFilter(*EventValue.list_of_states),F.text=="отмена")
async def admin_cancel(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer("все было отменено",reply_markup=admin_reply_keyboard)

#step backwards
@admin_private_router.message(StateFilter(*EventValue.list_of_states),F.text=="шаг назад")
async def admin_step_backwards(message: types.Message,state: FSMContext):
    current_state=await state.get_state()
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if current_state ==EventValue.event_name:
        await message.answer("назад некуда идти")
        return
    elif current_state==EventValue.are_you_sure and event_for_change is not None:
        await state.set_state(EventValue.event_limit)
        await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_limit"]}",reply_markup=update_fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.are_you_sure:
        await state.set_state(EventValue.event_limit)
        await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_limit"]}",reply_markup=fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.event_limit and event_for_change is not None:
        await state.set_state(EventValue.event_age)
        await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_age"]}",reply_markup=update_fsm_keyboard_age_limit)
        return
    elif current_state==EventValue.event_limit:
        await state.set_state(EventValue.event_age)
        await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts["EventValue:event_age"]}",reply_markup=fsm_keyboard_age_limit)
        return
    elif event_for_change is not None:
        previous=None
        for step in EventValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts[previous.state]}",reply_markup=update_fsm_keyboard)
            else:
                previous=step
    else:
        previous=None
        for step in EventValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"ок вы вернулись на шаг назад \n{EventValue.texts[previous.state]}",reply_markup=fsm_keyboard)
            else:
                previous=step


@admin_private_router.message(EventValue.event_name,F.text)
async def creat_event(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_name=event_for_change.name)
        await message.answer("ок оставляем это имя, теперь отправь новое количество баллов за это событие",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_point)
    else:   
        if len(message.text) <= 200:
            await state.update_data(event_name=message.text)
            await message.answer("теперь отправь количество баллов за это событие")
            await state.set_state(EventValue.event_point)
        else:
            await message.answer("имя превысило 200 символов,повтори на этот раз с меньшим количеством")

@admin_private_router.message(EventValue.event_point,F.text)
async def crea_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold() =="пропустить" and event_for_change is not None:
            await state.update_data(event_point=event_for_change.point)
            await message.answer("ок оставляем это количество, теперь отправь новое описание",reply_markup=update_fsm_keyboard)
            await state.set_state(EventValue.event_description)
        else:
            number_of_points=int(message.text)
            if number_of_points < 0:
                await message.answer("нельзя вводить отрицательные числа")
            else:
                await state.update_data(event_point=number_of_points)
                await message.answer("теперь отправь описание")
                await state.set_state(EventValue.event_description)
    except ValueError:
            await message.answer("было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")    

@admin_private_router.message(EventValue.event_description,F.text)
async def cre_event(message: types.Message,state: FSMContext):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text.casefold()=="пропустить" and event_for_change is not None:
        await state.update_data(event_description=event_for_change.description)
        await message.answer("ок оставляем это описание, теперь отправь новую дату",reply_markup=update_fsm_keyboard)
        await state.set_state(EventValue.event_date)
    else:  
        await state.update_data(event_description=message.text)
        await message.answer("теперь отправь дату в таком формате yyyy-mm-dd")
        await state.set_state(EventValue.event_date)

@admin_private_router.message(EventValue.event_date,F.text)
async def cr_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_date=event_for_change.event_date)
            await message.answer("ок оставляем эту дату, теперь отправь новый минимальный возраст участия",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_age)
            return
        elif event_for_change is not None:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate >= date.today():
                await state.update_data(event_date=edate)
                await message.answer("теперь отправь минимальный возраст участия",reply_markup=update_fsm_keyboard_age_limit)
                await state.set_state(EventValue.event_age)
            else:
                await message.answer("дата не может быть в прошлом времени,повтори пожалуйста")
        else:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate >= date.today():
                await state.update_data(event_date=edate)
                await message.answer("теперь отправь минимальный возраст участия",reply_markup=fsm_keyboard_age_limit)
                await state.set_state(EventValue.event_age)
            else:
                await message.answer("дата не может быть в прошлом времени,повтори пожалуйста")
    except ValueError:
        await message.answer("было введена дата не в том формате, повторите еще раз(без точек,запятых,пробелов только цифры и -)")

@admin_private_router.message(EventValue.event_age,F.text)
async def crea_event(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_age=event_for_change.required_age)
            await message.answer("ок оставляем этот минимальный возраст, теперь отправь новое число участников",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
            return
        elif message.text.casefold()=="без ограничения" and event_for_change is not None:
            await state.update_data(event_age=None)
            await message.answer("теперь отправь количество участников",reply_markup=update_fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
        elif message.text.casefold()=="без ограничения":
            await state.update_data(event_age=None)
            await message.answer("теперь отправь количество участников",reply_markup=fsm_keyboard_age_limit)
            await state.set_state(EventValue.event_limit)
        elif event_for_change is not None:
            age=int(message.text)
            if age < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            elif age > event_for_change.required_age:
                await message.answer("Нельзя вводить возраст меньше того что есть")
            else:
                await state.update_data(event_age=age)
                await message.answer("теперь отправь количество участников")
                await state.set_state(EventValue.event_limit)
        else:
            age=int(message.text)
            if age < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            else:
                await state.update_data(event_age=age)
                await message.answer("теперь отправь количество участников")
                await state.set_state(EventValue.event_limit)
    except ValueError:
            await message.answer("было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")    

@admin_private_router.message(EventValue.event_limit,F.text)
async def c_event(message: types.Message,state: FSMContext,session: AsyncSession):
    try:
        data=await state.get_data()
        event_for_change=data.get("event_for_change")
        if message.text.casefold()=="пропустить" and event_for_change is not None:
            await state.update_data(event_limit=event_for_change.limit)
            await message.answer("ок оставляем этот лимит")
            data = await state.get_data()
            await message.answer(render_event(data))
            await message.answer("вы довольны?",reply_markup=yes_no_kb)
            await state.set_state(EventValue.are_you_sure)
        elif message.text.casefold()=="без ограничения":
                await state.update_data(event_limit=None)
                data = await state.get_data()
                await message.answer(render_event(data))
                await message.answer("вы довольны?",reply_markup=yes_no_kb)
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
                await message.answer(render_event(data))
                await message.answer("вы довольны?",reply_markup=yes_no_kb)
                await state.set_state(EventValue.are_you_sure)
        else:
            number_of_limit=int(message.text)
            if number_of_limit < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            else:
                await state.update_data(event_limit=number_of_limit)
                data = await state.get_data()
                await message.answer(render_event(data))
                await message.answer("вы довольны?",reply_markup=yes_no_kb)
                await state.set_state(EventValue.are_you_sure)
    except ValueError:
        await message.answer("было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")

@admin_private_router.message(EventValue.are_you_sure,or_f(F.text=="да",F.text=="нет"))
async def are_you_sure_event(message: types.Message,state: FSMContext,session: AsyncSession):
    data=await state.get_data()
    event_for_change=data.get("event_for_change")
    if message.text=="да" and event_for_change is not None:
        data = await state.get_data()
        await orm_update_event(session,data)
        await message.answer("обновление совершено",reply_markup=admin_reply_keyboard)
        await state.clear()
    elif message.text=="да":
        data = await state.get_data()
        await orm_add_event(session,data)
        await message.answer("запись добавлена",reply_markup=admin_reply_keyboard)
        await state.clear()
    else:
        await message.answer("запись/изменение не добавлена",reply_markup=admin_reply_keyboard)
        await state.clear()

@admin_private_router.message(EventValue.are_you_sure,F.text)
async def are_you_sure_event_duplicate(message: types.Message,state: FSMContext):
    await message.answer("выбери один из двух вариантов")
