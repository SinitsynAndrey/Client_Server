from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication, QMessageBox
from PyQt5.QtCore import Qt


class DelUserDialog(QDialog):

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setFixedSize(350, 120)
        self.setWindowTitle('Удаление пользователя')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel(
            'Выберите пользователя для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.all_users_fill()

    def all_users_fill(self):
        self.selector.addItems(self.database.clients_list())

    def remove_user(self):
        self.database.remove_user(self.selector.currentText())
        self.messages.information(self, 'Успех', f'Пользователь {self.selector.currentText()} удалён.')
        if self.selector.currentText() in self.server.user_names:
            sock = self.server.user_names[self.selector.currentText()]
            del self.server.user_names[self.selector.currentText()]
            self.server.remove_client(sock)
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    from database import ServerStorage
    database = ServerStorage('../server_database.db3')
    from core import MessageProcessor
    server = MessageProcessor('127.0.0.1', 7777, database)
    dial = DelUserDialog(database, server)
    dial.show()
    app.exec_()
