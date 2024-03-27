import os
import telebot
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def timestamp_to_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")

@bot.message_handler(commands=['display_data_inbox'])
def display_data_inbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM inbox ORDER BY id DESC")
        inboxs = res.fetchall()
        response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

        bot.reply_to(message, response or 'tidak ada data gan')

@bot.message_handler(commands=['display_data_outbox'])
def display_data_outbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM outbox ORDER BY id DESC")
        inboxs = res.fetchall()
        response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

        bot.reply_to(message, response or 'tidak ada data gan')

@bot.message_handler(commands=['delete_all_data_inbox'])
def delete_all_data_inbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM inbox WHERE 1")
        con.commit()
        cur.close()
        bot.reply_to(message, "inbox terhapus gan")

@bot.message_handler(commands=['delete_all_data_outbox'])
def delete_all_data_outbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM outbox WHERE 1")
        con.commit()
        cur.close()
        bot.reply_to(message, "outbox terhapus gan")

@bot.message_handler(commands=['hello', 'start', 'hai', 'now'])
def retrieve_message(message):
    with sqlite3.connect("db.sqlite3") as con:
        request = message
        response = bot.reply_to(message, "yeyeyeye")

        cur = con.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS inbox(id INTEGER, usertoken INTEGER, created_at TEXT, username TEXT, message TEXT)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS outbox(id INTEGER, usertoken INTEGER, created_at TEXT, username TEXT, message TEXT)")


        cur.execute("INSERT INTO inbox VALUES(?, ?, ?, ?, ?)",
                    (request.message_id,
                     request.from_user.id,
                     timestamp_to_time(request.date),
                     request.from_user.username,
                     request.text))

        cur.execute("INSERT INTO outbox VALUES(?, ?, ?, ?, ?)",
                    (response.message_id,
                     response.from_user.id,
                     timestamp_to_time(response.date),
                     response.from_user.username,
                     response.text))

        con.commit()
        cur.close()

bot.infinity_polling()