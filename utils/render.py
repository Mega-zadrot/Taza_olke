from database.models import Event,User
from .time import calculate_age
from datetime import datetime

def render_event(event: Event | dict,user_num: int = 0) -> str:
    if isinstance(event,Event):
        state_str = "Активна" if event.state else "Отменена"
        age_str = str(event.required_age) if event.required_age is not None else "Не ограничено"
        date_str = event.event_date.strftime("%Y-%m-%d") 
        limit_str = str(event.limit) if event.limit is not None else "не ограничено"

        return (
            f"📌 {event.name}\n"
            f"👥 Количество зарегистрированных участников: {user_num} из {limit_str}\n"
            f"📝 {event.description}\n"
            f"📅 Дата: {date_str}\n"
            f"🎯 Баллы: {event.point}\n"
            f"📍 Состояние: {state_str}\n"
            f"🔞 Мин. возраст: {age_str}"
        )
    elif isinstance(event, dict):
        age_str = str(event["event_age"]) if event["event_age"] is not None else "Не ограничено"
        date_str = event["event_date"].strftime("%Y-%m-%d") 
        limit_str = str(event["event_limit"]) if event["event_limit"] is not None else "не ограничено"

        return (
            f"📌 {event["event_name"]}\n"
            f"👥 Количество зарегистрированных участников: {user_num} из {limit_str}\n"
            f"📝 {event["event_description"]}\n"
            f"📅 Дата: {date_str}\n"
            f"🎯 Баллы: {event["event_point"]}\n"
            f"📍 Состояние: {"Активна"}\n"
            f"🔞 Мин. возраст: {age_str}")
    

def render_user(user: dict | User) -> str:
    if isinstance(user, User):
        age_str = calculate_age(user.birth_date)
        date_str = user.birth_date.strftime("%Y-%m-%d") 
        return (
            f"{user.name} {user.surname} {user.fathers_name}\n"
            f"дата рождения: {date_str}\n"
            f"возраст на сегодня: {age_str}\n"
            f"номер телефона: {user.phone_number}\n"
            f"баланс: {user.balance}"
        )
    elif isinstance(user, dict):
        age_str = calculate_age(user["user_date"])
        date_str = datetime.strftime(user["user_date"],"%Y-%m-%d")
        return (
            f"вот что получилось:\n{user["user_name"]} {user["user_surname"]} {user["user_fname"]}\n"
            f"дата рождения: {date_str}\n"
            f"возраст на сегодня: {age_str}\n"
            f"номер телефона: {user["user_number"]}\n"
        )
    else:
        return f"у вас нет зарегистрированого аккаунта"
    
def render_my_event(event: Event,state: bool | None):
    state_str = "Активна" if event.state else "Отменена"
    age_str = str(event.required_age) if event.required_age is not None else "Не ограничено"
    date_str = event.event_date.strftime("%Y-%m-%d")
    was_or_not=(
        "зарегистрирован" if state is None
        else "присуствовал" if state
        else "зарегистрирован" if state_str=="Отменена"
        else "не присуствовал"
    )
    return (
        f"📌 {event.name}\n"
        f"📝 {event.description}\n"
        f"📅 Дата: {date_str}\n"
        f"🎯 Баллы: {event.point}\n"
        f"📍 Состояние: {state_str}\n"
        f"🔞 Мин. возраст: {age_str}\n"
        f"👤 {was_or_not}"
    )