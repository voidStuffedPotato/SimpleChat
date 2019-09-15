"""
Содержит клиент с графическим интерфейсом
"""

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QApplication, QInputDialog, QMainWindow
from client_tools import Client

TIMEOUT = 2000


class Chat(QWidget):

    def __init__(self):
        super().__init__()
        self.setupUi()
        self.mode = 'receive'
        self.chat_message = ''

    def setupUi(self):
        self.setObjectName("Dialog")
        self.resize(800, 670)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check)

        self.message_edit = QtWidgets.QPlainTextEdit(self)
        self.message_edit.setGeometry(QtCore.QRect(10, 620, 710, 40))
        self.message_edit.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.message_edit.setObjectName("message_edit")

        self.send_button = QtWidgets.QPushButton(self)
        self.send_button.setGeometry(QtCore.QRect(730, 620, 60, 40))
        self.send_button.setObjectName("send_button")
        self.send_button.clicked.connect(self._send_message)

        self.chat_label = QtWidgets.QLabel(self)
        self.chat_label.setGeometry(QtCore.QRect(10, 10, 780, 600))
        self.chat_label.setText("")
        self.chat_label.setObjectName("chat_label")

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Добро пожаловать"))
        self.send_button.setText(_translate("Dialog", "Отправить"))

    def launch(self, chat_name, nickname, host, port):
        if '&' in chat_name:
            arr = chat_name.split('&')
            arr.remove(nickname)
            title = 'Ваша переписка с ' + arr[0]
        else:
            title = 'Чат ' + chat_name
        self.setWindowTitle(QtCore.QCoreApplication.translate("Dialog", title))

        self.chat_name = chat_name
        self.client = Client(host, port, nickname)

        self.show()

        self.timer.start(TIMEOUT)

    def _check(self):
        if self.mode == 'send':
            displayed_text = self.client.send_message(self.chat_name, self.chat_message)
            self.chat_message = ''
            self.mode = 'receive'
        else:
            displayed_text = self.client.get_chat(self.chat_name)

        self.chat_label.clear()
        self.chat_label.setText(displayed_text)

    def _send_message(self):
        msg = self.message_edit.document().toPlainText()
        if msg:
            self.message_edit.clear()
            self.chat_message = msg
            self.mode = 'send'

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nickname = None
        self.mode = None
        self.setupUi()
        self.init_chat()

    def setupUi(self):

        self.setObjectName("Dialog")
        self.resize(290, 100)

        self.btn_dm = QtWidgets.QRadioButton(self)
        self.btn_dm.setGeometry(QtCore.QRect(10, 10, 200, 20))
        self.btn_dm.setObjectName("btn_dm")
        self.btn_dm.toggled.connect(lambda: self.set_mode(self.btn_dm))

        self.btn_chat = QtWidgets.QRadioButton(self)
        self.btn_chat.setGeometry(QtCore.QRect(10, 30, 200, 20))
        self.btn_chat.setObjectName("btn_chat")
        self.btn_chat.toggled.connect(lambda: self.set_mode(self.btn_chat))

        self.plainTextEdit = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit.setGeometry(QtCore.QRect(10, 60, 200, 30))
        self.plainTextEdit.setObjectName("plainTextEdit")

        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(220, 60, 60, 30))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.connect_to_chat)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Введите имя пользователя/чата"))
        self.btn_dm.setText(_translate("Dialog", "Личные сообщения"))
        self.btn_chat.setText(_translate("Dialog", "Чат"))
        self.pushButton.setText(_translate("Dialog", "Открыть"))

    def get_nickname(self):
        text, ok = QInputDialog.getText(self, 'Вход',
                                        'Введите ваш никнейм:')

        if ok:
            self.nickname = (str(text))
            self.show()
        else:
            sys.exit(0)

    def init_chat(self):
        text, ok = QInputDialog.getText(self, 'Подключение к серверу',
                                        'Введите адрес сервера в виде HOST,PORT:')

        if ok:
            text = (str(text))
            self.host_addr, self.host_port = text.split(',')[0], int(text.split(',')[1])
            print('Адрес сервера:', self.host_addr,':', self.host_port)
            self.get_nickname()
        else:
            sys.exit(0)

    def set_mode(self, btn):
        if btn.text() == "Чат" and btn.isChecked():
            self.mode = 'chat'
        if btn.text() == "Личные сообщения" and btn.isChecked():
            self.mode = 'dm'

    def connect_to_chat(self):
        chat_name = self.plainTextEdit.document().toPlainText()
        if self.mode and chat_name:
            self.plainTextEdit.document().clear()
            if self.mode == 'dm':
                chat_name = '&'.join(sorted((self.nickname, chat_name)))
            chat.launch(chat_name, self.nickname, self.host_addr, self.host_port)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWidget()
    chat = Chat()
    sys.exit(app.exec_())
