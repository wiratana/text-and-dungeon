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
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM inbox ORDER BY id DESC")
    inboxs = res.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    bot.reply_to(message, response)

@bot.message_handler(commands=['display_data_outbox'])
def display_data_outbox(message):
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM outbox ORDER BY id DESC")
    inboxs = res.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    bot.reply_to(message, response)

@bot.message_handler(commands=['hello'])
def retrieve_message(message):
    request = message
    response = bot.reply_to(message, "yeyeyeye")

    con = sqlite3.connect("db.sqlite3")
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
    con.close()

bot.infinity_polling()