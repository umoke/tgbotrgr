import telebot
from telebot import types
import json
import os

TOKEN = '6842079686:AAE__w7hTFo-jVsMQ6olr84k07JdPqXpgUI'
bot = telebot.TeleBot(TOKEN)

ORDERS_FILE = 'orders.json'
orders = {}
admins = [784687121]


def save_orders():
    with open(ORDERS_FILE, 'w') as file:
        json.dump(orders, file, indent=4)


def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as file:
            global orders
            orders = json.load(file)
    else:
        save_orders()


def register_return_request(chat_id, order_id, reason, contact):
    orders[chat_id] = {
        'order_id': order_id,
        'reason': reason,
        'contact': contact,
        'status': 'Рассматриваемый',
        'admin_response': None
    }
    save_orders()


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Добро пожаловать! Используйте /new для отправки запроса на возврат.")


@bot.message_handler(commands=['new'])
def handle_new_request(message):
    msg = bot.send_message(message.chat.id, "Введите номер вашего заказа:")
    bot.register_next_step_handler(msg, process_order_number)

def process_order_number(message):
    chat_id = message.chat.id
    order_id = message.text
    msg = bot.send_message(chat_id, "Укажите причину возврата:")
    bot.register_next_step_handler(msg, process_reason, order_id)


def process_reason(message, order_id):
    chat_id = message.chat.id
    reason = message.text
    msg = bot.send_message(chat_id, "Введите свои контактные данные:")
    bot.register_next_step_handler(msg, process_contact, order_id, reason)


def process_contact(message, order_id, reason):
    chat_id = message.chat.id
    contact = message.text
    register_return_request(chat_id, order_id, reason, contact)
    bot.send_message(chat_id, "Ваш запрос на возврат был отправлен.")

@bot.message_handler(commands=['stats'])
def stats(message):
    chat_id = message.chat.id
    if chat_id in admins:
        bot.send_message(chat_id, "Вот ссылка на статистику: https://0879-154-47-23-73.ngrok-free.app")
    else:
        bot.send_message(chat_id, "У вас нет доступа к статистике.")


@bot.message_handler(commands=['my'])
def user_requests(message):
    chat_id = str(message.chat.id)

    if chat_id in orders:
        order = orders[chat_id]
        response = (
            f"Идентификатор заказа: {order['order_id']}\n"
            f"Причина возврата: {order['reason']}\n"
            f"Контактные данные: {order['contact']}\n"
            f"Статус: {order['status']}\n"
            f"Ответ администратора: {order['admin_response'] or 'Ответа пока нет.'}"
        )
        bot.send_message(chat_id, response)
    else:
        bot.send_message(chat_id, "У вас нет никаких запросов на возврат.")


@bot.message_handler(func=lambda message: message.chat.id in admins)
def admin_commands(message):
    command_parts = message.text.split(maxsplit=2)
    command = command_parts[0]

    if command == '/delete':
        if len(command_parts) < 2:
            bot.reply_to(message, "Используйте: /delete <order_id>")
            return

        order_id_to_delete = command_parts[1]
        order_found = False

        for chat_id in list(orders.keys()):
            if orders[chat_id]['order_id'] == order_id_to_delete:
                del orders[chat_id]
                save_orders()
                bot.reply_to(message, f"Запрос с идентификатором заказа {order_id_to_delete} был удален.")
                order_found = True
                break

        if not order_found:
            bot.reply_to(message, "Заказ не найден.")
    elif command == '/reply':
        if len(command_parts) < 3:
            bot.reply_to(message, "Используйте: /reply <chat_id> <message>")
            return

        chat_id_str = command_parts[1]
        reply_message = command_parts[2]

        chat_id = chat_id_str

        if chat_id in orders:
            orders[chat_id]['admin_response'] = reply_message
            save_orders()
            bot.send_message(chat_id, f"Администратор ответил: {reply_message}")
            bot.reply_to(message, "Ответ отправлен пользователю.")
        else:
            bot.reply_to(message, "Заказ не найден.")
    elif command == '/change':
        if len(command_parts) < 3:
            bot.reply_to(message, "Используйте: /change <order_id> <new_status>")
            return

        order_id_to_change = command_parts[1]
        new_status = command_parts[2]

        order_found = False
        for chat_id, order in orders.items():
            if order['order_id'] == order_id_to_change:
                orders[chat_id]['status'] = new_status
                save_orders()
                bot.send_message(chat_id, f"Статус вашего заказа был обновлен до: {new_status}")
                bot.reply_to(message,
                             f"Статус заказа для идентификатора заказа {order_id_to_change} успешно изменен на {new_status}.")
                order_found = True
                break

        if not order_found:
            bot.reply_to(message, "Заказ с указанным идентификатором заказа не найден.")

    elif command == '/pending':
        pending_orders = [(chat_id, order) for chat_id, order in orders.items() if order['status'] == 'Рассматриваемый']
        if pending_orders:
            response = "Ожидающие рассмотрения запросы:\n\n"
            for chat_id, order in pending_orders:
                response += (
                    f"Идентификатор чата: {chat_id}\n"
                    f"Идентификатор заказа: {order['order_id']}\n"
                    f"Причина: {order['reason']}\n"
                    f"Контакт: {order['contact']}\n"
                    f"Статус: {order['status']}\n\n"
                )
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "Ожидающих запросов нет.")
    else:
        bot.reply_to(message, "Неизвестная команда.")


load_orders()
bot.polling(none_stop=True)
