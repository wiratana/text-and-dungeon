import os
import threading

import telebot
from dotenv import load_dotenv
from datetime import datetime
import mysql.connector
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
con = mysql.connector.connect(
    host= os.environ.get("HOST"),
    user= os.environ.get("USERNAME"),
    password= os.environ.get("PASSWORD"),
    database= os.environ.get("DB"),
    connect_timeout=60
)

def timestamp_to_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")

def write_outbox(outgoing_message):
    global con
    cur = con.cursor()
    cur.execute("INSERT INTO outbox VALUES(%s, %s, %s, %s, %s)",
                (outgoing_message.message_id,
                 outgoing_message.from_user.id,
                 timestamp_to_time(outgoing_message.date),
                 outgoing_message.from_user.username,
                 outgoing_message.text))

    con.commit()
    cur.close()

def display_data_inbox(message):
    global con
    cur = con.cursor()

    cur.execute("SELECT * FROM inbox ORDER BY id DESC")
    con.commit()
    cur.close()

    inboxs = cur.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    write_outbox(bot.reply_to(message, response or 'tidak ada data gan'))


def display_data_outbox(message):
    global con
    cur = con.cursor()

    cur.execute("SELECT * FROM outbox ORDER BY id DESC")
    con.commit()
    cur.close()

    inboxs = cur.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    write_outbox(bot.reply_to(message, response or 'tidak ada data gan'))


def delete_all_data_inbox(message):
    global con
    cur = con.cursor()
    cur.execute("DELETE FROM inbox WHERE 1")
    con.commit()
    cur.close()

    write_outbox(bot.reply_to(message, "inbox terhapus gan"))


def delete_all_data_outbox(message):
    global con
    cur = con.cursor()

    cur.execute("DELETE FROM outbox WHERE 1")
    con.commit()
    cur.close()

    write_outbox(bot.reply_to(message, "outbox terhapus gan"))


def retrieve_message(message):
    write_outbox(bot.reply_to(message, "yeyeyeye"))


@bot.message_handler(func=lambda message: True)
def auto_response(message):
    global con
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS inbox(id INT AUTO_INCREMENT PRIMARY KEY, usertoken varchar(255), created_at varchar(255), username varchar(255), message TEXT, execution_status INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS outbox(id INT AUTO_INCREMENT PRIMARY KEY, usertoken varchar(255), created_at varchar(255), username varchar(255), message TEXT)")

    menus = [
        {"label": "retrieve_data", "description": "menampilkan pesang singkat", "ref": retrieve_message},
        {"label": "display_data_inbox", "description": "menampilkan data inbox yang telah masuk", "ref": display_data_inbox},
        {"label": "display_data_outbox", "description": "menampilkan data outbox yang telah masuk", "ref": display_data_outbox},
        {"label": "delete_all_data_inbox", "description": "menghapus semua data inbox yang telah masuk", "ref": delete_all_data_inbox},
        {"label": "delete_all_data_outbox", "description": "menghapus semua data outbox yang telah masuk", "ref": delete_all_data_outbox}
    ]

    have_response = False
    solved = False

    for index, menu in enumerate(menus):
        if (message.text == ("/%s" % menus[index]["label"])):
            have_response = True
            threading.Thread(target=menus[index]["ref"], args=(message,)).start()

    if (not have_response):
        cur.execute("SELECT execution_status FROM inbox WHERE usertoken=%s ORDER BY id DESC LIMIT 1",
                          (message.from_user.id,))
        inbox = cur.fetchone()

        if(inbox):
            if (inbox[0] <= 0 and message.text.isdigit() and int(message.text) <= len(menus) and int(message.text) > 0):
                for i, menu in enumerate(menus):
                    if (i == int(message.text)):
                        solved = True
                        threading.Thread(target=menus[i]["ref"], args=(message,)).start()

    if (not solved):
        cur.execute("CREATE TABLE IF NOT EXISTS menu(id INT AUTO_INCREMENT PRIMARY KEY, no INT, label varchar(255), description TEXT)")
        cur.execute("SELECT * FROM menu ORDER BY id DESC")
        fetched_menus = cur.fetchall()

        if (not fetched_menus):
            for index, menu in enumerate(menus):
                cur.execute("INSERT INTO menu VALUES(%s, %s, %s, %s)",
                            (index + 1, index + 1, menus[index]["label"], menus[index]["description"]))
            con.commit()

            res = cur.execute("SELECT * FROM menu ORDER BY id DESC")
            fetched_menus = cur.fetchall()

        response = "\n----\n".join(["\n".join([str(property) for property in menu]) for menu in fetched_menus])

        write_outbox(bot.reply_to(message, response or 'tidak ada data menu gan'))


    cur.execute("INSERT INTO inbox VALUES(%s, %s, %s, %s, %s, %s)",
                (message.message_id,
                 message.from_user.id,
                 timestamp_to_time(message.date),
                 message.from_user.username,
                 message.text,
                 int(solved)))

    con.commit()
    cur.close()

bot.infinity_polling()