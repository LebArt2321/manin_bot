import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv('DB_PATH', 'data/bot.db')

def init_db():
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	# Пересоздать таблицу расписания для гарантии структуры
	cur.execute('DROP TABLE IF EXISTS schedule')
	cur.execute('''
		CREATE TABLE schedule (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			day TEXT NOT NULL,
			lesson TEXT NOT NULL,
			time TEXT NOT NULL
		)
	''')
	# Таблица домашки
	cur.execute('''CREATE TABLE IF NOT EXISTS homework (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			subject TEXT NOT NULL,
			task TEXT NOT NULL,
			due_date TEXT
		)
	''')
	conn.commit()
	conn.close()

def clear_db():
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('DELETE FROM schedule')
	cur.execute('DELETE FROM homework')
	conn.commit()
	conn.close()
