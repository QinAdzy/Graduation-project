import sys
from functools import partial

import chardet
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from bert_test.main import Doc_Sim

sys.path.append('..')
from PyQt5 import uic
from PyQt5.Qt import QWidget, QThread
from extract.main import main
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QHeaderView, QDesktopWidget, \
    QAbstractItemView, QPushButton, QVBoxLayout, QTextBrowser, QMessageBox


# 开启一个新窗口
class NewWindow(QWidget):
    def __init__(self, content):
        super().__init__()
        self.setWindowTitle("文件")
        self.setGeometry(0, 0, 800, 500)

        # 获取屏幕大小和中心点
        screen_size = QDesktopWidget().screenGeometry()
        center_point = screen_size.center()
        # 将窗口位置设置为屏幕中心
        self.move(center_point - self.rect().center())

        # 设置TextBrowser呈现样式
        self.text_browser = QTextBrowser(self)
        self.text_browser.setText(content)
        self.text_browser.setStyleSheet("font:15px;")
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.text_browser)
        self.setLayout(self.v_layout)


# 搜索线程
class SearchThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, flag):
        self.flag = flag
        super().__init__()

    def run(self):
        urls_dict = main(w.keywords, self.flag)
        # 发送自定义信号，将结果返回给主线程
        self.finished.emit(urls_dict)


# 文档embedding线程
class EmbThread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        w.obj.embedding()
        w.obj.tf_idf()


# 计算相似度线程
class SimThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, cur_key):
        self.cur_key = cur_key
        super().__init__()

    def run(self):
        sim_dict = w.obj.calculate(self.cur_key)
        # 发送自定义信号，将结果返回给主线程
        self.finished.emit(sim_dict)

# 筛选网页线程
class FilterThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        import_list = w.obj.filter()
        # 发送自定义信号，将结果返回给主线程
        self.finished.emit(import_list)


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.url_dict = {}
        self.init_ui()

    def init_ui(self):
        """
            主窗口设置
        """
        self.ui = uic.loadUi("./myQT.ui")
        self.mainwindow = self.ui
        self.mainwindow.setGeometry(0, 0, 1100, 670)
        # 获取屏幕大小和中心点
        screen_size = QDesktopWidget().screenGeometry()
        center_point = screen_size.center()
        # 将窗口位置设置为屏幕中心
        self.mainwindow.move(center_point - self.mainwindow.rect().center())

        self.mainwindow.setWindowTitle("网页主要内容提取及查重系统")
        self.keywords_qEdit = self.ui.keywords      # 获取搜索框
        self.research_btn = self.ui.search      # 获取搜索按钮
        self.result_qTable = self.ui.result     # 获取结果显示table
        self.fliter_button = self.ui.filter      # 筛选按钮
        self.baidu_radio = self.ui.baidu        # 获取两个单选框
        self.bing_radio = self.ui.bing
        self.flag = "baidu"        # 默认搜索引擎为百度

        """
            修改result_qTable呈现格式
        """
        self.result_qTable.setColumnCount(5)
        self.result_qTable.setHorizontalHeaderLabels(['名称', '链接', '查看', '计算', '相似度'])
        self.result_qTable.setShowGrid(False)
        self.result_qTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_qTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_qTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.result_qTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.result_qTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_qTable.setAlternatingRowColors(True)  # 隔行变色

        hstyle = """QHeaderView::section{
            font:bold 20px;
            color:white;
            background:rgb(120, 146, 98);
        }"""
        # 用三引号可实现字符串
        vstyle = """QHeaderView::section{
            font:bold 15px;
            color:white;
            background:rgb(120, 146, 98);
            width:40px;
        }"""

        # 禁用角落按钮
        self.result_qTable.setCornerButtonEnabled(False)
        self.result_qTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_qTable.horizontalHeader().setStyleSheet(hstyle)
        self.result_qTable.verticalHeader().setStyleSheet(vstyle)

        # 绑定信号与槽函数
        self.research_btn.clicked.connect(self.search)
        self.fliter_button.clicked.connect(self.filterUrl)

    def delrow(self):
        for row, name in self.name_lines.items():
            if name not in self.import_list:
                self.result_qTable.removeRow(row)

    def update_table(self):
        title = list(self.url_dict.keys())
        self.name_lines = {}
        for i, item in enumerate(title):
            name_item = QTableWidgetItem(item)
            self.name_lines[i] = item   # 建立网页与行号的对应表，方便删除
            self.result_qTable.setItem(i, 0, name_item)
            url_item = QTableWidgetItem(self.url_dict[item])
            self.result_qTable.setItem(i, 1, url_item)

            # 添加一个查看按钮
            Button = QPushButton()
            Button.setDown(True)
            Button.setStyleSheet("background:rgb(240, 240, 240,0.5);border:0px;font:18px")
            icon = QIcon('./icon/查看.png')
            Button.setIcon(icon)
            Button.setIconSize(QSize(25, 25))
            Button.clicked.connect(partial(self.open_window, item))
            self.result_qTable.setCellWidget(i, 2, Button)

            # 添加相似度按钮
            Button_sim = QPushButton()
            Button_sim.setDown(True)
            Button_sim.setStyleSheet("background:rgb(240, 240, 240,0.5);border:0px;font:18px")
            icon_sim = QIcon('./icon/环流相似或订正.png')
            Button_sim.setIcon(icon_sim)
            Button_sim.setIconSize(QSize(25, 25))
            Button_sim.clicked.connect(partial(self.update_sim, item))
            self.result_qTable.setCellWidget(i, 3, Button_sim)
            sim_item = QTableWidgetItem('NULL')
            self.result_qTable.setItem(i, 4, sim_item)

    def update_sim(self, cur_key):
        self.simthread = SimThread(cur_key)
        self.simthread.finished.connect(self.handle_sim_result)
        self.simthread.start()

    def handle_sim_result(self, sim_dict):
        for row in range(self.result_qTable.rowCount()):
            name = self.result_qTable.item(row, 0).text()
            sim_item = QTableWidgetItem(str(sim_dict[name]))
            if 0.5 < float(sim_dict[name]) < 0.8:
                sim_item.setForeground(QColor('orange'))
            elif float(sim_dict[name]) > 0.8:
                sim_item.setForeground(QColor('red'))
            else:
                pass
            self.result_qTable.setItem(row, 4, sim_item)

    # 点击搜索后触发事件函数
    def search(self):
        self.keywords = self.keywords_qEdit.text()
        if self.keywords:
            if self.baidu_radio.isChecked():
                self.flag = "baidu"
            else:
                self.flag = "bing"
            self.my_thread = SearchThread(self.flag)  # 创建线程
            self.my_thread.finished.connect(self.handle_result)
            self.my_thread.start()

    # 用于接收多线程的返回值
    def handle_result(self, result):
        # 在这里处理线程返回的结果
        self.url_dict = result
        self.result_qTable.setRowCount(len(self.url_dict))
        self.update_table()

        # 自动执行文档embedding
        QMessageBox.about(self, "提示", "正在执行文档embedding，请等待任务完成")
        self.obj = Doc_Sim(self.keywords, self.flag)
        self.emb_thread = EmbThread()  # 创建线程
        self.emb_thread.finished.connect(self.handle_emb_result)
        self.emb_thread.start()

    def handle_emb_result(self):
        # emb_thread完成后弹出提示框
        QMessageBox.about(self, "提示", "文档embedding已完成！")

    # 打开一个新窗口显示文档内容
    def open_window(self, item):
        item = f'../extract/{self.flag}/{self.keywords}/' + item + '.txt'
        try:
            # 检测文件编码类型
            with open(item, 'rb') as f:
                result = chardet.detect(f.read())
                encoding = result['encoding']
            with open(item, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            raise e
        self.new_window = NewWindow(content)
        self.new_window.show()

    # 筛选重要网页
    def filterUrl(self):
        QMessageBox.about(self, "提示", "正在筛选，请等待")
        self.filter_thread = FilterThread()  # 创建线程
        self.filter_thread.finished.connect(self.handle_filter_result)
        self.filter_thread.start()

    def handle_filter_result(self, import_list):
        self.import_list = import_list
        self.delrow()
        filter_num = self.result_qTable.rowCount()
        QMessageBox.about(self, "提示", f"筛选完成,一共筛选 {filter_num} 个重要网页")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWindow()
    w.ui.show()
    sys.exit(app.exec_())
