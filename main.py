import os
import threading
from typing import List, Dict, Any

import telebot
from dotenv import load_dotenv
from datetime import datetime
import mysql.connector

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
con = mysql.connector.connect(
    host=os.environ.get("HOST"),
    user=os.environ.get("USERNAME"),
    password=os.environ.get("PASSWORD"),
    database=os.environ.get("DB"),
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


def write_inbox(message, state, status):
    global con
    cur = con.cursor()
    cur.execute("INSERT INTO inbox VALUES(%s, %s, %s, %s, %s, %s, %s)",
                (message.message_id,
                 message.from_user.id,
                 timestamp_to_time(message.date),
                 message.from_user.username,
                 message.text,
                 state,
                 int(status)))


def display_data_inbox(message):
    global con
    cur = con.cursor()

    cur.execute("SELECT * FROM inbox ORDER BY id DESC")

    inboxs = cur.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    write_inbox(message, "display_data_outbox", 1)
    write_outbox(bot.reply_to(message, response or 'tidak ada data gan'))


def display_data_outbox(message):
    global con
    cur = con.cursor()

    cur.execute("SELECT * FROM outbox ORDER BY id DESC")

    inboxs = cur.fetchall()
    response = "\n----\n".join(["\n".join([str(property) for property in inbox]) for inbox in inboxs])

    write_inbox(message, "display_data_outbox", 1)
    write_outbox(bot.reply_to(message, response or 'tidak ada data gan'))


def delete_all_data_inbox(message):
    global con
    cur = con.cursor()

    cur.execute("DELETE FROM inbox WHERE 1")
    con.commit()

    write_inbox(message, "delete_all_data_inbox", 1)
    write_outbox(bot.reply_to(message, "inbox terhapus gan"))


def delete_all_data_outbox(message):
    global con
    cur = con.cursor()

    cur.execute("DELETE FROM outbox WHERE 1")
    con.commit()

    write_inbox(message, "delete_all_data_outbox", 1)
    write_outbox(bot.reply_to(message, "outbox terhapus gan"))

def display_data_student_by_nim(message):
    global con
    cur = con.cursor()

    list_students = [
        {"nim":"2105551019", "name":"andika"},
        {"nim": "2105551020", "name": "younglex"},
        {"nim": "2105551021", "name": "bin"}
    ]

    cur.execute("CREATE TABLE IF NOT EXISTS student(id INT AUTO_INCREMENT PRIMARY KEY, nim varchar(255), name varchar(255))")
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()

    if (not students):
        for index, student in enumerate(list_students):
            cur.execute("INSERT INTO student VALUES(%s, %s, %s)",
                        (index + 1, student["nim"], student["name"]))
        con.commit()

    cur.execute("SELECT state, status FROM inbox WHERE usertoken=%s ORDER BY id DESC LIMIT 1",
                (message.from_user.id,))
    inbox = cur.fetchone()

    if (inbox[0] != "display_data_student_by_nim"):
        write_inbox(message, "display_data_student_by_nim", 0)
        write_outbox(bot.reply_to(message, "masukin nim yang lo inginkan"))
        cur.close()
        return

    # check is input valid
    if (message.text.isnumeric()):
        cur.execute("SELECT * FROM student WHERE nim=%s", (int(message.text),))
        student = cur.fetchone()
        response = "\n".join([str(property) for property in student])
        write_inbox(message, "display_data_student_by_nim", 1)
        write_outbox(bot.reply_to(message, response or 'tidak ada data mahasiswa yang seperti itu ngab'))
        cur.close()
        return

    write_inbox(message, "display_data_student_by_nim", 0)
    write_outbox(bot.reply_to(message, "input salah tuh ngab coba lagi"))
    cur.close()
    return

def retrieve_message(message):
    write_inbox(message, "retrieve_message", 1)
    write_outbox(bot.reply_to(message, "yeyeyeye"))


def display_menu(message, functions):
    global con
    cur = con.cursor()

    # check is input valid
    if (message.text.isdigit() and int(message.text) <= len(functions) and int(message.text) > 0):
        for i, menu in enumerate(functions):
            if (i+1 == int(message.text)):
                print("input is valid and function %s is executed" % menu["label"])
                threading.Thread(target=menu["ref"], args=(message,)).start()
                return

    print("display menu")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS menu(id INT AUTO_INCREMENT PRIMARY KEY, no INT, label varchar(255), description TEXT)")
    cur.execute("SELECT * FROM menu ORDER BY id DESC")
    fetched_functions = cur.fetchall()

    if (not fetched_functions):
        for index, menu in enumerate(functions):
            cur.execute("INSERT INTO menu VALUES(%s, %s, %s, %s)",
                        (index + 1, index + 1, functions[index]["label"], functions[index]["description"]))
        con.commit()

        cur.execute("SELECT * FROM menu ORDER BY id DESC")
        fetched_functions = cur.fetchall()

    response = "\n----\n".join(["\n".join([str(property) for property in menu]) for menu in fetched_functions])

    write_inbox(message, "display_menu", 0)
    write_outbox(bot.reply_to(message, response or 'tidak ada data menu gan'))
    cur.close()
    return


@bot.message_handler(func=lambda message: True)
def auto_response(message):
    global con
    cur = con.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS inbox(id INT AUTO_INCREMENT PRIMARY KEY, usertoken varchar(255), created_at varchar(255), username varchar(255), message TEXT, state varchar(255), status BOOLEAN)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS outbox(id INT AUTO_INCREMENT PRIMARY KEY, usertoken varchar(255), created_at varchar(255), username varchar(255), message TEXT)")

    functions = [
        {"label": "display_data_student_by_nim", "description":"menampilkan informasi mahasiswa berdasarkan id", "ref": display_data_student_by_nim},
        {"label": "retrieve_data", "description": "menampilkan pesang singkat", "ref": retrieve_message},
        {"label": "display_data_inbox", "description": "menampilkan data inbox yang telah masuk",
         "ref": display_data_inbox},
        {"label": "display_data_outbox", "description": "menampilkan data outbox yang telah masuk",
         "ref": display_data_outbox},
        {"label": "delete_all_data_inbox", "description": "menghapus semua data inbox yang telah masuk",
         "ref": delete_all_data_inbox},
        {"label": "delete_all_data_outbox", "description": "menghapus semua data outbox yang telah masuk",
         "ref": delete_all_data_outbox}
    ]

    cur.execute("SELECT state, status FROM inbox WHERE usertoken=%s ORDER BY id DESC LIMIT 1",
                (message.from_user.id,))
    inbox = cur.fetchone()

    # check is command match
    for function in functions:
        if (message.text == (function["label"])):
            threading.Thread(target=function["ref"], args=(message,)).start()
            return

    # check is previous message is not solved
    if (inbox):
        for function in functions:
            if (inbox[0] == function["label"] and inbox[1] == 0):
                threading.Thread(target=function["ref"], args=(message,)).start()
                return

    # just execute default function
    threading.Thread(target=lambda: display_menu(message, functions)).start()
    return


bot.infinity_polling()
