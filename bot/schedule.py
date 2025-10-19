from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, CommandHandler, filters
from .models import models
import os
from dotenv import load_dotenv


# Константы для расписания
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
LESSON_TIMES = [
    "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
    "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
]

# Диалоговое удаление урока
DEL_SELECT_DAY, DEL_SELECT_LESSON, DEL_CONFIRM = range(10, 13)


async def delschedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back_to_main':
        await query.edit_message_text('Удаление расписания отменено.')
        return ConversationHandler.END
    day = query.data
    context.user_data['del_day'] = day
    lessons = models.get_schedule()
    # user-friendly: сортировка по времени, правильные номера
    def get_lesson_num(time):
        for i, t in enumerate(LESSON_TIMES):
            if t == time:
                return i + 1
        return None
    lessons_for_day = [(get_lesson_num(time), lesson, time) for d, lesson, time in lessons if d == day]
    lessons_for_day = sorted([l for l in lessons_for_day if l[0] is not None], key=lambda x: x[0])
    if not lessons_for_day:
        await query.edit_message_text('В этот день нет уроков.')
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(f"{num}. {lesson} ({time})", callback_data=str(num-1))] for num, lesson, time in lessons_for_day
    ]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Выберите урок для удаления:', reply_markup=reply_markup)
    context.user_data['lessons_for_day'] = lessons_for_day
    return DEL_SELECT_LESSON


async def delschedule_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_days':
        keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Выберите день недели для удаления:', reply_markup=reply_markup)
        return DEL_SELECT_DAY

    # Получаем информацию об уроке из lessons_for_day
    lessons_for_day = context.user_data['lessons_for_day']
    selected_lesson = next((lesson for num, lesson, time in lessons_for_day if str(num-1) == query.data), None)
    selected_time = next((time for num, lesson, time in lessons_for_day if str(num-1) == query.data), None)
    
    if not selected_lesson or not selected_time:
        await query.edit_message_text('Ошибка: не удалось найти урок для удаления.')
        return ConversationHandler.END

    day = context.user_data['del_day']
    
    # Сохраняем данные для удаления
    context.user_data['del_lesson'] = selected_lesson
    context.user_data['del_time'] = selected_time
    
    # Запрашиваем подтверждение
    await query.edit_message_text(
        f'Удалить урок: {selected_lesson} ({selected_time})?\nДень: {day}',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Удалить', callback_data='yes')],
            [InlineKeyboardButton('🔙 Назад', callback_data='back_to_lessons')]
        ])
    )
    return DEL_CONFIRM

async def delschedule_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_lessons':
        # Возврат к списку уроков
        day = context.user_data['del_day']
        lessons = models.get_schedule()
        def get_lesson_num(time):
            for i, t in enumerate(LESSON_TIMES):
                if t == time:
                    return i + 1
            return None
        lessons_for_day = [(get_lesson_num(time), lesson, time) for d, lesson, time in lessons if d == day]
        lessons_for_day = sorted([l for l in lessons_for_day if l[0] is not None], key=lambda x: x[0])
        keyboard = [
            [InlineKeyboardButton(f"{num}. {lesson} ({time})", callback_data=str(num-1))] 
            for num, lesson, time in lessons_for_day
        ]
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Выберите урок для удаления:', reply_markup=reply_markup)
        return DEL_SELECT_LESSON

    if query.data == 'yes':
        day = context.user_data['del_day']
        lesson = context.user_data['del_lesson']
        time = context.user_data['del_time']
        
        # Получаем id урока по точным параметрам
        conn = models.sqlite3.connect(models.DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id FROM schedule WHERE day=? AND lesson=? AND time=?', 
                   (day, lesson, time))
        row = cur.fetchone()
        conn.close()
        
        if row:
            schedule_id = row[0]
            models.delete_schedule(schedule_id)
            await query.edit_message_text(f'Урок {lesson} ({time}) удалён.')
        else:
            await query.edit_message_text('Ошибка: урок не найден.')
    else:
        await query.edit_message_text('Удаление отменено.')
    return ConversationHandler.END

async def delschedule_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Удаление расписания отменено.')
    return ConversationHandler.END

async def delschedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может удалять расписание.')
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите день недели для удаления:', reply_markup=reply_markup)
    return DEL_SELECT_DAY

async def delschedule_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.callback_query.edit_message_text('Только админ может удалять расписание.')
        return
    # Устанавливаем флаг для удаления урока
    context.user_data['deleting_lesson'] = True
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Выберите день недели для удаления:', reply_markup=reply_markup)


load_dotenv()
def get_admin_ids():
    raw = os.getenv('ADMIN_IDS', '').replace("'","").replace('"',"").strip()
    ids = []
    for i in raw.split(','):
        s = i.strip()
        if s:
            try:
                ids.append(int(s))
            except ValueError:
                pass
    return ids

ADMIN_IDS = get_admin_ids()

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    schedule = models.get_schedule()
    if not schedule:
        await update.message.reply_text('Расписание пусто.')
        return
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    # Вспомогательная функция для поиска номера урока по времени
    def get_lesson_num(time):
        for i, t in enumerate(LESSON_TIMES):
            if t == time:
                return i + 1
        return None

    # Если указан день, показываем только его
    if args:
        day_query = args[0].capitalize()
        if day_query not in days:
            await update.message.reply_text('Укажите день недели: Понедельник, Вторник, Среда, Четверг, Пятница')
            return
        lessons = [(get_lesson_num(time), lesson, time) for d, lesson, time in schedule if d == day_query]
        # Оставляем только заполненные номера
        lessons = sorted([l for l in lessons if l[0] is not None], key=lambda x: x[0])
        if lessons:
            text = f'<b>{day_query}</b>\n'
            for num, lesson, time in lessons:
                text += f'{num}. {lesson} — <b>{time}</b>\n'
        else:
            text = f'<b>{day_query}</b>\nНет уроков'
            await update.message.reply_text(text, parse_mode='HTML')
            return
    # Выводим расписание на всю неделю
    text = '<b>Расписание на неделю:</b>\n'
    for day in days:
        text += f'\n<b>{day}</b>\n'
        lessons = [(get_lesson_num(time), lesson, time) for d, lesson, time in schedule if d == day]
        lessons = sorted([l for l in lessons if l[0] is not None], key=lambda x: x[0])
        if lessons:
            for num, lesson, time in lessons:
                text += f'{num}. {lesson} — <b>{time}</b>\n'
        else:
            text += 'Нет уроков\n'
    await update.message.reply_text(text, parse_mode='HTML')


# Стадии диалога
SELECT_DAY, SELECT_LESSON, INPUT_NAME, ADD_MORE = range(4)

LESSON_TIMES = [
    "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
    "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
]
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]

async def addschedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"addschedule_start called by user {user_id}")
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может добавлять расписание.')
        print(f"User {user_id} is not admin. ADMIN_IDS: {ADMIN_IDS}")
        return ConversationHandler.END
    print(f"User {user_id} is admin. Showing days keyboard.")
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите день недели:', reply_markup=reply_markup)
    return SELECT_DAY

async def addschedule_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"addschedule_start_callback called by user {user_id}")
    if user_id not in ADMIN_IDS:
        await update.callback_query.edit_message_text('Только админ может добавлять расписание.')
        print(f"User {user_id} is not admin. ADMIN_IDS: {ADMIN_IDS}")
        return
    print(f"User {user_id} is admin. Showing days keyboard.")
    # Устанавливаем флаг для добавления урока
    context.user_data['adding_lesson'] = True
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Выберите день недели:', reply_markup=reply_markup)

async def addschedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back_to_main':
        await query.edit_message_text('Добавление расписания отменено.')
        return ConversationHandler.END
    context.user_data['day'] = query.data
    # Получаем все занятые слоты для выбранного дня
    lessons = models.get_schedule()
    busy_times = set([time for d, l, time in lessons if d == query.data])
    keyboard = []
    for i, time in enumerate(LESSON_TIMES):
        if time not in busy_times:
            keyboard.append([InlineKeyboardButton(f"{i+1} урок ({time})", callback_data=str(i))])
    if not keyboard:
        await query.edit_message_text('В этот день все слоты заняты.')
        return ConversationHandler.END
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Выберите номер урока:', reply_markup=reply_markup)
    return SELECT_LESSON

async def addschedule_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back_to_days':
        # Возвращаемся к выбору дня
        keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Выберите день недели:', reply_markup=reply_markup)
        return SELECT_DAY
    lesson_idx = int(query.data)
    context.user_data['lesson_time'] = LESSON_TIMES[lesson_idx]
    context.user_data['lesson_num'] = lesson_idx + 1
    # Список предметов
    SUBJECTS = [
        "Биология", "Информатика", "Литература", "Алгебра", "РМГ", "Вероятность и статистика",
        "Обществознание", "История", "География", "Геометрия", "Физкультура", "ОБЗР",
        "Английский язык", "Физика", "Проект"
    ]
    keyboard = [[InlineKeyboardButton(subj, callback_data=subj)] for subj in SUBJECTS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_lesson')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Выберите название урока для {context.user_data["lesson_num"]} урока ({context.user_data["lesson_time"]}):', reply_markup=reply_markup)
    return INPUT_NAME

async def addschedule_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем название из callback_data, если это callback, иначе из текста
    if update.callback_query:
        if update.callback_query.data == 'back_to_lesson':
            # Возвращаемся к выбору времени
            day = context.user_data['day']
            lessons = models.get_schedule()
            busy_times = set([time for d, l, time in lessons if d == day])
            keyboard = []
            for i, time in enumerate(LESSON_TIMES):
                if time not in busy_times:
                    keyboard.append([InlineKeyboardButton(f"{i+1} урок ({time})", callback_data=str(i))])
            if not keyboard:
                await update.callback_query.edit_message_text('В этот день все слоты заняты.')
                return ConversationHandler.END
            keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(f'Выберите номер урока для {day}:', reply_markup=reply_markup)
            return SELECT_LESSON
        lesson_name = update.callback_query.data
    else:
        lesson_name = update.message.text.strip()
    day = context.user_data['day']
    time = context.user_data['lesson_time']
    # Проверка на уникальность урока по дню и времени
    existing = [l for d, l, t in models.get_schedule() if d == day and t == time]
    if existing:
        await update.effective_message.reply_text(f'В этот день и время уже есть урок: {existing[0]}')
        # Удалить кнопки
        if update.callback_query:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        return ConversationHandler.END
    models.add_schedule(day, lesson_name, time)
    await update.effective_message.reply_text(f'Добавлено: {day} {lesson_name} {time}')
    
    # Предлагаем добавить еще урок в тот же день
    keyboard = [
        [InlineKeyboardButton('➕ Добавить еще урок', callback_data='add_more')],
        [InlineKeyboardButton('🔙 Назад к выбору дня', callback_data='back_to_days')],
        [InlineKeyboardButton('✅ Завершить', callback_data='finish')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        f'Урок добавлен в {day}!\n\nЧто хотите сделать дальше?',
        reply_markup=reply_markup
    )
    return ADD_MORE

async def addschedule_add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add_more':
        # Возвращаемся к выбору времени для того же дня
        day = context.user_data['day']
        lessons = models.get_schedule()
        busy_times = set([time for d, l, time in lessons if d == day])
        keyboard = []
        for i, time in enumerate(LESSON_TIMES):
            if time not in busy_times:
                keyboard.append([InlineKeyboardButton(f"{i+1} урок ({time})", callback_data=str(i))])
        if not keyboard:
            await query.edit_message_text('В этот день все слоты заняты.')
            return ConversationHandler.END
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f'Выберите номер урока для {day}:', reply_markup=reply_markup)
        return SELECT_LESSON
    elif query.data == 'back_to_days':
        # Возвращаемся к выбору дня
        keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Выберите день недели:', reply_markup=reply_markup)
        return SELECT_DAY
    elif query.data == 'finish':
        await query.edit_message_text('Добавление расписания завершено!')
        return ConversationHandler.END

async def addschedule_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Добавление расписания отменено.')
    return ConversationHandler.END

async def delete_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может удалять расписание.')
        return
    args = context.args
    if not args:
        await update.message.reply_text('Используйте: /delschedule <id>')
        return
    schedule_id = int(args[0])
    models.delete_schedule(schedule_id)
    await update.message.reply_text(f'Удалено расписание с id {schedule_id}')

async def edit_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может редактировать расписание.')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('Используйте: /editschedule <id> <день> <урок> <время>')
        return
    schedule_id, day, lesson, time = int(args[0]), args[1], args[2], args[3]
    models.edit_schedule(schedule_id, day, lesson, time)
    await update.message.reply_text(f'Изменено расписание с id {schedule_id}')

# Диалоговое редактирование урока
EDIT_SELECT_DAY, EDIT_SELECT_LESSON, EDIT_INPUT_NAME = range(20, 23)

async def editschedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может редактировать расписание.')
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите день недели для редактирования:', reply_markup=reply_markup)
    return EDIT_SELECT_DAY

async def editschedule_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.callback_query.edit_message_text('Только админ может редактировать расписание.')
        return
    # Устанавливаем флаг для редактирования урока
    context.user_data['editing_lesson'] = True
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Выберите день недели для редактирования:', reply_markup=reply_markup)

async def editschedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back_to_main':
        await query.edit_message_text('Редактирование расписания отменено.')
        return ConversationHandler.END
    day = query.data
    context.user_data['edit_day'] = day
    lessons = models.get_schedule()
    # user-friendly: сортировка по времени, правильные номера
    def get_lesson_num(time):
        for i, t in enumerate(LESSON_TIMES):
            if t == time:
                return i + 1
        return None
    lessons_for_day = [(get_lesson_num(time), lesson, time) for d, lesson, time in lessons if d == day]
    lessons_for_day = sorted([l for l in lessons_for_day if l[0] is not None], key=lambda x: x[0])
    if not lessons_for_day:
        await query.edit_message_text('В этот день нет уроков.')
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(f"{num}. {lesson} ({time})", callback_data=str(num-1))] for num, lesson, time in lessons_for_day
    ]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Выберите урок для редактирования:', reply_markup=reply_markup)
    context.user_data['lessons_for_day'] = lessons_for_day
    return EDIT_SELECT_LESSON

async def editschedule_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_days':
        keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in WEEKDAYS]
        keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Выберите день недели для редактирования:', reply_markup=reply_markup)
        return EDIT_SELECT_DAY

    # Получаем информацию об уроке из lessons_for_day
    lessons_for_day = context.user_data['lessons_for_day']
    selected_lesson = next((lesson for num, lesson, time in lessons_for_day if str(num-1) == query.data), None)
    selected_time = next((time for num, lesson, time in lessons_for_day if str(num-1) == query.data), None)
    
    if not selected_lesson or not selected_time:
        await query.edit_message_text('Ошибка: не удалось найти урок для редактирования.')
        return ConversationHandler.END

    day = context.user_data['edit_day']
    
    # Получаем id урока для редактирования
    conn = models.sqlite3.connect(models.DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id FROM schedule WHERE day=? AND lesson=? AND time=?', 
                (day, selected_lesson, selected_time))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        await query.edit_message_text('Ошибка: урок не найден.')
        return ConversationHandler.END
        
    schedule_id = row[0]
    context.user_data['edit_schedule_id'] = schedule_id
    context.user_data['edit_lesson_time'] = selected_time

    # Список предметов для выбора
    SUBJECTS = [
        "Биология", "Информатика", "Литература", "Алгебра", "РМГ", "Вероятность и статистика",
        "Обществознание", "История", "География", "Геометрия", "Физкультура", "ОБЗР",
        "Английский язык", "Физика", "Проект"
    ]
    keyboard = [[InlineKeyboardButton(subj, callback_data=subj)] for subj in SUBJECTS]
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_lessons')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f'Текущий урок: {selected_lesson}\nВремя: {selected_time}\n\nВыберите новое название для урока:',
        reply_markup=reply_markup
    )
    return EDIT_INPUT_NAME

async def editschedule_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем название из callback_data, если это callback, иначе из текста
    if update.callback_query:
        if update.callback_query.data == 'back_to_lessons':
            # Возвращаемся к выбору урока
            day = context.user_data['edit_day']
            lessons = models.get_schedule()
            def get_lesson_num(time):
                for i, t in enumerate(LESSON_TIMES):
                    if t == time:
                        return i + 1
                return None
            lessons_for_day = [(get_lesson_num(time), lesson, time) for d, lesson, time in lessons if d == day]
            lessons_for_day = sorted([l for l in lessons_for_day if l[0] is not None], key=lambda x: x[0])
            keyboard = [
                [InlineKeyboardButton(f"{num}. {lesson} ({time})", callback_data=str(num-1))] for num, lesson, time in lessons_for_day
            ]
            keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='back_to_days')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text('Выберите урок для редактирования:', reply_markup=reply_markup)
            return EDIT_SELECT_LESSON
        new_name = update.callback_query.data
    else:
        new_name = update.message.text.strip()
    schedule_id = context.user_data['edit_schedule_id']
    day = context.user_data['edit_day']
    time = context.user_data['edit_lesson_time']
    models.edit_schedule(schedule_id, day, new_name, time)
    await update.effective_message.reply_text(f'Урок обновлён: {day} {new_name} {time}')
    # Удалить кнопки
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(reply_markup=None)
    return ConversationHandler.END

async def editschedule_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Редактирование расписания отменено.')
    return ConversationHandler.END

async def clear_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text('Только админ может очищать расписание.')
        return
    # Очищаем только таблицу расписания
    conn = models.sqlite3.connect(models.DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM schedule')
    conn.commit()
    conn.close()
    await update.message.reply_text('Все расписание очищено.')