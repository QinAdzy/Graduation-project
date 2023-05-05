from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QPushButton
from PyQt5.QtCore import Qt

class MyTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.initUI()

    def initUI(self):
        self.setRowCount(3)
        self.setColumnCount(2)

        # 将按钮添加到单元格中
        button1 = QPushButton("Button 1")
        self.setCellWidget(0, 0, button1)
        button1.clicked.connect(self.handleButtonClicked)

        button2 = QPushButton("Button 2")
        self.setCellWidget(1, 0, button2)
        button2.clicked.connect(self.handleButtonClicked)

        button3 = QPushButton("Button 3")
        self.setCellWidget(2, 0, button3)
        button3.clicked.connect(self.handleButtonClicked)

    def handleButtonClicked(self):
        # 获取发送信号的按钮
        button = self.sender()

        # 获取按钮所在的单元格
        index = self.indexAt(button.pos())

        # 获取单元格的行号
        row = index.row()

        print(f"The button in row {row} was clicked.")

if __name__ == '__main__':
    app = QApplication([])
    table = MyTable(3, 2)
    table.show()
    app.exec_()
