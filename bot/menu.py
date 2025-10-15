from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

def help_menu():
    keyboard = [
        [KeyboardButton("📋 Меню")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_main_menu():
    """Возвращает главное меню с основными командами"""
    keyboard = [
        [InlineKeyboardButton("📅 Расписание", callback_data="menu_schedule")],
        [InlineKeyboardButton("➕ Добавить урок", callback_data="menu_add_lesson")],
        [InlineKeyboardButton("✏️ Редактировать урок", callback_data="menu_edit_lesson")],
        [InlineKeyboardButton("🗑️ Удалить урок", callback_data="menu_delete_lesson")],
        [InlineKeyboardButton("🧹 Очистить расписание", callback_data="menu_clear_schedule")],
        # [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# def get_schedule_menu():
#     """Возвращает меню для работы с расписанием"""
#     keyboard = [
#         [InlineKeyboardButton("📅 Показать расписание", callback_data="show_schedule")],
#         [InlineKeyboardButton("📅 Показать по дню", callback_data="show_schedule_day")],
#         [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
#     ]
#     return InlineKeyboardMarkup(keyboard)
def get_schedule_menu():
    keyboard = [
        [InlineKeyboardButton('🔙 Назад в главное меню', callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_days_menu():
    """Возвращает меню выбора дня недели"""
    from .schedule import WEEKDAYS
    keyboard = []
    for day in WEEKDAYS:
        keyboard.append([InlineKeyboardButton(day, callback_data=f"day_{day}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_schedule_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu():
    """Возвращает меню для администраторов"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить урок", callback_data="add_lesson")],
        [InlineKeyboardButton("✏️ Редактировать урок", callback_data="edit_lesson")],
        [InlineKeyboardButton("🗑️ Удалить урок", callback_data="delete_lesson")],
        [InlineKeyboardButton("🧹 Очистить расписание", callback_data="clear_schedule")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_clear_confirm_menu():
    """Возвращает меню подтверждения очистки расписания"""
    keyboard = [
        [InlineKeyboardButton("✅ Да, очистить всё", callback_data="confirm_clear")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_clear")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
