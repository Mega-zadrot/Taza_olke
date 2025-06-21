from aiogram.utils.keyboard import InlineKeyboardBuilder
def get_inline_keyboard(data: dict[str,str],sizes=(2,)):
    builder=InlineKeyboardBuilder()
    for text, data in data.items():
        builder.button(text=text,callback_data=data)
    return builder.adjust(*sizes).as_markup()