from decimal import Decimal, InvalidOperation, getcontext, ROUND_DOWN
import re

# Устанавливаем безопасную точность для Decimal
getcontext().prec = 50

# Максимальное значение для BIGINT в PostgreSQL
MAX_CENTS_BIGINT = 9_223_372_036_854_775_807

def parse_price_for_postgres(user_input: str) -> int:
    """
    Безопасно парсит цену от пользователя, возвращает целые центы.
    Проверяет:
    - формат ввода
    - максимум 2 знака после точки
    - не превышает лимит BIGINT
    """
    # Проверка формата: положительное число, до 2 знаков после точки, без лишних ведущих нулей
    pattern = r'^(0|[1-9]\d*)(\.\d{1,2})?$'
    if not re.match(pattern, user_input):
        raise ValueError("Неверный формат числа: положительное число с максимум 2 знаками после точки")

    try:
        d = Decimal(user_input)
        # Квантование до 2 знаков после точки
        d = d.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        # Перевод в центы
        cents = int(d * 100)
    except InvalidOperation:
        raise ValueError("Некорректное число")
    except OverflowError:
        raise ValueError("Число слишком большое для обработки")

    # Проверка лимита для BIGINT
    if cents > MAX_CENTS_BIGINT:
        raise ValueError("Цена слишком большая для хранения в базе данных")

    return cents
