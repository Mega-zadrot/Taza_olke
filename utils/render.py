from database.models import Event,User
from .time import calculate_age
from datetime import datetime
from decimal import Decimal
def render_event(event: Event | dict,user_num: int = 0) -> str:
    if isinstance(event,Event):
        state_str = "Активна" if event.state else "Отменена"
        age_str = str(event.required_age) if event.required_age is not None else "Не ограничено"
        date_str = event.event_date.strftime("%Y-%m-%d") 
        limit_str = str(event.limit) if event.limit is not None else "не ограниченого"
        events_point = Decimal(event.point)/Decimal("100")
        return (
            f"📌 {event.name}\n"
            f"👥 Количество участников: {user_num} из {limit_str}\n"
            f"📝 {event.description}\n"
            f"🚩 Местоположение: {event.city}\n"
            f"📅 Дата: {date_str}\n"
            f"🎯 Баллы: {events_point}\n"
            f"📍 Состояние: {state_str}\n"
            f"🔞 Мин. возраст: {age_str}"
        )
    elif isinstance(event, dict):
        age_str = str(event["event_age"]) if event["event_age"] is not None else "Не ограничено"
        date_str = event["event_date"].strftime("%Y-%m-%d") 
        limit_str = str(event["event_limit"]) if event["event_limit"] is not None else "не ограниченого"
        event_point=Decimal(event["event_point"])/Decimal("100")
        return (
            f"📌 {event["event_name"]}\n"
            f"👥 Количество участников: {user_num} из {limit_str}\n"
            f"📝 {event["event_description"]}\n"
            f"🚩 Местоположение: {event["event_city"]}\n"
            f"📅 Дата: {date_str}\n"
            f"🎯 Баллы: {event_point}\n"
            f"📍 Состояние: {"Активна"}\n"
            f"🔞 Мин. возраст: {age_str}")
    

def render_user(user: dict | User) -> str:
    if isinstance(user, User):
        age_str = calculate_age(user.birth_date)
        date_str = user.birth_date.strftime("%Y-%m-%d") 
        users_balance = Decimal(user.balance) / Decimal("100")
        return (
            f"{user.name} {user.surname} {user.fathers_name}\n"
            f"📅 Дата рождения: {date_str}\n"
            f"🕑 Возраст на сегодня: {age_str}\n"
            f"📞 Номер телефона: {user.phone_number}\n"
            f"💸 Баланс: {users_balance}"
        )
    elif isinstance(user, dict):
        age_str = calculate_age(user["user_date"])
        date_str = datetime.strftime(user["user_date"],"%Y-%m-%d")
        return (
            f"Вот что получилось:\n{user["user_name"]} {user["user_surname"]} {user["user_fname"]}\n"
            f"📅 Дата рождения: {date_str}\n"
            f"🕑 Возраст на сегодня: {age_str}\n"
            f"📞 Номер телефона: {user["user_number"]}\n"
        )
    else:
        return f"У вас нет зарегистрированого аккаунта"
    
def render_my_event(event: Event, state: bool | None):
    state_str = "Активна" if event.state else "Отменена"
    age_str = str(event.required_age) if event.required_age is not None else "Не ограничено"
    date_str = event.event_date.strftime("%Y-%m-%d")
    was_or_not=(
        "Зарегистрирован" if state is None
        else "Присуствовал" if state
        else "Зарегистрирован" if state_str=="Отменена"
        else "Не присуствовал"
    )
    events_point = Decimal(event.point)/Decimal("100")
    return (
        f"📌 {event.name}\n"
        f"📝 {event.description}\n"
        f"🚩 Местоположение: {event.city}\n"
        f"📅 Дата: {date_str}\n"
        f"🎯 Баллы: {events_point}\n"
        f"📍 Состояние: {state_str}\n"
        f"🔞 Мин. возраст: {age_str}\n"
        f"👤 {was_or_not}"
    )