from database.models import Event,User,Request,Report
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
        username=f"@{user.username}" if user.username is not None else "Нет username"
        return (
            f"{user.name} {user.surname} {user.fathers_name}\n"
            f"📅 Дата рождения: {date_str}\n"
            f"🕑 Возраст на сегодня: {age_str}\n"
            f"📞 Номер телефона: {user.phone_number}\n"
            f"💸 Баланс: {users_balance}\n"
            f"{username}"
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

def render_request(request: Request | dict[str,datetime]) -> str:
    if isinstance(request,Request):
        date_str = request.created_at.strftime("%Y-%m-%d %H:%M")
        username=f"@{request.username}" if request.username is not None else "Нет username"
        return (
            f"📌 {request.name}\n"
            f"📝 {request.description}\n"
            f"🚩 Адрес: {request.address}\n"
            f"📅 Дата и время создания: {date_str}\n"
            f"👤 Создатель: {username}\n"
            f"📞 Номер телефона: {request.phone_number}\n"
            f"📢 Статус заявки: {request.status.capitalize()}"
        )
    elif isinstance(request, dict):
        date_str = request["request_date"].strftime("%Y-%m-%d %H:%M") 
        username=f"@{request["username"]}" if request["username"] is not None else "Нет username"
        return (
            f"📌 {request["request_name"]}\n"
            f"📝 {request["request_description"]}\n"
            f"🚩 Адрес: {request["request_address"]}\n"
            f"📅 Дата и время создания: {date_str}\n"
            f"👤 Создатель: {username}\n"
            f"📞 Номер телефона: {request["phone_number"]}\n"
            f"📢 Статус заявки: В ожидании"
        )

def render_report(report: Report | dict) -> str:
    if isinstance(report,Report):
        date_str = report.created_at.strftime("%Y-%m-%d %H:%M")
        username=f"@{report.username}" if report.username is not None else "Нет username"
        return (
            f"📌 {report.name}\n"
            f"📝 {report.description}\n"
            f"🚩 Адрес: {report.address}\n"
            f"📅 Дата и время создания: {date_str}\n"
            f"👤 Создатель: {username}\n"
            f"📞 Номер телефона: {report.phone_number}\n"
        )
    elif isinstance(report, dict):
        date_str = report["report_date"].strftime("%Y-%m-%d %H:%M") 
        username=f"@{report["username"]}" if report["username"] is not None else "Нет username"
        return (
            f"📌 {report["report_name"]}\n"
            f"📝 {report["report_description"]}\n"
            f"🚩 Адрес: {report["report_address"]}\n"
            f"📅 Дата и время создания: {date_str}\n"
            f"👤 Создатель: {username}\n"
            f"📞 Номер телефона: {report["phone_number"]}\n"
        )