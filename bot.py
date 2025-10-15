import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from bot.db.init_db import init_db, clear_db
from bot.schedule import show_schedule, clear_schedule
from bot.schedule import addschedule_start, addschedule_day, addschedule_lesson, addschedule_name, addschedule_cancel, addschedule_add_more, addschedule_start_callback
from bot.schedule import delschedule_start, delschedule_day, delschedule_lesson, delschedule_confirm, delschedule_cancel, delschedule_start_callback
from bot.schedule import editschedule_start, editschedule_day, editschedule_lesson, editschedule_name, editschedule_cancel, editschedule_start_callback
from bot.menu import get_main_menu, get_schedule_menu, get_days_menu, get_admin_menu, get_clear_confirm_menu, help_menu
from telegram import ReplyKeyboardMarkup, KeyboardButton  # Добавьте этот импорт в начало файла


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# ...existing code...

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📋 Меню":
        await update.message.reply_text(
            'Выберите действие:',
            reply_markup=get_main_menu()
        )

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         'Привет! Я бот-платформа для расписания и домашки.\n\nВыберите действие:', 
#         # reply_markup=get_main_menu(),
#         reply_markup=help_menu()
#     )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаем нижнюю клавиатуру
    keyboard = [
        [KeyboardButton("📋 Меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Привет! Я бот-платформа для расписания и домашки.', 
        reply_markup=reply_markup  # Нижняя клавиатура
    )
    
    # Отправляем второе сообщение с inline-кнопками меню
    await update.message.reply_text(
        'Доступные действия:',
        reply_markup=get_main_menu()  # Inline-кнопки
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Доступные команды:\n\n'
        '📅 Расписание - просмотр расписания\n'
        '➕ Добавить урок - добавить новый урок\n'
        '✏️ Редактировать урок - изменить существующий урок\n'
        '🗑️ Удалить урок - удалить урок\n'
        '🧹 Очистить расписание - очистить всё расписание\n\n'
        'Используйте кнопки ниже для удобной навигации!',
        reply_markup=get_main_menu()
    )

# Обработчики кнопок меню
# async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     try:
#         if query.data == "menu_schedule":
#             await query.edit_message_text(
#                 "Выберите действие с расписанием:",
#                 reply_markup=get_schedule_menu()
#             )
#         elif query.data == "show_schedule":
#             # Получаем расписание и отправляем как новое сообщение
#             from bot.models import models
#             schedule = models.get_schedule()
#             if not schedule:
#                 await query.edit_message_text(
#                     '📅 Расписание пусто.\n\nВыберите действие:',
#                     reply_markup=get_schedule_menu()
#                 )
#                 return
        
#             days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
#             LESSON_TIMES = [
#                 "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
#                 "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
#             ]
            
#             def get_lesson_num(time):
#                 for i, t in enumerate(LESSON_TIMES):
#                     if t == time:
#                         return i + 1
#                 return None

#             text = '<b>Расписание на неделю:</b>\n'
#             for day in days:
#                 text += f'\n<b>{day}</b>\n'
#                 lessons = [(get_lesson_num(time), lesson, time) for d, lesson, time in schedule if d == day]
#                 lessons = sorted([l for l in lessons if l[0] is not None], key=lambda x: x[0])
#                 if lessons:
#                     for num, lesson, time in lessons:
#                         text += f'{num}. {lesson} — <b>{time}</b>\n'
#                 else:
#                     text += 'Нет уроков\n'
            
#             await query.edit_message_text(
#                 f"{text}\n\nВыберите действие:",
#                 parse_mode='HTML',
#                 reply_markup=get_schedule_menu()
#             )
#         elif query.data == "show_schedule_day":
#             await query.edit_message_text(
#                 "Выберите день недели:",
#                 reply_markup=get_days_menu()
#             )
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "menu_schedule":
            # Сразу показываем расписание
            from bot.models import models
            schedule = models.get_schedule()
            if not schedule:
                await query.edit_message_text(
                    '📅 Расписание пусто.',
                    reply_markup=get_schedule_menu()
                )
                return
            
            days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
            LESSON_TIMES = [
                "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
                "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
            ]
            
            def get_lesson_num(time):
                for i, t in enumerate(LESSON_TIMES):
                    if t == time:
                        return i + 1
                return None

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
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=get_schedule_menu()
            )
        elif query.data == "menu_add_lesson":
            # await addschedule_start_callback(update, context)
            # Устанавливаем флаг adding_lesson
            context.user_data['adding_lesson'] = True
            # Очищаем другие флаги
            context.user_data.pop('editing_lesson', None)
            context.user_data.pop('deleting_lesson', None)
            await addschedule_start_callback(update, context)
        elif query.data == "add_lesson":
            await addschedule_start_callback(update, context)
        elif query.data == "menu_edit_lesson":
            # Устанавливаем флаг editing_lesson
            context.user_data['editing_lesson'] = True
            # Очищаем другие флаги
            context.user_data.pop('adding_lesson', None)
            context.user_data.pop('deleting_lesson', None)
            await editschedule_start_callback(update, context)
            # await editschedule_start_callback(update, context)
        elif query.data == "edit_lesson":
            await editschedule_start_callback(update, context)
        elif query.data == "menu_delete_lesson":
            # await delschedule_start_callback(update, context)
            # Устанавливаем флаг deleting_lesson
            context.user_data['deleting_lesson'] = True
            # Очищаем другие флаги  
            context.user_data.pop('adding_lesson', None)
            context.user_data.pop('editing_lesson', None)
            await delschedule_start_callback(update, context)
            
        elif query.data == "delete_lesson":
            await delschedule_start_callback(update, context)
        elif query.data == "menu_clear_schedule":
            await query.edit_message_text(
                "⚠️ ВНИМАНИЕ! Это действие удалит ВСЁ расписание безвозвратно!\n\nВы уверены, что хотите продолжить?",
                reply_markup=get_clear_confirm_menu()
            )
        elif query.data == "clear_schedule":
            await query.edit_message_text(
                "⚠️ ВНИМАНИЕ! Это действие удалит ВСЁ расписание безвозвратно!\n\nВы уверены, что хотите продолжить?",
                reply_markup=get_clear_confirm_menu()
            )
        elif query.data == "confirm_clear":
            # Очищаем расписание напрямую
            from bot.models import models
            conn = models.sqlite3.connect(models.DB_PATH)
            cur = conn.cursor()
            cur.execute('DELETE FROM schedule')
            conn.commit()
            conn.close()
            await query.edit_message_text(
                "✅ Расписание полностью очищено!",
                reply_markup=get_main_menu()
            )
        elif query.data == "cancel_clear":
            await query.edit_message_text(
                "Очистка расписания отменена. Выберите действие:",
                reply_markup=get_main_menu()
            )
        elif query.data == "menu_help":
            await query.edit_message_text(
                'Доступные команды:\n\n'
                '📅 Расписание - просмотр расписания\n'
                '➕ Добавить урок - добавить новый урок\n'
                '✏️ Редактировать урок - изменить существующий урок\n'
                '🗑️ Удалить урок - удалить урок\n'
                '🧹 Очистить расписание - очистить всё расписание\n\n'
                'Используйте кнопки ниже для удобной навигации!',
                reply_markup=get_main_menu()
            )
        elif query.data == "back_to_main":
            # Очищаем флаги процессов
            if hasattr(context, 'user_data'):
                context.user_data.pop('adding_lesson', None)
                context.user_data.pop('deleting_lesson', None)
                context.user_data.pop('editing_lesson', None)
            await query.edit_message_text(
                "Главное меню:",
                reply_markup=get_main_menu()
            )
        elif query.data == "back_to_schedule_menu":
            await query.edit_message_text(
                "Выберите действие с расписанием:",
                reply_markup=get_schedule_menu()
            )
        elif query.data.startswith("day_"):
            day = query.data.replace("day_", "")
            # Получаем расписание для конкретного дня
            from bot.models import models
            schedule = models.get_schedule()
            LESSON_TIMES = [
                "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
                "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
            ]
            
            def get_lesson_num(time):
                for i, t in enumerate(LESSON_TIMES):
                    if t == time:
                        return i + 1
                return None

            lessons = [(get_lesson_num(time), lesson, time) for d, lesson, time in schedule if d == day]
            lessons = sorted([l for l in lessons if l[0] is not None], key=lambda x: x[0])
            
            if lessons:
                text = f'<b>{day}</b>\n'
                for num, lesson, time in lessons:
                    text += f'{num}. {lesson} — <b>{time}</b>\n'
            else:
                text = f'<b>{day}</b>\nНет уроков'
            
            await query.edit_message_text(
                f"{text}\n\nВыберите действие:",
                parse_mode='HTML',
                reply_markup=get_schedule_menu()
            )
        # Обработка выбора дня для добавления урока
        elif query.data in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]:
            # Проверяем, находимся ли мы в процессе добавления урока
            if hasattr(context, 'user_data') and 'adding_lesson' in context.user_data:
                await addschedule_day(update, context)
            # Проверяем, находимся ли мы в процессе удаления урока
            elif hasattr(context, 'user_data') and 'deleting_lesson' in context.user_data:
                await delschedule_day(update, context)
            # Проверяем, находимся ли мы в процессе редактирования урока
            elif hasattr(context, 'user_data') and 'editing_lesson' in context.user_data:
                await editschedule_day(update, context)
            else:
                # Если не в процессе, показываем расписание для этого дня
                day = query.data
                from bot.models import models
                schedule = models.get_schedule()
                LESSON_TIMES = [
                    "8:30-9:10", "9:20-10:00", "10:10-10:50", "11:10-11:50", "12:00-12:40", "12:50-13:30",
                    "14:00-14:40", "14:50-15:30", "15:40-16:20", "16:30-17:10", "17:20-18:00", "18:10-18:50"
                ]
                
                def get_lesson_num(time):
                    for i, t in enumerate(LESSON_TIMES):
                        if t == time:
                            return i + 1
                    return None

                lessons = [(get_lesson_num(time), lesson, time) for d, lesson, time in schedule if d == day]
                lessons = sorted([l for l in lessons if l[0] is not None], key=lambda x: x[0])
                
                if lessons:
                    text = f'<b>{day}</b>\n'
                    for num, lesson, time in lessons:
                        text += f'{num}. {lesson} — <b>{time}</b>\n'
                else:
                    text = f'<b>{day}</b>\nНет уроков'
                
                await query.edit_message_text(
                    f"{text}\n\nВыберите действие:",
                    parse_mode='HTML',
                    reply_markup=get_schedule_menu()
                )
        # Обработка выбора времени урока (цифры 0-11)
        elif query.data.isdigit() and 0 <= int(query.data) <= 11:
            if hasattr(context, 'user_data') and 'adding_lesson' in context.user_data:
                await addschedule_lesson(update, context)
            elif hasattr(context, 'user_data') and 'deleting_lesson' in context.user_data:
                await delschedule_lesson(update, context)
            elif hasattr(context, 'user_data') and 'editing_lesson' in context.user_data:
                await editschedule_lesson(update, context)
        # Обработка выбора предмета (названия предметов)
        elif query.data in ["Биология", "Информатика", "Литература", "Алгебра", "РМГ", "Вероятность и статистика",
                           "Обществознание", "История", "География", "Геометрия", "Физкультура", "ОБЗР",
                           "Английский язык", "Физика", "Проект"]:
            if hasattr(context, 'user_data') and 'adding_lesson' in context.user_data:
                await addschedule_name(update, context)
            elif hasattr(context, 'user_data') and 'editing_lesson' in context.user_data:
                await editschedule_name(update, context)
        # Обработка специальных callback-ов
        elif query.data in ['add_more', 'back_to_days', 'finish', 'back_to_lesson', 'back_to_lessons', 'yes', 'back']:
            if hasattr(context, 'user_data') and 'adding_lesson' in context.user_data:
                if query.data in ['add_more', 'back_to_days', 'finish']:
                    await addschedule_add_more(update, context)
                elif query.data == 'back_to_lesson':
                    await addschedule_name(update, context)
            elif hasattr(context, 'user_data') and 'deleting_lesson' in context.user_data:
                if query.data in ['back_to_days', 'back_to_lessons', 'yes']:
                    await delschedule_confirm(update, context)
            elif hasattr(context, 'user_data') and 'editing_lesson' in context.user_data:
                if query.data in ['back_to_lesson', 'back', 'back_to_days']:
                    # Возвращаемся к выбору дня
                    await editschedule_start_callback(update, context)
    except Exception as e:
        print(f"Error in handle_menu_callback: {e}")
        # Если произошла ошибка, отправляем новое сообщение
        await query.message.reply_text(
            "Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_menu()
        )

# ...existing code...



if __name__ == '__main__':
    load_dotenv()
    # init_db()  # Инициализация таблиц
    # clear_db()  # Раскомментировать для очистки БД
    TOKEN = os.getenv('TG_TOKEN')
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Выберите действие с расписанием:",
            reply_markup=get_schedule_menu()
        )
    app.add_handler(CommandHandler('schedule', schedule_command))
    app.add_handler(CommandHandler('clearschedule', clear_schedule))
    app.add_handler(CallbackQueryHandler(handle_menu_callback))

    async def addschedule_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"addscheduletest called by user {update.effective_user.id}")
        await update.message.reply_text('Тестовый обработчик /addscheduletest сработал!')
    app.add_handler(CommandHandler('addscheduletest', addschedule_test))
    from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
    from bot.schedule import SELECT_DAY, SELECT_LESSON, INPUT_NAME, ADD_MORE
    from bot.schedule import DEL_SELECT_DAY, DEL_SELECT_LESSON, DEL_CONFIRM
    from bot.schedule import EDIT_SELECT_DAY, EDIT_SELECT_LESSON, EDIT_INPUT_NAME
    addschedule_conv = ConversationHandler(
        entry_points=[CommandHandler('addschedule', addschedule_start)],
        states={
            SELECT_DAY: [CallbackQueryHandler(addschedule_day)],
            SELECT_LESSON: [CallbackQueryHandler(addschedule_lesson)],
            INPUT_NAME: [CallbackQueryHandler(addschedule_name)],
            ADD_MORE: [CallbackQueryHandler(addschedule_add_more)]
        },
        fallbacks=[CommandHandler('cancel', addschedule_cancel)],
    )
    delschedule_conv = ConversationHandler(
        entry_points=[CommandHandler('delschedule', delschedule_start)],
        states={
            DEL_SELECT_DAY: [CallbackQueryHandler(delschedule_day)],
            DEL_SELECT_LESSON: [CallbackQueryHandler(delschedule_lesson)],
            DEL_CONFIRM: [CallbackQueryHandler(delschedule_confirm)]
        },
        fallbacks=[CommandHandler('cancel', delschedule_cancel)],
    )
    app.add_handler(addschedule_conv)
    app.add_handler(delschedule_conv)
    editschedule_conv = ConversationHandler(
        entry_points=[CommandHandler('editschedule', editschedule_start)],
        states={
            EDIT_SELECT_DAY: [CallbackQueryHandler(editschedule_day)],
            EDIT_SELECT_LESSON: [CallbackQueryHandler(editschedule_lesson)],
            EDIT_INPUT_NAME: [CallbackQueryHandler(editschedule_name)]
        },
        fallbacks=[CommandHandler('cancel', editschedule_cancel)],
    )
    app.add_handler(editschedule_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_button))
    # ...existing homework handlers...
    app.run_polling()
