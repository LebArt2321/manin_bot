import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from bot.db.init_db import init_db, clear_db
from bot.schedule import show_schedule, clear_schedule
from bot.schedule import addschedule_start, addschedule_day, addschedule_lesson, addschedule_name, addschedule_cancel
from bot.schedule import delschedule_start, delschedule_day, delschedule_lesson, delschedule_confirm, delschedule_cancel
from bot.schedule import editschedule_start, editschedule_day, editschedule_lesson, editschedule_name, editschedule_cancel


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# ...existing code...


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот-платформа для расписания и домашки.\n/help - помощь')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Доступные команды:\n/start - начать\n/help - помощь\n/schedule - расписание\n/addschedule - добавить расписание\n/delschedule - удалить расписание\n/editschedule - редактировать расписание') #\n/homework - домашка\n/addhomework - добавить домашку

# ...existing code...



if __name__ == '__main__':
    load_dotenv()
    # init_db()  # Инициализация таблиц
    # clear_db()  # Раскомментировать для очистки БД
    TOKEN = os.getenv('TG_TOKEN')
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('schedule', show_schedule))
    app.add_handler(CommandHandler('clearschedule', clear_schedule))

    async def addschedule_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"addscheduletest called by user {update.effective_user.id}")
        await update.message.reply_text('Тестовый обработчик /addscheduletest сработал!')
    app.add_handler(CommandHandler('addscheduletest', addschedule_test))
    from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
    from bot.schedule import SELECT_DAY, SELECT_LESSON, INPUT_NAME
    from bot.schedule import DEL_SELECT_DAY, DEL_SELECT_LESSON, DEL_CONFIRM
    from bot.schedule import EDIT_SELECT_DAY, EDIT_SELECT_LESSON, EDIT_INPUT_NAME
    addschedule_conv = ConversationHandler(
        entry_points=[CommandHandler('addschedule', addschedule_start)],
        states={
            SELECT_DAY: [CallbackQueryHandler(addschedule_day)],
            SELECT_LESSON: [CallbackQueryHandler(addschedule_lesson)],
            INPUT_NAME: [CallbackQueryHandler(addschedule_name)]
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
    # ...existing homework handlers...
    app.run_polling()
