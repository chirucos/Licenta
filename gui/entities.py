from crawler.settings import mysql_conn

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QApplication, QWidget, QDesktopWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QComboBox
from PyQt5.QtWidgets import QSizePolicy, QLineEdit, QTextBrowser, QDialog
from PyQt5.QtWidgets import QListWidget

import sys

class Entities(QDialog):


    def __init__(self, parentW=None):
        super(Entities, self).__init__()

        self.setWindowTitle("Entitati")

        self.parentW = parentW

        self.initUI()


    def initUI(self):
        # self.setGeometry(1030, 300, 800, 640)

        self.createList()

        self.show()






if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Entities()
    sys.exit(app.exec_())