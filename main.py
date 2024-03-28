import os
import threading

import telebot
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def timestamp_to_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")

def display_data_inbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM inbox ORDER BY id DESC")
        inboxs = res.fetchall()
        response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

        bot.reply_to(message, response or 'tidak ada data gan')

def display_data_outbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM outbox ORDER BY id DESC")
        inboxs = res.fetchall()
        response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

        bot.reply_to(message, response or 'tidak ada data gan')

def delete_all_data_inbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM inbox WHERE 1")
        con.commit()
        cur.close()
        bot.reply_to(message, "inbox terhapus gan")

def delete_all_data_outbox(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM outbox WHERE 1")
        con.commit()
        cur.close()
        bot.reply_to(message, "outbox terhapus gan")

def retrieve_message(message):
    bot.reply_to(message, "yeyeyeye")

@bot.message_handler(func=lambda message: True)
def auto_response(message):
    with sqlite3.connect("db.sqlite3") as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS action(id INTEGER, status INTEGER)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS inbox(id INTEGER, usertoken INTEGER, created_at TEXT, username TEXT, message TEXT, execution_status INTEGER)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS outbox(id INTEGER, usertoken INTEGER, created_at TEXT, username TEXT, message TEXT)")

        cur.execute("INSERT INTO outbox VALUES(?, ?, ?, ?, ?)",
                    (message.message_id,
                     message.from_user.id,
                     timestamp_to_time(message.date),
                     message.from_user.username,
                     message.text))

        con.commit()

        function_list = {
            'retrieve_data': handle_retrieve_message,
            'display_data_inbox': handle_display_data_inbox,
            'display_data_outbox': handle_display_data_outbox,
            'delete_all_data_outbox': handle_delete_all_data_outbox,
            'delete_all_data_inbox': handle_delete_all_data_inbox
        }

        solved = False
        res = cur.execute("SELECT id, execution_status FROM inbox WHERE usertoken=? ORDER BY id DESC LIMIT 1", (message.from_user.id, ))
        inbox = res.fetchone()
        print(inbox[1])
        if(inbox[1] == 1 and message.text.isdigit() and int(message.text) <= len(function_list) and int(message.text) > 0):
            for i, function in enumerate(function_list):
                if(i == int(message.text)):
                    solved = True
                    threading.Thread(target=function_list[function], args=(message,)).start()

        if(not solved):
            cur.execute("UPDATE inbox SET execution_status=0 WHERE id=?", (inbox[0],))
            con.commit()

        basic_menus = [
            {"label": "display_data_inbox", "description": "menampilkan data inbox yang telah masuk"},
            {"label": "display_data_outbox", "description": "menampilkan data outbox yang telah masuk"},
            {"label": "delete_all_data_inbox", "description": "menghapus semua data inbox yang telah masuk"},
            {"label": "delete_all_data_outbox", "description": "menghapus semua data outbox yang telah masuk"}
        ]

        have_response = False

        for i, (k, v) in enumerate(function_list.items()):
            if(message.text == ("/%s" % k)):
                have_response = True
                threading.Thread(target=v, args=(message,)).start()

        flag = 0

        if(not have_response):
            cur.execute("CREATE TABLE IF NOT EXISTS menu(id INTEGER, no INTEGER, label TEXT, description TEXT)")
            con.commit()

            res = cur.execute("SELECT * FROM menu ORDER BY id DESC")
            menus = res.fetchall()

            if(not menus):


                for index, menu in enumerate(basic_menus):
                    cur.execute("INSERT INTO menu VALUES(?, ?, ?, ?)",
                            (index+1, index+1, basic_menus[index]["label"], basic_menus[index]["description"]))

                con.commit()

                res = cur.execute("SELECT * FROM menu ORDER BY id DESC")
                menus = res.fetchall()

            response = "\n----\n".join(["\n".join([str(property) for property in menu]) for menu in menus])

            bot.reply_to(message, response or 'tidak ada data menu gan')

            flag = 1

        cur.execute("INSERT INTO inbox VALUES(?, ?, ?, ?, ?, ?)",
                    (message.message_id,
                     message.from_user.id,
                     timestamp_to_time(message.date),
                     message.from_user.username,
                     message.text,
                     flag))

        con.commit()

        cur.close()

@bot.message_handler(commands=['retrieve_data'])
def handle_retrieve_message(message):
    threading.Thread(target=retrieve_message, args=(message,)).start()

@bot.message_handler(commands=['delete_all_data_outbox'])
def handle_delete_all_data_outbox(message):
    threading.Thread(target=delete_all_data_outbox, args=(message,)).start()

@bot.message_handler(commands=['delete_all_data_inbox'])
def handle_delete_all_data_inbox(message):
    threading.Thread(target=delete_all_data_inbox, args=(message,)).start()

@bot.message_handler(commands=['display_data_outbox'])
def handle_display_data_outbox(message):
    threading.Thread(target=display_data_outbox, args=(message,)).start()

@bot.message_handler(commands=['display_data_inbox'])
def handle_display_data_inbox(message):
    threading.Thread(target=display_data_inbox, args=(message,)).start()

bot.infinity_polling()