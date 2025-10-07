import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
DB_PATH = os.getenv('DB_PATH', 'data/bot.db')

def add_schedule(day, lesson, time):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('INSERT INTO schedule (day, lesson, time) VALUES (?, ?, ?)', (day, lesson, time))
	conn.commit()
	conn.close()

def get_schedule():
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('SELECT day, lesson, time FROM schedule ORDER BY id')
	rows = cur.fetchall()
	conn.close()
	return rows

def delete_schedule(schedule_id):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('DELETE FROM schedule WHERE id = ?', (schedule_id,))
	conn.commit()
	conn.close()

def edit_schedule(schedule_id, day, lesson, time):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('UPDATE schedule SET day = ?, lesson = ?, time = ? WHERE id = ?', (day, lesson, time, schedule_id))
	conn.commit()
	conn.close()

# Аналогично для домашки
def add_homework(subject, task, due_date):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('INSERT INTO homework (subject, task, due_date) VALUES (?, ?, ?)', (subject, task, due_date))
	conn.commit()
	conn.close()

def get_homework():
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('SELECT subject, task, due_date FROM homework ORDER BY id')
	rows = cur.fetchall()
	conn.close()
	return rows

def delete_homework(homework_id):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('DELETE FROM homework WHERE id = ?', (homework_id,))
	conn.commit()
	conn.close()

def edit_homework(homework_id, subject, task, due_date):
	conn = sqlite3.connect(DB_PATH)
	cur = conn.cursor()
	cur.execute('UPDATE homework SET subject = ?, task = ?, due_date = ? WHERE id = ?', (subject, task, due_date, homework_id))
	conn.commit()
	conn.close()
