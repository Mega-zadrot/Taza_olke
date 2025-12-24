from datetime import date, datetime
from aiogram import types, Router, Bot
from aiogram.filters import Command,StateFilter,or_f
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
#modules
from custom_filters.router_filters import TypeCheck
from database.queries import (
    orm_add_user,
    orm_delete_user,
    orm_read_user,
    orm_update_user,
    orm_read_events_user,
    orm_register,
    orm_read_event_name,
    orm_users_past_events,
    orm_read_association,
    orm_users_future_events,
    orm_deregister,
    orm_read_event_limit,
    orm_count_users,
    orm_read_event_state,
    orm_read_event_age_limit,
    orm_read_search_events,
    orm_add_request,
    orm_update_request,
    orm_read_my_active_requests,
    orm_delete_request,
    orm_read_request,
    orm_read_my_past_requests,
    orm_read_report
    )
from kbds.reply import (
    update_fsm_keyboard,
    fsm_keyboard,
    yes_no_kb,
    account_keyboard,
    get_reply_keyboard,
    update_contact_markup,
    contact_markup,
    search_fsm_kb,
    search_age_fsm_kb,
    request_keyboard,
    request_update_keyboard,
    request_yes_no_kb,
    request_keyboard_album,
    request_keyboard_album_update,
    re_contact_markup,
    re_update_contact_markup,
    user_reply_keyboard
    )
from kbds.inline import get_inline_keyboard
from utils.render import render_user
from utils.time import calculate_age
from utils.bonus import parse_price_for_postgres
from media.album import send_event,send_request,send_report,send_events

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
        "UserValue:user_name":"Введите ваше имя",
        "UserValue:user_surname":"Введите вашу фамилию",
        "UserValue:user_fname":"Введите ваше отчество",
        "UserValue:user_date":"Введите дату рождения в формате yyyy-mm-dd",
        "UserValue:user_number":"Нажмите 'поделиться номером' "
        }
    list_of_states=[user_name,user_surname,user_fname,user_date,user_number,are_you_sure]

class SearchValue(StatesGroup):
    search_city=State()
    search_req_age=State()
    search_date=State()
    search_name=State()
    search_point=State()
    list_of_states=[search_city,search_name,search_req_age,search_date,search_point]

class RequestValue(StatesGroup):
    request_album=State()
    request_address=State()
    request_name=State()
    request_description=State()
    request_phone_number=State()
    are_you_sure=State()
    list_of_states=[request_album,request_address,request_name,request_description,request_phone_number,are_you_sure]

#start command
@user_private_router.message(StateFilter(None),Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать!\nЗдесь вы сможете записаться на акцию или подать заявку о неполадках на улицах Косшы.\nВведите '/help' чтобы узнать побольше",reply_markup=get_reply_keyboard("/help"))

#help command
@user_private_router.message(StateFilter(None),F.text.casefold()=="помощь")
@user_private_router.message(StateFilter(None),Command("help"))
async def help_cmd(message:types.Message):
    await message.answer("'Мой аккаунт' сверить текущие сведения аккаунта и узнать текущий баланс\n'Создать заявку' создать заявку о неполадках или неисправностях в работе служб города Косшы\n'Мои активные заявки' посмотреть список ваших заявок которые рассматриваются/в ожидании\n'Мои неактивные заявки' посмотреть список ваших заявок которые отклонены/обработаны\n'Мои прошедшие акции' получить список акций в которых вы успели принять участие\n'Мои грядущие акции' получить список акций на которые вы зарегистрировались\n'Грядущие акции' акции доступные для регистрации\n'Искать акции' искать акции по критериям",reply_markup=user_reply_keyboard)
#see upcoming events
@user_private_router.message(StateFilter(None),Command("events"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="грядущие акции")
async def events_cmd(message: types.Message,session: AsyncSession):
    events= await orm_read_events_user(session)
    if not events:
        await message.answer("Нет событий",reply_markup=user_reply_keyboard)
    else:
        await send_events(events,message,session)

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
        return await callback.message.answer("Событие было удалено",reply_markup=user_reply_keyboard)
    
    #Проверка на статус
    if not event_state:
        return await callback.message.answer("Событие было отменено",reply_markup=user_reply_keyboard)

    # Проверка пользователя
    if user is None:
        return await callback.message.answer("У вас нет аккаунта. Пожалуйста зарегистрируйтесь",
                                             reply_markup=get_reply_keyboard("Создать аккаунт"))
    #Проверка на регистрацию
    if already_registered:
        return await callback.message.answer("Вы уже зарегистрированы",reply_markup=user_reply_keyboard)

    # Проверка возраста
    user_age = calculate_age(user.birth_date) if user.birth_date else None
    if age_limit is not None and (user_age is None or user_age < age_limit):
        return await callback.message.answer("Вы не подходите по возрасту",reply_markup=user_reply_keyboard)

    # Проверка лимита
    if limit is not None and registered_count >= limit:
        return await callback.message.answer("Нет мест",reply_markup=user_reply_keyboard)

    # Регистрация
    await orm_register(session, user_id, event_id)
    return await callback.message.answer(f"Вы зарегистрировались на {event_name.casefold()}",reply_markup=user_reply_keyboard)

#deregister
@user_private_router.callback_query(StateFilter(None),F.data.startswith("deregister_"))
async def deregister_event(callback: types.CallbackQuery,session: AsyncSession):
    user_id=callback.from_user.id
    event_id=int(callback.data.split("_")[-1])
    already_registered=await orm_read_association(session,user_id,event_id)
    if already_registered is not None:
        await orm_deregister(session,user_id,event_id)
        await callback.message.answer("Заявка отозвана",reply_markup=user_reply_keyboard)
    else:
        await callback.message.answer("Заявка уже отозвана",reply_markup=user_reply_keyboard)

#my past events
@user_private_router.message(StateFilter(None),F.text.casefold()=="мои прошедшие акции")
@user_private_router.message(StateFilter(None),Command("my_past_events"))
async def my_past_events_cmd(message: types.Message,session: AsyncSession):
    user_id=message.from_user.id
    rows=await orm_users_past_events(session,user_id)
    if not rows:
        await message.answer("Здесь нет ничего",reply_markup=user_reply_keyboard)
    else:
        for event, was_there in rows:
            await send_event(event=event,state=was_there,message=message)
        await message.answer("Вот список ваших посещеных акций",reply_markup=user_reply_keyboard)

#my future events
@user_private_router.message(StateFilter(None),F.text.casefold()=="мои грядущие акции")
@user_private_router.message(StateFilter(None),Command("my_future_events"))
async def my_future_events_cmd(message: types.Message,session: AsyncSession):
    user_id=message.from_user.id
    rows=await orm_users_future_events(session,user_id)
    if not rows:
        await message.answer("Здесь нет ничего",reply_markup=user_reply_keyboard)
    else:
        for event, was_there in rows:
            await send_event(message=message,event=event,state=was_there)
            await message.answer(
                f"Действия с {event.name.casefold()}",
                reply_markup=get_inline_keyboard(
                    data={"Отозвать❌":f"deregister_{event.id}"}))
        await message.answer("Вот список ваших активных регистраций",reply_markup=user_reply_keyboard)

#my account
@user_private_router.message(StateFilter(None),Command("my_account"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="мой аккаунт")
async def my_user(message: types.Message,session: AsyncSession):
    user=await orm_read_user(session,message.from_user.id)
    if user is None:
        await message.answer(render_user(user),reply_markup=get_reply_keyboard("Создать аккаунт"))
    else:
        await message.answer(render_user(user),reply_markup=account_keyboard)

#delete account
@user_private_router.message(StateFilter(None),Command("delete_account"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="удалить аккаунт")
async def delete_user(message: types.Message,session: AsyncSession, state: FSMContext):
    await message.answer("Вы точно уверены? Все ваши достижения стерутся при этом",reply_markup=get_reply_keyboard("да","нет"))
    await state.set_state(UserValue.are_you_sure)
    await state.update_data(user_for_delete=True)

#update info
@user_private_router.message(StateFilter(None),Command("change_account"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="изменить сведения")
async def change_user(message: types.Message,state: FSMContext,session: AsyncSession):
    user_id=int(message.from_user.id)
    user_for_change=await orm_read_user(session,user_id)
    if user_for_change:
        await state.update_data(user_for_change = user_for_change)
        await message.answer("Введите новое имя",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_name)
        await state.update_data(user_id=user_id)
    else:
        await message.answer("Нечего обновлять",reply_markup=user_reply_keyboard)

#read my active requests
@user_private_router.message(StateFilter(None),Command("read_my_current_requests"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="мои активные заявки")
async def read_my_active_requests(message: types.Message,session: AsyncSession):
    requests = await orm_read_my_active_requests(session,message.from_user.id)
    if not requests:
        await message.answer("Нет заявок",reply_markup=user_reply_keyboard)
    else:
        for request in requests:
            await send_request(
                message=message,
                request=request)
            await message.answer(
                f"Действия с {request.name.casefold()}",
                reply_markup=get_inline_keyboard(
                    data={"Удалить❌":f"rdelete_{request.id}",
                          "Изменить🔁":f"rupdate_{request.id}"
                          }))
        await message.answer("Вот список ваших активных заявок",reply_markup=user_reply_keyboard)

#read my past requests
@user_private_router.message(StateFilter(None),Command("read_my_past_requests"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="мои неактивные заявки")
async def read_my_past_requests(message: types.Message,session: AsyncSession):
    requests = await orm_read_my_past_requests(session,message.from_user.id)
    if not requests:
        await message.answer("Нет заявок")
    else:
        for request in requests:
            await send_request(
                message=message,
                request=request)
            if request.status=="Обработано":
                await message.answer(
                f"Действия с {request.name.casefold()}",
                reply_markup=get_inline_keyboard(data={"отчет📄":f"get_report_{request.id}"}))
            elif request.status=="Отклонено":
                await message.answer(
                f"Действия с {request.name.casefold()}",
                reply_markup=get_inline_keyboard(data={"комментарий💬":f"get_comment_{request.id}"}))
        await message.answer("Вот список ваших неактивных заявок",reply_markup=user_reply_keyboard)

#delete request
@user_private_router.callback_query(StateFilter(None),F.data.startswith("rdelete_"))
async def delete_request(callback: types.CallbackQuery,session: AsyncSession):
    request_id=int(callback.data.split("_")[-1])
    request = await orm_read_request(session,request_id)
    if request is not None and request.status=="В ожидании":
        await orm_delete_request(session,request_id)
        await callback.message.answer(f"Заявка {request.name.casefold()} была удалена",reply_markup=user_reply_keyboard)
        await callback.answer("Заявка удалена",reply_markup=user_reply_keyboard)
    elif request is None:
        await callback.message.answer("Уже удалена",reply_markup=user_reply_keyboard)
    else:
        await callback.message.answer("С вашей заявкой взаимодействовали/рассматривают",reply_markup=user_reply_keyboard)

#update request
@user_private_router.callback_query(StateFilter(None),F.data.startswith("rupdate_"))
async def update_request(callback: types.CallbackQuery,session: AsyncSession,state: FSMContext):
    request_id=int(callback.data.split("_")[-1])
    request_for_change=await orm_read_request(session,request_id)
    if request_for_change is not None and request_for_change.status=="В ожидании":
        await state.update_data(request_for_change = request_for_change)
        await callback.answer()
        await callback.message.answer("Введите новый тип заявки", reply_markup=request_update_keyboard)
        await state.set_state(RequestValue.request_name)
        await state.update_data(request_date=request_for_change.created_at,username=request_for_change.username,request_album=None, count=0, id=request_id)
    elif request_for_change is None:
        await callback.message.answer("Заявка была удалена")
    else:
        await callback.message.answer("С вашей заявкой взаимодействовали/рассматривают")

#get report
@user_private_router.callback_query(StateFilter(None),F.data.startswith("get_report_"))
async def get_report(callback: types.CallbackQuery,session: AsyncSession):
    request_id = int(callback.data.split("_")[-1])
    report = await orm_read_report(session,request_id)
    if report is not None:
        await send_report(report,callback.message)
        await callback.answer()
    else:
        await callback.message.answer("Заявка удалена",reply_markup=user_reply_keyboard)
        await callback.answer("Заявка удалена",reply_markup=user_reply_keyboard)

#get comment
@user_private_router.callback_query(StateFilter(None),F.data.startswith("get_comment_"))
async def get_comment(callback: types.CallbackQuery,session: AsyncSession):
    request_id=int(callback.data.split("_")[-1])
    request=await orm_read_request(session,request_id)
    if request is not None:
        await callback.message.answer(request.comment)
    else:
        await callback.message.answer("Заявка удалена",reply_markup=user_reply_keyboard)

#account FSM
@user_private_router.message(StateFilter(None),Command("create_account"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="создать аккаунт")
async def create_user(message: types.Message,state: FSMContext,session: AsyncSession):
    result=await orm_read_user(session,message.from_user.id)
    if result:
        await message.answer("У вас уже есть аккаунт",reply_markup=user_reply_keyboard)
    else:
        await message.answer(
            "Введите ваше имя (не больше 150 символов и отвечайте только текстом на все в противном случае бот не будет вам отвечать)",
            reply_markup=fsm_keyboard)
        await state.set_state(UserValue.user_name)
        await state.update_data(user_id=message.from_user.id, user_username=message.from_user.username)

#cancel actions
@user_private_router.message(StateFilter(*SearchValue.list_of_states),F.text.casefold()=="отмена")
@user_private_router.message(StateFilter(*UserValue.list_of_states),F.text.casefold()=="отмена")
@user_private_router.message(StateFilter(*RequestValue.list_of_states),F.text.casefold()=="отмена")
async def ucancel(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer("Все было отменено",reply_markup=user_reply_keyboard)

#step backwards
@user_private_router.message(StateFilter(*UserValue.list_of_states),F.text.casefold()=="шаг назад")
async def ustep_backwards(message: types.Message,state: FSMContext):
    current_state=await state.get_state()
    data=await state.get_data()
    user_for_change=data.get("user_for_change") 
    if current_state==UserValue.user_name:
        await message.answer("Назад некуда идти")
        return
    elif current_state==UserValue.are_you_sure and user_for_change is not None:
        await state.set_state(UserValue.user_number)
        await message.answer(f"Ок вы вернулись на шаг назад \n{UserValue.texts["UserValue:user_number"]}",reply_markup=update_contact_markup)
    elif current_state==UserValue.are_you_sure:
        await state.set_state(UserValue.user_number)
        await message.answer(f"Ок вы вернулись на шаг назад \n{UserValue.texts["UserValue:user_number"]}",reply_markup=contact_markup)
    elif user_for_change is not None:
        previous=None
        for step in UserValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"Ок вы вернулись на шаг назад \n{UserValue.texts[previous.state]}",reply_markup=update_fsm_keyboard)
            else:
                previous=step
    else:
        previous=None
        for step in UserValue.__all_states__:
            if step.state==current_state:
                await state.set_state(previous)
                await message.answer(f"Ок вы вернулись на шаг назад \n{UserValue.texts[previous.state]}",reply_markup=fsm_keyboard)
            else:
                previous=step
#fsm account
@user_private_router.message(UserValue.user_name,F.text)
async def user_name(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_name=user_for_change.name)
        await message.answer("Ок оставляем это имя, теперь отправьте новую фамилию",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_surname)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_name=message.text.capitalize())
            await message.answer("Теперь отправьте свою фамилию")
            await state.set_state(UserValue.user_surname)
        else:
            await message.answer("Имя превысило 150 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_surname,F.text)
async def user_surname(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_surname=user_for_change.surname)
        await message.answer("Ок оставляем эту фамилию, теперь отправьте новое отчество",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_fname)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_surname=message.text.capitalize())
            await message.answer("Теперь отправьте свое отчество")
            await state.set_state(UserValue.user_fname)
        else:
            await message.answer("Фамилия превысила 150 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_fname,F.text)
async def user_fname(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_fname=user_for_change.fathers_name)
        await message.answer("Ок оставляем это отчество, теперь отправьте новую дату рождения",reply_markup=update_fsm_keyboard)
        await state.set_state(UserValue.user_date)
    else:   
        if len(message.text) <= 150:
            await state.update_data(user_fname=message.text.capitalize())
            await message.answer("Теперь отправьте свою дату рождения в таком формате yyyy-mm-dd")
            await state.set_state(UserValue.user_date)
        else:
            await message.answer("Отчество превысила 150 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(UserValue.user_date,F.text)
async def user_birth_date(message: types.Message,state: FSMContext):
    try:
        data=await state.get_data()
        user_for_change=data.get("user_for_change")
        if message.text.casefold()=="пропустить" and user_for_change is not None:
            await state.update_data(user_date=user_for_change.birth_date)
            await message.answer("Ок оставляем эту дату, теперь отправьте новый номер телефона через кнопку",reply_markup=update_contact_markup)
            await state.set_state(UserValue.user_number)
        elif user_for_change is not None:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate < date.today():
                await state.update_data(user_date=edate)
                await message.answer("Теперь отправьте новый номер телефона через кнопку",reply_markup=update_contact_markup)
                await state.set_state(UserValue.user_number)
            else:
                await message.answer("Дата не может быть в будущем времени, повторите пожалуйста")
        else:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate < date.today():
                await state.update_data(user_date=edate)
                await message.answer("Теперь отправьте номер телефона через кнопку",reply_markup=contact_markup)
                await state.set_state(UserValue.user_number)
            else:
                await message.answer("Дата не может быть в будущем времени, повторите пожалуйста")
    except ValueError:
        await message.answer("Было введена дата не в том формате, повторите еще раз(без точек,запятых,пробелов только цифры и -)")

@user_private_router.message(UserValue.user_number,F.contact)
async def get_phone_number(message: types.Message,state: FSMContext):
    await state.update_data(user_number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(render_user(data))
    await message.answer("Вы довольны?",reply_markup=yes_no_kb)
    await state.set_state(UserValue.are_you_sure)
    
@user_private_router.message(UserValue.user_number,F.text)
async def get_phone_number2(message: types.Message,state: FSMContext):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    if message.text.casefold()=="пропустить" and user_for_change is not None:
        await state.update_data(user_number=user_for_change.phone_number)
        await message.answer("Ок оставляем этот номер телефона")
        data = await state.get_data()
        await message.answer(render_user(data))
        await message.answer("Вы довольны?",reply_markup=yes_no_kb)
        await state.set_state(UserValue.are_you_sure)
    else:
        await message.answer("Воспользуйтесь кнопкой")

@user_private_router.message(UserValue.are_you_sure,or_f(F.text.casefold()=="да",F.text.casefold()=="нет"))
async def are_you_sure_user(message: types.Message,state: FSMContext,session: AsyncSession):
    data=await state.get_data()
    user_for_change=data.get("user_for_change")
    user_for_delete=data.get("user_for_delete")
    if message.text.casefold() == "да" and user_for_change:
        data = await state.get_data()
        await orm_update_user(session,data)
        await message.answer("Обновление совершено",reply_markup=user_reply_keyboard)
        await state.clear()
        return
    elif message.text.casefold() == "да" and user_for_delete:
        result=await orm_read_user(session,message.from_user.id)
        if result:
            await orm_delete_user(session,message.from_user.id)
            await message.answer("Ваш аккаунт был удален",reply_markup=user_reply_keyboard)
            return
        else:
            await message.answer("Нечего удалять",reply_markup=user_reply_keyboard)
            return
    elif message.text.casefold() =="да":
        data = await state.get_data()
        await orm_add_user(session,data)
        await message.answer("Запись добавлена",reply_markup=user_reply_keyboard)
        await state.clear()
        return
    else:
        await message.answer("Запись/изменение/удаление не совершенно",reply_markup=user_reply_keyboard)
        await state.clear()
        return

@user_private_router.message(UserValue.are_you_sure,F.text)
async def are_you_sure_user_duplicate(message: types.Message,state: FSMContext):
    await message.answer("Выберите один из двух вариантов")

#search FSM
@user_private_router.message(StateFilter(None),Command("search_events"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="искать акции")
async def search_events(message: types.Message,state: FSMContext):
    await message.answer(
        "Введите название города",
        reply_markup=search_fsm_kb)
    await state.set_state(SearchValue.search_city)

@user_private_router.message(SearchValue.search_city,F.text)
async def search_city(message: types.Message,state: FSMContext):
    if message.text.casefold()=="пропустить":
        await state.update_data(city=None)
        await message.answer("Теперь отправьте минимальный возраст участия",reply_markup=search_age_fsm_kb)
        await state.set_state(SearchValue.search_req_age)
    else:
        if len(message.text) <= 100:
            await state.update_data(city=message.text)
            await message.answer("Теперь отправьте минимальный возраст участия",reply_markup=search_age_fsm_kb)
            await state.set_state(SearchValue.search_req_age)
        else:
            await message.answer("Название города превысило 100 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(SearchValue.search_req_age,F.text)
async def search_age(message: types.Message,state: FSMContext):
    try:
        if message.text.casefold()=="пропустить":
            await state.update_data(required_age=None)
            await message.answer("Теперь отправьте название",reply_markup=search_fsm_kb)
            await state.set_state(SearchValue.search_name)
        elif message.text.casefold()=="без ограничения":
            await state.update_data(required_age="gay")
            await message.answer("Теперь отправьте название",reply_markup=search_fsm_kb)
            await state.set_state(SearchValue.search_name)
        else:
            age=int(message.text)
            if age < 0:
                await message.answer("Нельзя вводить отрицательные числа")
            else:
                await state.update_data(required_age=age)
                await message.answer("Теперь отправьте название",reply_markup=search_fsm_kb)
                await state.set_state(SearchValue.search_name)
    except ValueError:
            await message.answer("Было введено не число, повторите еще раз(без точек,запятых,пробелов только цифры)")  

@user_private_router.message(SearchValue.search_name,F.text)
async def search_name(message: types.Message,state: FSMContext):
    if message.text.casefold()=="пропустить":
        await state.update_data(name=None)
        await message.answer("Теперь отправьте дату в таком формате yyyy-mm-dd",reply_markup=search_fsm_kb)
        await state.set_state(SearchValue.search_date)
    else:
        if len(message.text) <= 100:
            await state.update_data(name=message.text)
            await message.answer("Теперь отправьте дату в таком формате yyyy-mm-dd",reply_markup=search_fsm_kb)
            await state.set_state(SearchValue.search_date)
        else:
            await message.answer("Название события превысило 100 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(SearchValue.search_date,F.text)
async def search_date(message: types.Message,state: FSMContext):
    try:
        if message.text.casefold()=="пропустить":
            await state.update_data(event_date=None)
            await message.answer("Теперь отправьте количество баллов за это событие",reply_markup=search_fsm_kb)
            await state.set_state(SearchValue.search_point)
        else:
            edate=datetime.strptime(message.text,"%Y-%m-%d").date()
            if edate >= date.today():
                await state.update_data(event_date=edate)
                await message.answer("Теперь отправьте количество баллов за это событие",reply_markup=search_fsm_kb)
                await state.set_state(SearchValue.search_point)
            else:
                await message.answer("Дата не может быть в прошлом времени, повторите пожалуйста")
    except ValueError:
        await message.answer("Была введена дата не в том формате, повторите еще раз(без точек,запятых,пробелов только цифры и -)")

@user_private_router.message(SearchValue.search_point,F.text)
async def search_point(message: types.Message,state: FSMContext,session: AsyncSession):
    try:
        if message.text.casefold()=="пропустить":
            await state.update_data(point=None)
            data=await state.get_data()
            events = await orm_read_search_events(session,data)
            if not events:
                await message.answer("Нет событий",reply_markup=user_reply_keyboard)
            else:
                await send_events(events,message,session)
            await state.clear()
        else:
            number_of_points = parse_price_for_postgres(message.text)
            await state.update_data(point=number_of_points)
            data=await state.get_data()
            events = await orm_read_search_events(session,data)
            if not events:
                await message.answer("Нет событий",reply_markup=user_reply_keyboard)
            else:
                await send_events(events,message,session)
            await state.clear()    
    except ValueError as e:
        await message.answer(str(e))


#request FSM
@user_private_router.message(StateFilter(None),Command("create_request"))
@user_private_router.message(StateFilter(None),F.text.casefold()=="создать заявку")
async def create_request(message: types.Message,state: FSMContext):
    await message.answer(
        "Введите тип заявки(переполненая мусорка и т.д.)",
        reply_markup=request_keyboard)
    await state.set_state(RequestValue.request_name)
    await state.update_data(user_id=message.from_user.id, username=message.from_user.username, request_album=None, count=0)

@user_private_router.message(RequestValue.request_name,F.text)
async def name_request(message: types.Message,state: FSMContext):
    data = await state.get_data()
    request_for_change = data.get("request_for_change")
    if message.text.casefold()=="пропустить" and request_for_change is not None:
        await state.update_data(request_name=request_for_change.name)
        await message.answer("Ок оставляем этот тип, теперь отправьте новые фото/видео для этой заявки",reply_markup=request_keyboard_album_update)
        await state.set_state(RequestValue.request_album)
    else:   
        if len(message.text) <= 100:
            await state.update_data(request_name=message.text)
            await message.answer("Теперь отправьте фото/видео для заявки",reply_markup=request_keyboard_album)
            await state.set_state(RequestValue.request_album)
        else:
            await message.answer("Тип превысил 100 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(RequestValue.request_album,F.video)        
@user_private_router.message(RequestValue.request_album,F.photo)
async def get_album(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    media=data.get("request_album")
    count=data.get("count")
    if count == 10 and request_for_change is not None:
        await message.answer(f"Добавлено {count} из 10")
        await message.answer("Теперь отправьте новое местоположение/адрес для заявки",reply_markup=request_update_keyboard)
        await state.set_state(RequestValue.request_address)
    elif count == 10 and request_for_change is None:
        await message.answer(f"Добавлено {count} из 10")
        await message.answer("Теперь отправьте местоположение/адрес для заявки",reply_markup=request_keyboard)
        await state.set_state(RequestValue.request_address)
    else:
        if media is None:
            media=""
        if message.photo:
            media+=f"photo:{message.photo[-1].file_id},"
        else:
            media+=f"video:{message.video.file_id},"
        count += 1
        await state.update_data(request_album=media,count=count)
        await message.answer(f"Добавлено {count} из 10")

@user_private_router.message(RequestValue.request_album,F.text)
async def get_album2(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    if message.text.casefold()=="пропустить" and request_for_change is not None:
        await state.update_data(request_album=request_for_change.album)
        await message.answer("Ок оставляем эти фото и видео, теперь отправьте другой адрес",reply_markup=request_update_keyboard)
        await state.set_state(RequestValue.request_address)
    elif message.text.casefold()=="завершить" and request_for_change is not None:
        await message.answer("Теперь отправьте другой адрес",reply_markup=request_update_keyboard)
        await state.set_state(RequestValue.request_address)
    elif message.text.casefold()=="завершить":
        await message.answer("Теперь отправьте адрес",reply_markup=request_keyboard)
        await state.set_state(RequestValue.request_address)

@user_private_router.message(RequestValue.request_address,F.text)
async def request_location(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    if message.text.casefold()=="пропустить" and request_for_change is not None:
        await state.update_data(request_address=request_for_change.address)
        await message.answer("Ок оставляем это местоположение, теперь отправьте новый номер телефона",reply_markup=re_update_contact_markup)
        await state.set_state(RequestValue.request_phone_number)
    else:
        if len(message.text) <= 100:
            await state.update_data(request_address=message.text)
            await message.answer("Теперь отправьте номер телефона через кнопку",reply_markup=re_contact_markup)
            await state.set_state(RequestValue.request_phone_number)
        else:
            await message.answer("Длина адреса превысило 100 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(RequestValue.request_phone_number,F.contact)
async def get_phone_number_request(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    await state.update_data(phone_number=message.contact.phone_number)
    if request_for_change is None:
        await message.answer("Теперь напишите примечание/описание к заявке",reply_markup=request_keyboard)
    else:
        await message.answer("Теперь напишите новое примечание/описание",reply_markup=request_update_keyboard)
    await state.set_state(RequestValue.request_description)
    
@user_private_router.message(RequestValue.request_phone_number,F.text)
async def get_phone_number_request2(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    if message.text.casefold()=="пропустить" and request_for_change is not None:
        await state.update_data(phone_number=request_for_change.phone_number)
        await message.answer("Ок оставляем этот номер телефона, теперь отправьте новое примечание/описание",reply_markup=request_update_keyboard)
        await state.set_state(RequestValue.request_description)
    else:
        await message.answer("Воспользуйтесь кнопкой")

@user_private_router.message(RequestValue.request_description,F.text)
async def request_description(message: types.Message,state: FSMContext):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    if message.text.casefold()=="пропустить" and request_for_change is not None:
        await state.update_data(request_description=request_for_change.description)
        await message.answer("Ок оставляем это описание",reply_markup=request_yes_no_kb)
        data = await state.get_data()
        await send_request(message=message,request=data)
        await message.answer("Вы довольны?",reply_markup=request_yes_no_kb)
        await state.set_state(RequestValue.are_you_sure)
    else:
        if len(message.text) <= 600:
            await state.update_data(request_description=message.text,request_date=datetime.now())
            await message.answer("Вы довольны?",reply_markup=request_yes_no_kb)
            data = await state.get_data()
            await send_request(message=message,request=data)
            await state.set_state(RequestValue.are_you_sure)
        else:
            await message.answer("Описание превысило 600 символов, повторите на этот раз с меньшим количеством")

@user_private_router.message(RequestValue.are_you_sure,or_f(F.text.casefold()=="да",F.text.casefold()=="нет"))
async def are_you_sure_request(message: types.Message,state: FSMContext,session: AsyncSession):
    data=await state.get_data()
    request_for_change=data.get("request_for_change")
    if message.text.casefold()=="да" and request_for_change is not None:
        data = await state.get_data()
        await orm_update_request(session,data)
        await message.answer("Обновление совершено",reply_markup=user_reply_keyboard)
        await state.clear()
    elif message.text.casefold()=="да":
        data = await state.get_data()
        await orm_add_request(session,data)
        await message.answer("Запись добавлена",reply_markup=user_reply_keyboard)
        await state.clear()
    else:
        await message.answer("Запись/изменение не добавлено",reply_markup=user_reply_keyboard)
        await state.clear()

