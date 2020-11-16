"""
Содержит класс-клиент
"""

import json
import socket
import struct

HOST = '127.0.0.1'
PORT = 55555


class Client:
    def __init__(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname

    def get_chat(self, chat_name: str):
        """
        Возвращает содержимое чата на сервере
        chat_name: имя чата (таблицы в БД)
        """
        with socket.socket() as sock:
            sock.connect((self.host, self.port))
            data = dict(mode='read', chat_name=chat_name)
            message = self._pack_message(data)
            sock.sendall(message)
            received = self._recv_message(sock)
        return json.loads(received[4:].decode('utf-8'))['text']

    def send_message(self, chat_name: str, text: str):
        """
        Отправляет сообщение в чат на сервере и возращает содержимое чата
        chat_name: имя чата (таблицы в БД)
        text: текст сообщения
        """
        with socket.socket() as sock:
            sock.connect((self.host, self.port))
            data = dict(mode='send', chat_name=chat_name, text=text, sender=self.nickname)
            message = self._pack_message(data)
            sock.sendall(message)
            received = self._recv_message(sock)
        return json.loads(received[4:].decode('utf-8'))['text']

    @staticmethod
    def _pack_message(_dict):
        """
        Запаковывает сообщение серверу и возращает его
        _dict: словарь, содержащий сообщение. Описание приведено в модуле server.py
        """
        json_part = json.dumps(_dict, ensure_ascii=False)
        message = struct.pack('>I', len(json_part)) + json_part.encode('utf-8')
        return message

    @staticmethod
    def _recv_message(sock):
        """
        Возвращает сообщение, полученное из сокета sock
        """
        in_b = b''
        while True:
            recv_data = sock.recv(1024)
            if not recv_data:
                break
            else:
                in_b += recv_data
        return in_b


if __name__ == '__main__':
    CLIENT = Client(HOST, PORT, 'sample_name')
    print(CLIENT.send_message('common', 'Нужно больше золота\n'*10))
