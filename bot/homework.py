from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .models import models
import os
from dotenv import load_dotenv

load_dotenv()

# Conversation stages
HW_SELECT_ACTION, HW_SELECT_SUBJECT, HW_INPUT_TASK, HW_SELECT_HW, HW_CONFIRM_DELETE, HW_EDIT_INPUT = range(6)

SUBJECTS = [
    "Биология", "Информатика", "Литература", "Алгебра", "РМГ", "Вероятность и статистика",
    "Обществознание", "История", "География", "Геометрия", "Физкультура", "ОБЗР",
    "Английский язык", "Физика", "Проект"
]

async def show_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hw = models.get_homework()
    text = '<b>Домашние задания:</b>\n'
    if not hw:
        text = 'Домашние задания отсутствуют.'
    else:
        for _id, subject, task, due in hw:
            when = f' (к {due})' if due else ''
            text += f'\n<b>{subject}</b>: {task}{when}\n'
    # support both message and callback_query
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def show_homework_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback-friendly wrapper to show homework by editing the message."""
    await show_homework(update, context)

async def addhomework_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # show subjects
    keyboard = [[InlineKeyboardButton(s, callback_data=s)] for s in SUBJECTS]
    keyboard.append([InlineKeyboardButton('🔙 Отмена', callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text('Выберите предмет для домашнего задания:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Выберите предмет для домашнего задания:', reply_markup=reply_markup)
    return HW_SELECT_SUBJECT

async def addhomework_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback wrapper for addhomework_start."""
    return await addhomework_start(update, context)

async def addhomework_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text('Добавление домашки отменено.')
        return ConversationHandler.END
    context.user_data['hw_subject'] = query.data
    # mark that we expect a text input next
    context.user_data['expecting_homework_input'] = True
    await query.edit_message_text('Введите текст задания (и при желании срок, например: "прочитать главы 1-2; 2025-11-05")')
    return HW_INPUT_TASK

async def addhomework_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # text from message
    text = update.message.text.strip()
    # naive split by ';' for task and due date
    if ';' in text:
        task, due = [p.strip() for p in text.split(';', 1)]
    else:
        task, due = text, None
    subject = context.user_data.get('hw_subject')
    if not subject:
        await update.message.reply_text('Не выбран предмет. Отправьте /addhomework заново.')
        return ConversationHandler.END
    models.add_homework(subject, task, due)
    await update.message.reply_text(f'Добавлено: {subject} — {task}{f" (к {due})" if due else ""}')
    # clear expectation flag
    context.user_data.pop('expecting_homework_input', None)
    # clear flow flag
    context.user_data.pop('adding_homework', None)
    return ConversationHandler.END

async def delhomework_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hw = models.get_homework()
    if not hw:
        if update.callback_query:
            await update.callback_query.edit_message_text('Домашние задания отсутствуют.')
        else:
            await update.message.reply_text('Домашние задания отсутствуют.')
        return ConversationHandler.END
    keyboard = []
    for _id, subject, task, due in hw:
        label = f'{subject}: {task[:30]}{("..." if len(task)>30 else "")}'
        keyboard.append([InlineKeyboardButton(label, callback_data=f'hw_del_{_id}')])
    keyboard.append([InlineKeyboardButton('🔙 Отмена', callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text('Выберите задание для удаления:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Выберите задание для удаления:', reply_markup=reply_markup)
    context.user_data['hw_list'] = hw
    return HW_SELECT_HW

async def delhomework_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await delhomework_start(update, context)

async def delhomework_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text('Удаление отменено.')
        return ConversationHandler.END
    # callback_data is expected like 'hw_del_<id>'
    if not query.data.startswith('hw_del_'):
        await query.edit_message_text('Неверный выбор.')
        return ConversationHandler.END
    hw_id = int(query.data.replace('hw_del_', ''))
    # find item for display
    hw = context.user_data.get('hw_list', [])
    found = next(((s, t, d) for _id, s, t, d in hw if _id == hw_id), None)
    if not found:
        await query.edit_message_text('Задание не найдено.')
        return ConversationHandler.END
    subject, task, due = found
    context.user_data['hw_delete_id'] = hw_id
    await query.edit_message_text(f'Удалить задание: {subject} — {task}{f" (к {due})" if due else ""}?', reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton('Удалить', callback_data='yes')],
        [InlineKeyboardButton('Отмена', callback_data='cancel')]
    ]))
    return HW_CONFIRM_DELETE

async def delhomework_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'yes':
        hw_id = context.user_data.get('hw_delete_id')
        if hw_id:
            models.delete_homework(hw_id)
            await query.edit_message_text('Задание удалено.')
        else:
            await query.edit_message_text('Ошибка: id не найден.')
    else:
        await query.edit_message_text('Удаление отменено.')
    # clear deleting flag
    context.user_data.pop('deleting_homework', None)
    # clear any lingering hw_list or ids
    context.user_data.pop('hw_list', None)
    context.user_data.pop('hw_delete_id', None)
    return ConversationHandler.END

async def edithomework_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hw = models.get_homework()
    if not hw:
        if update.callback_query:
            await update.callback_query.edit_message_text('Домашние задания отсутствуют.')
        else:
            await update.message.reply_text('Домашние задания отсутствуют.')
        return ConversationHandler.END
    keyboard = []
    for _id, subject, task, due in hw:
        label = f'{subject}: {task[:30]}{("..." if len(task)>30 else "")}'
        keyboard.append([InlineKeyboardButton(label, callback_data=f'hw_edit_{_id}')])
    keyboard.append([InlineKeyboardButton('🔙 Отмена', callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text('Выберите задание для редактирования:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Выберите задание для редактирования:', reply_markup=reply_markup)
    context.user_data['hw_list'] = hw
    return HW_SELECT_HW

async def edithomework_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edithomework_start(update, context)

async def edithomework_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text('Редактирование отменено.')
        return ConversationHandler.END
    # callback_data like 'hw_edit_<id>'
    if not query.data.startswith('hw_edit_'):
        await query.edit_message_text('Неверный выбор.')
        return ConversationHandler.END
    hw_id = int(query.data.replace('hw_edit_', ''))
    hw = context.user_data.get('hw_list', [])
    found = next(((s, t, d) for _id, s, t, d in hw if _id == hw_id), None)
    if not found:
        await query.edit_message_text('Задание не найдено.')
        return ConversationHandler.END
    subject, task, due = found
    context.user_data['hw_edit_id'] = hw_id
    # Show subject selection buttons so user can't mistype subject
    keyboard = [[InlineKeyboardButton(s, callback_data=s)] for s in SUBJECTS]
    keyboard.append([InlineKeyboardButton('Оставить текущий предмет', callback_data='keep_subject')])
    keyboard.append([InlineKeyboardButton('🔙 Отмена', callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Текущий предмет: {subject}\nТекущее задание: {task}{f" (к {due})" if due else ""}\n\nВыберите предмет для обновления или оставьте текущий:', reply_markup=reply_markup)
    # next callback will be handled by edithomework_choose_subject
    return HW_SELECT_SUBJECT

async def edithomework_choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text('Редактирование отменено.')
        return ConversationHandler.END
    hw_id = context.user_data.get('hw_edit_id')
    if not hw_id:
        await query.edit_message_text('Ошибка: id задания не найден. Начните заново.')
        return ConversationHandler.END
    if query.data == 'keep_subject':
        subject = None
    else:
        subject = query.data
    # save chosen subject (None means keep)
    context.user_data['hw_chosen_subject'] = subject
    # prompt for new task text (and optional date)
    await query.edit_message_text('Отправьте новое задание (и при желании дату через ";"):')
    context.user_data['expecting_homework_edit_input'] = True
    return HW_EDIT_INPUT

async def edithomework_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = [p.strip() for p in text.split(';')]
    # parts should be either task; date  OR task alone. Subject comes from previous choice.
    if len(parts) == 2:
        task, due = parts
    elif len(parts) == 1:
        task = parts[0]
        due = None
    else:
        await update.message.reply_text('Неверный формат. Отправьте: задание; YYYY-MM-DD (дата необязательна)')
        return ConversationHandler.END
    hw_id = context.user_data.get('hw_edit_id')
    if not hw_id:
        await update.message.reply_text('Ошибка: id задания не найден. Начните заново.')
        return ConversationHandler.END
    # determine subject: chosen earlier or keep existing
    chosen = context.user_data.get('hw_chosen_subject')
    if chosen is None:
        # keep existing subject from DB
        conn = models.sqlite3.connect(models.DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT subject FROM homework WHERE id=?', (hw_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            subject = row[0]
        else:
            await update.message.reply_text('Ошибка: запись не найдена.')
            return ConversationHandler.END
    else:
        subject = chosen
    models.edit_homework(hw_id, subject, task, due)
    await update.message.reply_text('Задание обновлено.')
    # clear expectation flag
    context.user_data.pop('expecting_homework_edit_input', None)
    context.user_data.pop('hw_chosen_subject', None)
    context.user_data.pop('hw_edit_id', None)
    # clear editing flag
    context.user_data.pop('editing_homework', None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Операция отменена.')
    return ConversationHandler.END
