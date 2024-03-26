# encoding: utf-8

import sys, os, logging, platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QLCDNumber, QLabel, QMessageBox, QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

''' 
生成一个基于pyqt5的小程序
界面要求：
1、窗口标题为“Blue”
2、第一行是一个表格，有两列，分别是“Task”和“Time”，表格的内容可以编辑，选中时只能选中一行，不能选中多行，不能选中多列，不能选中多个单元格，表格不显示序号，且内容的大小占满整个表格
3、第二行是一个Lcd Number，格式为“xx:xx:xx”
4、第三行是一个“Start”按钮和一个“Stop”按钮
5、第四行是一个“Add”按钮、一个输入框、一个“Delete”按钮

功能要求：
1、表格能够记录若干条任务以及对应花费时间，时间的格式按“xx:xx:xx”；
2、点击“Add”的时候，添加一条任务，任务名字为输入框中的内容，时间为“00:00:00”；
3、点击“Delete”的时候，删除选中的任务；
4、点击“Start”的时候，对选中的任务开始计时，计时显示到LCD number上，同时“Start”按钮显示为“Pause”；
5、点击“Pause”的时候，暂停计时，计时暂停在LCD number上，同时"start"按钮显示为“Continue”；
6、点击“Continue”的时候，继续计时，计时继续在LCD number上，同时“Continue”按钮显示为“Pause”；
7、点击“Stop”的时候，停止计时，同时将计时累计到对应任务的时间中；
8、切换任务的时候，默认先点击了“Stop”；
'''



# utility functions

def valid_total_time(total_time):
    if len(total_time) != 8:
        return False
    if total_time[2] != ":" or total_time[5] != ":":
        return False
    if not total_time[0:2].isdigit() or not total_time[3:5].isdigit() or not total_time[6:8].isdigit():
        return False
    if int(total_time[0:2]) < 0 or int(total_time[0:2]) > 23:
        return False
    if int(total_time[3:5]) < 0 or int(total_time[3:5]) > 59:
        return False
    if int(total_time[6:8]) < 0 or int(total_time[6:8]) > 59:
        return False
    return True

def get_file_path(file_name):
    if platform.system() == "Windows":
        return file_name
    elif platform.system() == "Darwin":
        current_dir = os.path.dirname(sys.executable)
        if not current_dir:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, file_name)
    elif platform.system() == "Linux":
        logging.error("Linux is not supported")
        assert False

# logging configuration

log_file = get_file_path("blue.log")

if os.path.exists(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()
        if len(lines) > 500:
            lines = lines[-500:]
    with open(log_file, 'w') as file:
        file.writelines(lines)

logging.basicConfig(filename='blue.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class LogStream:
    def write(self, message):
        logging.info(message.strip())
    def flush(self):
        pass

sys.stdout = LogStream()
sys.stderr = LogStream()

# main application

encoding = 'utf-8'

class BlueApp(QMainWindow):
    def __init__(self):
        logging.info("Initializing BlueApp")
        super().__init__()
        self.init_window()
        self.init_menu()
        self.init_label()
        self.init_table()
        self.init_lcd()
        self.init_button()
        self.init_lineedit()
        self.init_layout()
        self.init_style()
        logging.info("BlueApp initialized")
        self.tasks = []
        self.current_task = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
    
    def quick_open(self):
        logging.info("Performing quick open")
        tasks_file = get_file_path("tasks.tmpl")
        logging.info(f"Opening tasks from {tasks_file}")
        try:
            with open(tasks_file, "r", encoding=encoding) as file:
                for i, line in enumerate(file):
                    parts = line.strip().split(" ")
                    if len(parts) != 2 or not valid_total_time(parts[1]):
                        logging.error(f"Invalid line: {i + 1}")
                        continue
                    task = {"name": parts[0], "time": 0, "total_time": parts[1]}
                    self._add_task(task)
            logging.info("Tasks opened")
        except FileNotFoundError:
            logging.error(f"File not found: {tasks_file}")

    def quick_save(self):
        logging.info("Performing quick save")
        tasks_file = get_file_path("tasks.tmpl")
        logging.info(f"Saving tasks to {tasks_file}")
        try:
            with open(tasks_file, "w", encoding=encoding) as file:
                for task in self.tasks:
                    file.write(f"{task['name']} {task['total_time']}\n")
            logging.info("Tasks saved")
        except FileNotFoundError:
            logging.error(f"File not found: {tasks_file}")

    def clear(self):
        logging.info("Clearing tasks")
        self.stop_timer()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.tasks = []

    def about(self):
        logging.info("Displaying about dialog")
        text = "Blue is a simple task timer application.Click <a href='https://github.com/BerneXJ'>here</a> for more information."
        QMessageBox.about(self, "About", text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_task()
        elif event.key() == Qt.Key_Return:
            self.add_task()

    def closeEvent(self, event):
        logging.info("Closing BlueApp")
        text = "Save tasks before quitting?"
        reply = QMessageBox.question(self, "Message", text, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.quick_save()
            event.accept()
        elif reply == QMessageBox.Cancel:
            event.ignore()
            return
        logging.info("BlueApp closed")
        event.accept()    

    def init_window(self):
        logging.info("Initializing window")
        self.setWindowTitle("Blue")
        self.setFixedSize(280, 450)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

    def init_menu(self):
        logging.info("Initializing menu")
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        quick_open_action = QAction("Quick Open", self)
        quick_open_action.setShortcut("Ctrl+O")
        quick_open_action.triggered.connect(self.quick_open)
        file_menu.addAction(quick_open_action)
        quick_save_action = QAction("Quick Save", self)
        quick_save_action.setShortcut("Ctrl+S")
        quick_save_action.triggered.connect(self.quick_save)
        file_menu.addAction(quick_save_action)
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self.clear)
        file_menu.addAction(clear_action)

        about_menu = menu_bar.addMenu("About")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about)
        about_menu.addAction(about_action)

    def init_label(self):
        logging.info("Initializing label")
        self.task_label = QLabel("Task")
        self.time_label = QLabel("Time")
        self.task_label.setAlignment(Qt.AlignCenter)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.task_label.setFixedHeight(12)
        self.time_label.setFixedHeight(12)

    def init_table(self):
        logging.info("Initializing table")
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        if platform.system() == "Windows":
            self.table.setFixedHeight(int(self.size().height() * 0.5))
        elif platform.system() == "Darwin":
            self.table.setFixedHeight(int(self.size().height() * 0.6))
        elif platform.system() == "Linux":
            self.table.setFixedHeight(int(self.size().height() * 0.6))
    
    def init_lcd(self):
        logging.info("Initializing LCD")
        self.lcd = QLCDNumber()
        self.lcd.setDigitCount(8)
        self.lcd.display("00:00:00")

    def init_button(self):
        logging.info("Initializing buttons")
        self.start_pause_continue_button = QPushButton("Start")
        self.start_pause_continue_button.clicked.connect(self.start_pause_continue_timer)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_timer)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_task)
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_task)

    def init_lineedit(self):
        logging.info("Initializing line edit")
        self.task_input = QLineEdit()

    def init_layout(self):
        logging.info("Initializing layout")
        layout = QVBoxLayout()

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.task_label)
        label_layout.addWidget(self.time_label)

        layout.addLayout(label_layout)

        layout.addWidget(self.table)
        layout.addWidget(self.lcd)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_pause_continue_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.add_button)
        input_layout.addWidget(self.task_input)

        layout.addLayout(input_layout)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def init_style(self):
        logging.info("Initializing style")
        self.setWindowOpacity(0.8)
        color1 = "rgb(240, 240, 240)"
        color2 = "rgb(113, 133, 215)"
        self.setStyleSheet(f"QMainWindow {{ background-color: {color1}; }}")
        self.menuBar().setStyleSheet(f"QMenuBar {{ background-color: {color1}; }}")
        self.task_label.setStyleSheet(f"QLabel {{ background-color: {color1}; color: black; }}")
        self.time_label.setStyleSheet(f"QLabel {{ background-color: {color1}; color: black; }}")
        self.table.setStyleSheet(f"QTableWidget {{ background-color: {color1}; }} QTableWidget::item:selected {{ background-color: {color2}; color: black; }}")
        self.lcd.setStyleSheet("QLCDNumber { background-color: rgb(240, 240, 240); color: gray; }")
        self.lcd.setSegmentStyle(QLCDNumber.Flat)
        font = QFont("Arial", 12)
        if platform.system() == "Windows":
            font = QFont("Microsoft YaHei", 9)
        elif platform.system() == "Darwin":
            font = QFont("PingFang SC", 12)
        elif platform.system() == "Linux":
            font = QFont("WenQuanYi Micro Hei", 12)
        QApplication.setFont(font)

    def update_time(self):
        if self.current_task is not None:
            self.current_task["time"] += 1
            self.lcd.display(self.format_time(self.current_task["time"]))

    def format_time(self, time):
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def add_time(self, total_time, time):
        total_seconds = int(total_time[6:8]) + int(total_time[3:5]) * 60 + int(total_time[0:2]) * 3600
        total_seconds += time
        return self.format_time(total_seconds)

    def start_pause_continue_timer(self):
        if self.start_pause_continue_button.text() == "Start":
            self.start_timer()
        elif self.start_pause_continue_button.text() == "Pause":
            self.pause_timer()
        elif self.start_pause_continue_button.text() == "Continue":
            self.continue_timer()

    def start_timer(self):
        logging.info("Starting timer")
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.current_task = self.tasks[row]
            self.timer.start(1000)
            self.start_pause_continue_button.setText("Pause")
        
    def pause_timer(self):
        logging.info("Pausing timer")
        self.timer.stop()
        self.start_pause_continue_button.setText("Continue")

    def continue_timer(self):
        logging.info("Continuing timer")
        self.timer.start(1000)
        self.start_pause_continue_button.setText("Pause")

    def stop_timer(self):
        logging.info("Stopping timer")
        if self.current_task is not None:
            self.current_task["total_time"] = self.add_time(self.current_task["total_time"], self.current_task["time"])
            self.current_task["time"] = 0
            time_str = self.current_task["total_time"]
            self.table.setItem(self.table.currentRow(), 1, QTableWidgetItem(time_str))
            self.table.item(self.table.currentRow(), 1).setTextAlignment(Qt.AlignCenter)
            self.current_task = None
            self.lcd.display("00:00:00")
            self.start_pause_continue_button.setText("Start")

    def _add_task(self, task):
        self.tasks.append(task)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(task["name"]))
        self.table.setItem(row, 1, QTableWidgetItem(task["total_time"]))
        self.table.item(row, 0).setTextAlignment(Qt.AlignCenter)
        self.table.item(row, 1).setTextAlignment(Qt.AlignCenter)

    def add_task(self):
        logging.info("Adding task")
        task_name = self.task_input.text().strip()
        if " " in task_name:
            QMessageBox.warning(self, "Error", "Task name cannot contain spaces.")
            return
        if task_name:
            task = {"name": task_name, "time": 0, "total_time": "00:00:00"}
            self._add_task(task)
            self.task_input.clear()    

    def _delete_task(self, row):
        self.table.removeRow(row)
        del self.tasks[row]

    def delete_task(self):
        logging.info("Deleting task")
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            self.stop_timer()
            self._delete_task(selected_rows[0].row())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    blue_app = BlueApp()
    blue_app.show()
    sys.exit(app.exec_())