from datetime import datetime, date, timedelta
import asyncio
def calculate_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year

    # Если день рождения ещё не наступил в этом году — уменьшаем возраст на 1
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def daily_notifier(func):
    async def wrapper():
        while True:
            now = datetime.now()
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            await func()
    return wrapper

