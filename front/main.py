# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from app.utils.constants import AppConstants
from app.tabs.config_tab import ConfigTab
from app.tabs.testing_tab import TestingTab
from app.tabs.report_tab import ReportTab

from back_pyd.vram_backend import Vram

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Инициализация Backend
        self.vram = Vram(AppConstants.DEFAULT_WORD_COUNT)

        self.setWindowTitle(AppConstants.WINDOW_TITLE)
        self.resize(AppConstants.WINDOW_WIDTH, AppConstants.WINDOW_HEIGHT)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.setup_tabs()
        
        # Настраиваем стили
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

    def setup_tabs(self):
        self.report_tab = ReportTab()
        self.config_tab = ConfigTab(self.vram)
        self.testing_tab = TestingTab(self.vram, self.report_tab)
        
        # СВЯЗКА ВНУТРИ: Когда ConfigTab создает новую память,
        # передаем её в TestingTab
        self.config_tab.vram_changed.connect(self.testing_tab.set_new_vram)
        
        self.tabs.addTab(self.config_tab, "Конфигурация")
        self.tabs.addTab(self.testing_tab, "Тестирование")
        self.tabs.addTab(self.report_tab, "Результаты")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())