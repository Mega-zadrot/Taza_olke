from datetime import date, datetime
from aiogram import types, Router,Bot
from aiogram.filters import Command,StateFilter,or_f
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
#modules
from custom_filters.router_filters import TypeCheck
from database.queries import (
    orm_add_user,
    orm_delete_user,
    orm_read_user,
    orm_update_user,
    orm_read_events,
    orm_register,
    orm_read_event_name,
    orm_users_past_events,
    orm_read_association,
    orm_users_future_events,
    orm_deregister,
    orm_read_event_limit,
    orm_count_users,
    orm_read_event_state,
    orm_read_event_age_limit
    )
from kbds.reply import update_fsm_keyboard,fsm_keyboard,yes_no_kb,account_keyboard,get_reply_keyboard,update_contact_markup,contact_markup
from kbds.inline import get_inline_keyboard
from utils.render import render_user,render_event,render_my_event
from utils.time import calculate_age

user_private_router=Router()
user_private_router.message.filter(TypeCheck(["private"]))

class UserValue(StatesGroup):
    user_name=State()
    user_surname=State()
    user_fname=State()
    user_date=State()
    user_number=State()
    are_you_sure=State()
    texts={
        "UserValue:user_name":"введите ваше имя",
        "UserValue:user_surname":"введите вашу фамилию",
        "UserValue:user_fname":"введите ваше отчество",
        "UserValue:user_date":"введите дату рождения в формате yyyy-mm-dd",
        "UserValue:user_number":"нажмите 'поделиться номером' "
        }
    list_of_states=[user_name,user_surname,user_fname,user_date,user_number,are_you_sure]

#start command
@user_private_router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать!\nЗдесь вы сможете записаться на акцию и зарабатывать баллы которые можно будет в дальнейшем обменять а также цифровое потверждение того что вы и вправду участвовали.\nПомимо этого вы будете получать уведомления за день до акции (в 00:00) и при отмене события.\nВыберите '/help' чтобы узнать побольше",reply_markup=get_reply_keyboard("/help"))

#help command
@user_private_router.message(Command("help"))
async def help_cmd(message:types.Message):
    await message.answer("'/my_account' сверить текущие сведения аккаунта и узнать текущий баланс\n'/create_account' создать аккаунт\n'/delete_account' удалить аккаунт\n'/change_account' изменить сведения об аккаунте\n'/my_past_events' получить список акций в которых вы успели принять участие\n'/my_future_events' увидеть ваши заявки\n'/events' акции доступные для регистрации")

#see upcoming events
@user_private_router.message(Command("events"))
async def events_cmd(message: types.Message,session: AsyncSession):
    events= await orm_read_events(session)
    if not events:
        await message.answer("нет событий")
    else:
        for event in events:
            user_num=await orm_count_users(session,event.id)
            await message.answer(
                render_event(event,user_num),
                reply_markup=get_inline_keyboard(
                    data={"зарегистрироваться✅":f"register_{event.id}"}))
        await message.answer("вот список событий")

#register
@user_private_router.callback_query(StateFilter(None),F.data.startswith("register_"))
async def register_event(callback: types.CallbackQuery,session: AsyncSession):
    user_id = callback.from_user.id
    event_id = int(callback.data.split("_")[-1])

    user = await orm_read_user(session, user_id)
    already_registered = await orm_read_association(session, user_id, event_id)
    limit = await orm_read_event_limit(session, event_id)
    registered_count = await orm_count_users(session, event_id)
    event_state = await orm_read_event_state(session, event_id)
    age_limit = await orm_read_event_age_limit(session, event_id)
    event_name = await orm_read_event_name(session, event_id)

    # Проверка на существование
    if event_state is None:
        return await callback.message.answer("событие было удалено")
    
    #Проверка на статус
    if not event_state:
        return await callback.message.answer("событие было отменено")

    # Проверка пользователя
    if user is None:
        return await callback.message.answer("у вас нет аккаунта. Пожалуйста зарегистрируйтесь",
                                             reply_markup=get_reply_keyboard("создать аккаунт"))
    #Проверка на регистрацию
    if already_registered:
        return await callback.message.answer("вы уже зарегистрированы")

    # Проверка возраста
    user_age = calculate_age(user.birth_date) if user.birth_date else None
    if age_limit is not None and (user_age is None or user_age < age_limit):
        return await callback.message.answer("вы не подходите по возрасту")

    # Проверка лимита
    if limit is not None and registered_count >= limit:
        return await callback.message.answer("нет мест")

    # Регистрация
    await orm_register(session, user_id, event_id)
    return await callback.message.answer(f"вы зарегистрировались на {event_name.lower()}")

#deregister
@user_private_router.callback_query(StateFilter(None),F.data.startswith("deregister_"))
async def deregister_event(callback: types.CallbackQuery,session: AsyncSession):
    user_id=callback.from_user.id
    event_id=int(callback.data.split("_")[-1])
    already_registered=await orm_read_association(session,user_id,event_id)
    if already_registered is not None:
        await orm_deregister(session,user_id,event_id)
        await callback.message.answer("заявка отозвана")
    else:
        await callback.message.answer("заявка уже отозвана")

#my past events
@user_private_router.message(Command("my_past_events"))
async def my_past_events_cmd(message: types.Message,session: AsyncSession):
    user_id=message.from_user.id
    rows=await orm_users_past_events(session,user_id)
    if not rows:
        await message.answer("здесь нет ничего")
    else:
        for event, was_there in rows:
            await message.answer(render_my_event(event,was_there))

#my future events
@user_private_router.message(Command("my_future_events"))
async def my_future_events_cmd(message: types.Message,session: AsyncSession):
    user_id=message.from_user.id
    rows=await orm_users_future_events(session,user_id)
    if not rows:
        await message.answer("здесь нет ничего")
    else:
        for event, was_there in rows:
            await message.answer(render_my_event(event,was_there),
                reply_markup=get_inline_keyboard(
                    data={"отозвать❌":f"deregister_{event.id}"}))

#my account
@user_private_router.message(StateFilter(None),Command("my_account"))
@user_private_router.message(StateFilter(None),F.text=="мой аккаунт")
async def my_user(message: types.Message,session: AsyncSession):
    user=await orm_read_user(session,message.from_user.id)
    if user is None:
        await message.answer(render_user(user),reply_markup=get_reply_keyboard("создать аккаунт"))
    else:
        await message.answer(render_user(user),reply_markup=account_keyboard)

#delete account
@user_private_router.message(StateFilter(None),Command("delete_account"))
@user_private_router.message(StateFilter(None),F.text=="удалить аккаунт")
async def delete_user(message: types.Message,session: AsyncSession, state: FSMContext):
    await message.answer("Вы точно уверены? Все ваши достижения стерутся при этом",reply_markup=get_reply_keyboard("да","нет"))
    await state.set_state(UserValue.are_you_sure)
    await state.update_data(user_for_delete=True)

#update info
@user_private_router.message(StateFilter(None),Command("change_account"))
@user_private_router.message(StateFilter(None),F.text=="изменить сведения")
async def change_user(message: types.Message,state: FSMContext,session: AsyncSession):
    user_id=int(message.from_user.id)
    user_for_change=await orm_read_user(session,user_id)
    if user_for_change:
        await state.update_data(user_for_change = user_for_change)
        await message.answer("введите новое имя",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_name)
        await state.update_data(user_id=user_id)
    else:
        await message.answer("нечего обновлять")

#user FSM
@user_private_router.message(StateFilter(None),Command("create_account"))
@user_private_router.message(StateFilter(None),F.text=="создать аккаунт")
async def create_user(message: types.Message,state: FSMContext,session: AsyncSession):
    result=await orm_read_user(session,message.from_user.id)
    if result:
        await message.answer("у вас уже есть аккаунт")
    else:
        await message.answer(
            "Введите ваше имя (не больше 150 символов и отвечайте только текстом на все в противном случае бот не будет вам отвечать)",
            reply_markup=fsm_keyboard)
        await state.set_state(UserValue.user_name)
        await state.update_data(user_id=message.from_user.id)

#cancel actions
@user_private_router.message(StateFilter(*UserValue.list_of_states),F.text=="отмена")
async def ucancel(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer("все было отменено",reply_markup=types.ReplyKeyboardRemove())

#step backwards
@user_private_router.message(StateFilter(*UserValue.list_of_states),F.text=="шаг назад")
async def ustep_backwards(message: types.Message,state: FSMContext):
    current_state=await state.get_state()
    data=await state.get_data()
    user_for_change=data.get("user_for_change") 
    if current_state==UserValue.user_name:
        await message.answer("назад некуда идти")
        return
    elif current_state==UserValue.are_you_sure and user_for_change is not None:
        await state.set_state(UserValue.user_number)
        await message.answer(f"ок вы вернулись на шаг назад \n{UserValue.texts["UserValue:user_number"]}",reply_markup=update_contact_markup)
    elif current_state==UserValue.are_you_sure:
        await state.set_state(UserValue.user_number)
        await message.answer(f"ок вы вернулись на шаг назад \n{UserValue.texts["UserValue:user_number"]}",reply_markup=contact_markup)
    elif user_for_change is not None:
        previous=None
        for step in UserValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"ок вы вернулись на шаг назад \n{UserValue.texts[previous.state]}",reply_markup=update_fsm_keyboard)
            else:
                previous=step
    else:
        previous=None
        for step in UserValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"ок вы вернулись на шаг назад \n{UserValue.texts[previous.state]}",reply_markup=fsm_keyboard)
            else:
                previous=step

@user_private_router.message(UserValue.user_name,F.text)
async def creat_use(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_name=user_for_change.name)
        await message.answer("ок оставляем это имя, теперь отправь новую фамилию",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_surname)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_name=message.text.capitalize())
            await message.answer("теперь отправь свою фамилию")
            await state.set_state(UserValue.user_surname)
        else:
            await message.answer("имя превысило 150 символов,повтори на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_surname,F.text)
async def creat_us(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_surname=user_for_change.surname)
        await message.answer("ок оставляем эту фамилию, теперь отправь новое отчество",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_fname)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_surname=message.text.capitalize())
            await message.answer("теперь отправь свое отчество")
            await state.set_state(UserValue.user_fname)
        else:
            await message.answer("фамилия превысила 150 символов,повтори на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_fname,F.text)
async def creat_u(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_fname=user_for_change.fathers_name)
        await message.answer("ок оставляем это отчество, теперь отправь новую дату рождения",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_date)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_fname=message.text.capitalize())
            await message.answer("теперь отправь свою дату рождения в таком формате yyyy-mm-dd")
            await state.set_state(UserValue.user_date)
        else:
            await message.answer("отчество превысила 150 символов,повтори на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_date,F.text)
async def cr_user(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        user_for_change=data.get("user_for_change")
        if message.text.casefold()=="пропустить" and user_for_change is not None:
            await state.update_data(user_date=user_for_change.birth_date)
            await message.answer("ок оставляем эту дату, теперь отправь новый номер телефона через кнопку",reply_markup=update_contact_markup)
            await state.set_state(UserValue.user_number)
        else:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate < date.today():
                await state.update_data(user_date=edate)
                await message.answer("теперь отправь номер телефона через кнопку",reply_markup=contact_markup)
                await state.set_state(UserValue.user_number)
            else:
                await message.answer("дата не может быть в будущем времени,повторите пожалуйста")
    except ValueError:
        await message.answer("было введена дата не в том формате, повторите еще раз(без точек,запятых,пробелов только цифры и -)")

@user_private_router.message(UserValue.user_number,F.contact)
async def get_phone_number(message: types.Message,state: FSMContext):
    await state.update_data(user_number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(render_user(data))
    await message.answer("вы довольны?",reply_markup=yes_no_kb)
    await state.set_state(UserValue.are_you_sure)
    
@user_private_router.message(UserValue.user_number,F.text)
async def get_phone_number2(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_number=user_for_change.phone_number)
        await message.answer("ок оставляем этот номер телефона")
        data = await state.get_data()
        await message.answer(render_user(data))
        await message.answer("вы довольны?",reply_markup=yes_no_kb)
        await state.set_state(UserValue.are_you_sure)
    else:
        await message.answer("воспользуйтесь кнопкой")

@user_private_router.message(UserValue.are_you_sure,or_f(F.text=="да",F.text=="нет"))
async def are_you_sure_user(message: types.Message,state: FSMContext,session: AsyncSession):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    user_for_delete=data.get("user_for_delete")
    if message.text=="да" and user_for_change:
        data = await state.get_data()
        await orm_update_user(session,data)
        await message.answer("обновление совершено",reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    elif message.text=="да" and user_for_delete:
        result=await orm_read_user(session,message.from_user.id)
        if result:
            await orm_delete_user(session,message.from_user.id)
            await message.answer("ваш аккаунт был удален",reply_markup=types.ReplyKeyboardRemove())
            return
        else:
            await message.answer("нечего удалять",reply_markup=types.ReplyKeyboardRemove())
            return
    elif message.text=="да":
        data = await state.get_data()
        await orm_add_user(session,data)
        await message.answer("запись добавлена",reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    else:
        await message.answer("запись/изменение/удаление не совершенно",reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

@user_private_router.message(UserValue.are_you_sure,F.text)
async def are_you_sure_user_duplicate(message: types.Message,state: FSMContext):
    await message.answer("выбери один из двух вариантов")