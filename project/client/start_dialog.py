from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel , qApp
from PyQt5.QtCore import Qt


class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Привет!')
        self.setFixedSize(210, 120)

        self.label = QLabel('Введите логин и пароль:', self)
        self.label.move(10, 10)
        self.label.setAlignment(Qt.AlignJustify)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(190, 20)
        self.client_name.move(10, 30)
        self.client_name.setPlaceholderText('Введите логин:')

        self.client_password = QLineEdit(self)
        self.client_password.setFixedSize(190, 20)
        self.client_password.move(10, 60)
        self.client_password.setEchoMode(QLineEdit.Password)
        self.client_password.setPlaceholderText('Введите пароль:')

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 90)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(110, 90)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text() and self.client_password.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
