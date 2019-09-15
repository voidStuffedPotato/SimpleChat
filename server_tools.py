"""
Содержит классы для работы сервера
"""

import datetime
import json
import struct

import sqlalchemy
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DBConnection:
    """
    Класс, служащий для обмена данными с БД
    """

    def __init__(self):
        self.engine = sqlalchemy.create_engine('postgresql+psycopg2://postgres:postgres@localhost/chatdb', echo=False)
        self.sessionmaker = sessionmaker(bind=self.engine)

    @staticmethod
    def _generate_table(name: str):
        """
        Возвращает декларатив sqlalchemy
        name - имя таблицы в БД
        """
        Base = declarative_base()

        class Chat(Base):
            __tablename__ = name
            id = Column(Integer, primary_key=True)
            ip = Column(String)
            sender = Column(String)
            text = Column(String)
            time = Column(String)

            def __repr__(self):
                return '%s[%s] at %s:\n%s' % (self.sender, self.ip, self.time, self.text)

        return Chat

    def return_chat(self, table_name: str):
        """
        Возвращает последние 20 сообщений чата из таблицы в БД, в случае отсутствия возращает 'Сообщений нет'
        table_name - имя таблицы в БД
        """
        session = self.sessionmaker()
        table = self._generate_table(table_name)
        table.metadata.create_all(self.engine)
        count = len(session.query(table).all())
        if count > 20:
            result = session.query(table).all()[count - 20:]
        elif count == 0:
            return 'Сообщений нет'
        else:
            result = session.query(table).all()
        return '\n'.join(str(i) for i in result)

    def insert_message(self, table_name: str, data: dict):
        """
        Вставляет сообщение чата data в таблицу table_name в БД.

        data - dict, должен содержать поля
            'ip': (str)
            'sender': (str)
            'text': (str)
            'time': (str)
        """
        session = self.sessionmaker()
        table = self._generate_table(table_name)
        table.metadata.create_all(self.engine)
        session.add(table(**data))
        session.commit()


class Message:
    """
    Класс - обработчик сообщений между клиентом и сервером
    self.addr - адрес клиента
    self._in_b - буфер для входящих сообщений клиента
    self._out_b - буфер для исходящих сообщений клиента
    self._dict - представление сообщения клиента в виде словаря.
    """

    def __init__(self, addr):
        self.addr = addr
        self._in_b = b''
        self._out_b = b''
        self._header_read = False
        self._json_len = None
        self._dict = dict()
        self.processed = False

    def read(self, sock, server):
        """
        Принимает сообщение от клиента и распаковывает его в self._dict
        """
        recv_data = sock.recv(1024)

        if not recv_data:
            server.sel.unregister(sock)
            sock.close()

        if recv_data and not self._header_read:
            self._json_len = struct.unpack('>I', recv_data[:4])[0]
            recv_data = recv_data[4:]
            self._header_read = True

        self._in_b += recv_data

        if self._json_len is not None and len(self._in_b) >= self._json_len:
            self._dict = json.loads(self._in_b.decode('utf-8'), encoding='utf-8')

    def _process(self):
        """
        Записывает в self._out_b ответ, содержащий последние 20 сообщений в БД,
        находяющихся в таблице self._dict['chat_name'].
        Если клиент предварительно отправил сообщение чата в БД, оно будет включено в ответ.
        """
        if self._dict['mode'] == 'send':
            curr_time = datetime.datetime.now().strftime('%d-%m-%y %H:%M')
            DBConnection().insert_message(self._dict['chat_name'],
                                          dict(ip=self.addr[0], sender=self._dict['sender'],
                                               text=self._dict['text'], time=curr_time))

        response = DBConnection().return_chat(self._dict['chat_name'])

        json_part = json.dumps(dict(chat_name=self._dict['chat_name'], text=response), ensure_ascii=False)
        self._out_b = struct.pack('>I', len(json_part)) + json_part.encode('utf-8')
        self.processed = True

    def write(self, sock, server):
        """
        Отправляет в sock содержимое self._out_b
        """
        if not self.processed:
            self._process()
        if self._out_b:
            sent = sock.send(self._out_b)
            print(f'Sent {sent} bytes')
            self._out_b = self._out_b[sent:]
        else:
            server.sel.unregister(sock)
            sock.close()
