"""
Содержит класс сервера

Структура сообщения клиент -> сервер:
    Первые 4 байта - uint, big-endian - длина json-блока.
    Остаток сообщения - json-блок.
    Содержит словарь с ключами:
        mode - 'режим' сообщения.
            'send' - отправить новое сообщение, затем получить сообщения чата из БД, 'read' - только получить.
        chat_name - имя чата (таблицы в БД)
        sender - никнейм отправителя (Только в режиме 'send')
        text - текст отправляемого сообщения (Только в режиме 'send')

Структура сообщения сервер -> клиент:
    Первые 4 байта - uint, big-endian - длина json-блока.
    Остаток сообщения - json-блок.
    Содержит словарь с ключами:
        chat_name - имя чата (таблицы в БД)
        text - содержимое чата
"""

import socket
import selectors
from server_tools import Message

HOST = '127.0.0.1'
PORT = 55555


class Server:
    """
    Класс сервера
    self.sel - селектор, контролирующий обработку сообщений
    """
    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket()
        self.sock.bind((HOST, PORT))
        self.sock.setblocking(False)
        self.sock.listen()
        self.sel.register(self.sock, selectors.EVENT_READ, None)

    def select_loop(self):
        """
        Выбирает сокет, доступный для чтения/записи и вызывет функции, выполняющие необзодимые действия
        """
        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.accept_conn(key.fileobj)
                else:
                    self.service_conn(key, mask)

    def accept_conn(self, sock):
        """
        Подтверждает соединение и регистрирует соответсвующий сокет в селекторе
        """
        conn, addr = sock.accept()
        print('Connection accepted from', addr)
        conn.setblocking(False)
        data = Message(addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data)

    def service_conn(self, key, mask):
        """
        Принимает сообщение от клиента и обрабатывет его
        """
        print('Servicing last connection')
        sock = key.fileobj
        sock.setblocking(False)
        data = key.data
        if mask & selectors.EVENT_READ:
            data.read(sock, self)
        if mask & selectors.EVENT_WRITE:
            data.write(sock, self)


if __name__ == '__main__':
    server = Server()
    server.select_loop()
