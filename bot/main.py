import threading
import telebot
import time
from telebot import types
import requests
import re
import sqlite3

bot = telebot.TeleBot('2122815268:AAG2zN_9FVW4kP9wDXkReP_TmtjRKexn0aA')
# Интервал проверки в секундах
check_interval = 3600


# Запуск бота, при запуске в первый раз записывает айди пользователя в chat_id.txt для рассылки в monitoring, в базу записываются только сайты
@bot.message_handler(commands=['start'])
def start(message):
    with open('chat_id.txt', 'a+') as chat_id:
        print(message.chat.id, file=chat_id)
    con = sqlite3.connect("database.sqlite3", check_same_thread=False)
    cursor = con.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sites (id int auto_increment primary key, site_name VARCHAR(512))")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uniq ON sites(site_name)")
    con.commit()
    cursor.close()
    con.close()
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
    btn2 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
    btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id,
                     f'Привет {message.from_user.first_name}, это чат-бот для монитора состояния сайтов, я буду оповещать о всех состояних сайта.',
                     reply_markup=markup)


# Обработчик меню
@bot.message_handler(commands=['menu'])
def help_handler(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
    btn2 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
    btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id,
                     'Меню',
                     reply_markup=markup)

    # Обработчик help


@bot.message_handler(commands=['help'])
def help_handler(message):
    markup = types.InlineKeyboardMarkup()
    btn0 = types.InlineKeyboardButton('Написать мне', url='https://t.me/raccoon_meh')
    btn1 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
    btn2 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
    btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
    markup.row(btn0)
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id,
                     'Данный бот следит за состоянием сайтов. Если нужна помощь или обнаружены ошибки, напиши мне.',
                     reply_markup=markup)


# Листинг сайтов
@bot.callback_query_handler(func=lambda callback: True)
def site_list(callback):
    if callback.data == 'site_list':
        con = sqlite3.connect("database.sqlite3", check_same_thread=False)
        cursor = con.cursor()
        cursor.execute('SELECT * FROM sites ')
        list = cursor.fetchall()

        info = ''
        for el in list:
            info += f'{el[1]}\n'

        cursor.close()
        con.close()
        markup = types.InlineKeyboardMarkup()
        btn2 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
        btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
        markup.row(btn2)
        markup.row(btn3)
        bot.send_message(callback.message.chat.id,
                         f'Список сайтов:\n{info}', reply_markup=markup)

    elif callback.data == 'add_site':
        bot.send_message(callback.message.chat.id, 'Отправь полный URL сайта для добавления в базу')
        bot.register_next_step_handler(callback.message, add_success)
    elif callback.data == 'delete_site':
        bot.send_message(callback.message.chat.id, 'Укажи полный URL сайта для удаления')
        bot.register_next_step_handler(callback.message, del_success)


# Добавление нового сайта, проверка уже существующего
def add_success(message):
    site_name = message.text.strip()
    con = sqlite3.connect("database.sqlite3", check_same_thread=False)
    cursor = con.cursor()

    if re.findall("(?P<url>https?://[^\s]+)", site_name):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
        btn2 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
        btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
        markup.row(btn1)
        markup.row(btn2)
        markup.row(btn3)

        try:
            cursor.execute("INSERT INTO sites (site_name) VALUES ('%s')" % (site_name,))

        except sqlite3.Error:
            bot.send_message(message.chat.id, f'{site_name} уже существует', reply_markup=markup)
            con.rollback()

        else:
            bot.send_message(message.chat.id, f'Добавлено: {site_name}', reply_markup=markup)

        con.commit()
        cursor.close()
        con.close()

    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
        btn2 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
        markup.row(btn1)
        markup.row(btn2)
        bot.send_message(message.chat.id, f'Ошибка в адресе или указан не полный url', reply_markup=markup)


# Удаление сайта, провка на наличии при удалении
def del_success(message):
    site_name = message.text.strip()
    if re.findall("(?P<url>https?://[^\s]+)", site_name):

        con = sqlite3.connect("database.sqlite3", check_same_thread=False)
        cursor = con.cursor()

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Добавить сайт', callback_data='add_site')
        btn2 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
        btn3 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
        markup.row(btn1)
        markup.row(btn2)
        markup.row(btn3)

        cursor.execute("SELECT * FROM `sites` WHERE site_name = ?", (site_name,))
        check_delete = cursor.fetchone()

        if check_delete:
            cursor.execute("DELETE FROM `sites` WHERE site_name = ?", (site_name,))
            bot.send_message(message.chat.id, f'Удалено: {site_name}', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f'{site_name} не существует', reply_markup=markup)

        con.commit()
        cursor.close()
        con.close()

    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Удалить сайт', callback_data='delete_site')
        btn2 = types.InlineKeyboardButton('Список сайтов', callback_data='site_list')
        markup.row(btn1)
        markup.row(btn2)
        bot.send_message(message.chat.id, f'Ошибка в адресе или указан не полный url', reply_markup=markup)


# Мониторинг, из базы берутся только сайты, пользователи из файла chat_id
def monitoring():
    while True:
        con = sqlite3.connect("database.sqlite3", check_same_thread=False)
        cursor = con.cursor()
        cursor.execute('SELECT * FROM sites ')
        monitoring_list = cursor.fetchall()

        for el in monitoring_list:
            st_site = requests.get(el[1])
            if st_site.status_code != 200:
                for i in open('chat_id.txt', 'r').readlines():
                    bot.send_message(i, f'Не работает: {el[1]} код ошибки {st_site.status_code}')
                    time.sleep(check_interval)

        cursor.close()
        con.close()


task_thread = threading.Thread(target=monitoring)
task_thread.start()

bot.polling(none_stop=True)
