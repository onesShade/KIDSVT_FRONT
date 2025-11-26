# app/tabs/testing_tab.py
import os
import glob
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QLabel, QComboBox, QPushButton, QSlider, 
                             QFormLayout, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTimer
from app.widgets.ram_grid import RamGridWidget
from app.utils.constants import AppConstants
from back_pyd.vram_backend import Vram, TestRunner

class TestingTab(QWidget):
    def __init__(self, vram: Vram, report_tab):
        super().__init__()
        self.vram = vram
        self.report_tab = report_tab
        self.runner = None
        self.test_files_map = {}
        
        self.current_error_count = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.do_step)
        
        self.init_ui()
        self.refresh_test_list()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Монитор памяти (Read-Only визуализация)"))
        
        self.ram_grid = RamGridWidget(read_only=True)
        self.ram_grid.update_dimensions(AppConstants.DEFAULT_WORD_COUNT)
        self.setup_grid_labels()
        left_panel.addWidget(self.ram_grid)

        # Легенда
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(0, 10, 0, 0)
        legend_layout.addStretch()
        legend_layout.addWidget(self.create_legend_item(AppConstants.COLOR_BG_DEFAULT, "Ожидание"))
        legend_layout.addWidget(self.create_legend_item(AppConstants.COLOR_BG_ACTIVE, "Запись (Write)"))
        legend_layout.addWidget(self.create_legend_item(AppConstants.COLOR_BG_SUCCESS, "Чтение OK"))
        legend_layout.addWidget(self.create_legend_item(AppConstants.COLOR_BG_ERROR, "Чтение FAIL"))
        legend_layout.addStretch()
        left_panel.addLayout(legend_layout)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QVBoxLayout()

        # Группа 1: Запуск
        grp_setup = QGroupBox("Запуск теста")
        grp_setup_layout = QFormLayout()
        
        self.combo_tests = QComboBox()
        
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.refresh_test_list)
        
        self.btn_load_test = QPushButton("Загрузить / Сброс")
        self.btn_load_test.clicked.connect(self.load_test)
        
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(self.btn_load_test)
        
        grp_setup_layout.addRow("Тест:", self.combo_tests)
        grp_setup_layout.addRow(btn_layout)
        grp_setup.setLayout(grp_setup_layout)

        # Группа 2: Управление
        grp_control = QGroupBox("Управление")
        grp_control_layout = QVBoxLayout()
        
        btns_control = QHBoxLayout()
        self.btn_play_pause = QPushButton("Старт (Авто)")
        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_play_pause.setEnabled(False)
        
        self.btn_step = QPushButton("Шаг")
        self.btn_step.clicked.connect(self.do_step)
        self.btn_step.setEnabled(False)
        
        btns_control.addWidget(self.btn_play_pause)
        btns_control.addWidget(self.btn_step)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Скорость:"))
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(30, 3000) 
        self.slider_speed.setValue(300)
        self.slider_speed.valueChanged.connect(self.update_speed_label)
        
        self.lbl_speed = QLabel("300 оп/мин")
        self.lbl_speed.setFixedWidth(80)
        
        slider_layout.addWidget(self.slider_speed)
        slider_layout.addWidget(self.lbl_speed)
        
        grp_control_layout.addLayout(btns_control)
        grp_control_layout.addLayout(slider_layout)
        grp_control.setLayout(grp_control_layout)

        # Группа 3: Статус
        grp_status = QGroupBox("Статус")
        grp_status_layout = QFormLayout()
        self.lbl_status = QLabel("Нет активного теста")
        self.lbl_last_action = QLabel("-")
        self.lbl_errors = QLabel("0")
        
        font_bold = self.lbl_status.font()
        font_bold.setBold(True)
        self.lbl_status.setFont(font_bold)
        self.lbl_errors.setStyleSheet("color: red; font-weight: bold;")
        
        grp_status_layout.addRow("Состояние:", self.lbl_status)
        grp_status_layout.addRow("Действие:", self.lbl_last_action)
        grp_status_layout.addRow("Найдено ошибок:", self.lbl_errors)
        grp_status.setLayout(grp_status_layout)

        right_panel.addWidget(grp_setup)
        right_panel.addWidget(grp_control)
        right_panel.addWidget(grp_status)
        right_panel.addStretch()

        main_layout.addLayout(left_panel, 6)
        main_layout.addLayout(right_panel, 4)
        
        self.update_speed_label()

    def set_new_vram(self, vram_obj, size):
        """Полная замена объекта памяти на новый из ConfigTab."""
        self.vram = vram_obj
        
        # Сбрасываем текущий раннер, так как он привязан к старой памяти
        self.runner = None
        
        # Обновляем визуальную сетку
        self.ram_grid.update_dimensions(size)
        self.setup_grid_labels()
        self.ram_grid.reset_grid()
        
        # Сбрасываем статус UI
        self.timer.stop()
        self.btn_play_pause.setText("Старт (Авто)")
        self.btn_play_pause.setEnabled(False)
        self.btn_step.setEnabled(False)
        
        self.lbl_status.setText("ПАМЯТЬ ОБНОВЛЕНА")
        self.lbl_last_action.setText("Нажмите 'Загрузить' для старта")
        self.lbl_errors.setText("0")
        self.current_error_count = 0

    def create_legend_item(self, color, text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 10, 0)
        box = QFrame()
        box.setFixedSize(15, 15)
        box.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
        label = QLabel(text)
        layout.addWidget(box)
        layout.addWidget(label)
        return widget

    def setup_grid_labels(self):
        rows = self.ram_grid.rows
        self.ram_grid.table.setHorizontalHeaderLabels([str(15 - i) for i in range(16)])
        self.ram_grid.table.setVerticalHeaderLabels([f"0x{i:04X}" for i in range(rows)])

    def refresh_test_list(self):
        path = AppConstants.TEST_FILES_PATH
        self.combo_tests.clear()
        self.test_files_map.clear()
        if not os.path.exists(path):
            self.combo_tests.addItem("Ресурсы не найдены")
            return
        files = glob.glob(os.path.join(path, "*.kids"))
        if not files:
            self.combo_tests.addItem("Нет тестов (.kids)")
            return
        for f in files:
            base_name = os.path.basename(f)
            clean_name = os.path.splitext(base_name)[0]
            self.test_files_map[clean_name] = f
            self.combo_tests.addItem(clean_name)

    def load_test(self):
        name = self.combo_tests.currentText()
        if name not in self.test_files_map: return
        full_path = self.test_files_map[name]
        
        self.timer.stop()
        self.btn_play_pause.setText("Старт (Авто)")
        
        try:
            # Создаем TestRunner с НОВЫМ self.vram
            self.runner = TestRunner(self.vram, full_path)
            self.current_error_count = 0
            
            self.btn_step.setEnabled(True)
            self.btn_play_pause.setEnabled(True)
            
            self.lbl_status.setText("ГОТОВ")
            self.lbl_last_action.setText("Ожидание запуска...")
            self.lbl_errors.setText("0")
            
            self.ram_grid.reset_grid()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play_pause.setText("Старт (Авто)")
            self.lbl_status.setText("ПАУЗА")
        else:
            self.update_speed_label()
            self.timer.start()
            self.btn_play_pause.setText("Пауза")
            self.lbl_status.setText("ВЫПОЛНЕНИЕ...")

    def update_speed_label(self):
        ops_per_min = self.slider_speed.value()
        self.lbl_speed.setText(f"{ops_per_min} оп/мин")
        
        if ops_per_min > 0:
            interval_ms = int(60000 / ops_per_min)
            self.timer.setInterval(interval_ms)

    def do_step(self):
        if not self.runner: return
        try:
            res = self.runner.step()
            addr = res.i
            
            if res.type == TestRunner.StepResult.Type.WRITE:
                self.lbl_last_action.setText(f"Запись по адресу 0x{addr:04X}")
                self.ram_grid.highlight_row(addr, AppConstants.COLOR_BG_ACTIVE)
                
            elif res.type == TestRunner.StepResult.Type.TEST_SUCCEEDED:
                self.lbl_last_action.setText(f"Чтение 0x{addr:04X} -> OK")
                self.ram_grid.highlight_row(addr, AppConstants.COLOR_BG_SUCCESS)
                
            elif res.type == TestRunner.StepResult.Type.TEST_FAILED:
                self.current_error_count += 1
                self.lbl_errors.setText(str(self.current_error_count))
                self.lbl_last_action.setText(f"Чтение 0x{addr:04X} -> ОШИБКА")
                self.ram_grid.highlight_row(addr, AppConstants.COLOR_BG_ERROR)
                
            elif res.type == TestRunner.StepResult.Type.ENDED:
                self.finish_test()

        except Exception as e:
            self.timer.stop()
            print(f"Error during step: {e}")

    def finish_test(self):
        self.timer.stop()
        self.btn_play_pause.setText("Старт (Авто)")
        self.btn_play_pause.setEnabled(False)
        self.btn_step.setEnabled(False)
        
        self.lbl_status.setText("ЗАВЕРШЕН")
        self.lbl_last_action.setText("Тест окончен")
        
        errors = self.runner.detected_errors()
        err_count = len(errors)
        test_name = self.combo_tests.currentText()
        
        self.lbl_errors.setText(str(err_count))
        
        for addr in errors:
            self.ram_grid.highlight_row(addr, AppConstants.COLOR_BG_ERROR)
        
        self.report_tab.append_formatted_result(test_name, errors)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Результат теста")
        if err_count == 0:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"<h3 style='color:green;'>Тест успешно пройден!</h3>")
            msg.setInformativeText(f"Алгоритм: <b>{test_name}</b><br>Ошибок не обнаружено.")
        else:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"<h3 style='color:red;'>Тест провален!</h3>")
            msg.setInformativeText(f"Алгоритм: <b>{test_name}</b><br>Событий ошибок: <b>{err_count}</b>")
        msg.exec()