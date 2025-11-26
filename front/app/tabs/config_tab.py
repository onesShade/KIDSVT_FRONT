# app/tabs/config_tab.py
import json
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QPushButton, QRadioButton, QButtonGroup, QComboBox, 
                             QListWidget, QFileDialog, QFormLayout, QSpinBox, 
                             QMessageBox, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal # <--- Добавлен pyqtSignal
from app.widgets.ram_grid import RamGridWidget
from app.utils.constants import AppConstants
from back_pyd.vram_backend import Vram

class ConfigTab(QWidget):
    # Сигнал, который отправляет новый объект Vram и его новый размер
    vram_changed = pyqtSignal(object, int)

    FAULT_TRANSLATIONS = {
        "NO": "Нет ошибки",
        "STUCK_AT_0": "Залипание в 0",
        "STUCK_AT_1": "Залипание в 1",
        "TRANSITION_0_TO_1": "Переход 0->1",
        "TRANSITION_1_TO_0": "Переход 1->0",
        "WRITE_OR_READ_DESTRUCTIVE_0": "Деструктивная запись/чтение 0",
        "WRITE_OR_READ_DESTRUCTIVE_1": "Деструктивная запись/чтение 1",
        "INCORRECT_READ_0": "Некорректное чтение 0",
        "INCORRECT_READ_1": "Некорректное чтение 1",
        "DECEPTIVE_READ_0": "Обманчивое чтение 0",
        "DECEPTIVE_READ_1": "Обманчивое чтение 1"
    }

    def __init__(self, vram_instance: Vram):
        super().__init__()
        self.vram = vram_instance
        
        self.ru_to_type = {}
        for name, member in Vram.ErrType.__members__.items():
            if name in self.FAULT_TRANSLATIONS:
                ru_name = self.FAULT_TRANSLATIONS[name]
                self.ru_to_type[ru_name] = member

        self.init_ui()
        self.apply_grid_settings()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QVBoxLayout()
        
        tools_layout = QHBoxLayout()
        mem_group = QGroupBox("Размер памяти")
        mem_layout = QHBoxLayout()
        self.spin_words = QSpinBox()
        self.spin_words.setRange(1, 1024)
        self.spin_words.setValue(AppConstants.DEFAULT_WORD_COUNT)
        self.spin_words.setPrefix("Слов (16bit): ")
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self.on_recreate_vram)
        mem_layout.addWidget(self.spin_words)
        mem_layout.addWidget(btn_apply)
        mem_group.setLayout(mem_layout)
        
        mode_group = QGroupBox("Режим")
        mode_layout = QHBoxLayout()
        self.rb_view = QRadioButton("Инфо")
        self.rb_assign = QRadioButton("Назначение")
        self.rb_view.setChecked(True)
        self.mode_btn_group = QButtonGroup()
        self.mode_btn_group.addButton(self.rb_view)
        self.mode_btn_group.addButton(self.rb_assign)
        mode_layout.addWidget(self.rb_view)
        mode_layout.addWidget(self.rb_assign)
        mode_group.setLayout(mode_layout)

        tools_layout.addWidget(mem_group)
        tools_layout.addWidget(mode_group)
        left_panel.addLayout(tools_layout)
        
        self.ram_grid = RamGridWidget(read_only=False)
        self.ram_grid.table.cellClicked.connect(self.on_cell_clicked)
        left_panel.addWidget(self.ram_grid)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QVBoxLayout()

        grp_config = QGroupBox("Конфигурация (.json)")
        grp_config_layout = QHBoxLayout()
        btn_load = QPushButton("Загрузить")
        btn_save = QPushButton("Сохранить")
        btn_load.clicked.connect(self.load_config)
        btn_save.clicked.connect(self.save_config)
        grp_config_layout.addWidget(btn_load)
        grp_config_layout.addWidget(btn_save)
        grp_config.setLayout(grp_config_layout)
        
        grp_constructor = QGroupBox("Добавление неисправности")
        grp_cons_layout = QFormLayout()
        
        self.spin_fault_addr = QSpinBox()
        self.spin_fault_addr.setRange(0, self.spin_words.value() - 1)
        self.spin_fault_addr.setPrefix("Address: 0x")
        self.spin_fault_addr.setDisplayIntegerBase(16)
        
        self.spin_fault_bit = QSpinBox()
        self.spin_fault_bit.setRange(0, 15)
        self.spin_fault_bit.setPrefix("Bit: ")
        
        self.combo_fault_type = QComboBox()
        ru_names = [v for k, v in self.FAULT_TRANSLATIONS.items() if k != "NO"]
        self.combo_fault_type.addItems(ru_names)
        
        grp_cons_layout.addRow("Адрес слова:", self.spin_fault_addr)
        grp_cons_layout.addRow("Бит (0-15):", self.spin_fault_bit)
        grp_cons_layout.addRow("Тип:", self.combo_fault_type)
        
        btn_add_fault = QPushButton("Добавить")
        btn_add_fault.clicked.connect(self.add_fault)
        grp_cons_layout.addWidget(btn_add_fault)
        grp_constructor.setLayout(grp_cons_layout)

        grp_list = QGroupBox("Список ошибок")
        grp_list_layout = QVBoxLayout()
        self.list_faults = QListWidget()
        grp_list_layout.addWidget(self.list_faults)
        
        btns_list_layout = QHBoxLayout()
        btn_remove = QPushButton("Удалить")
        btn_remove.clicked.connect(self.remove_fault)
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.clear_all_faults)
        btns_list_layout.addWidget(btn_remove)
        btns_list_layout.addWidget(btn_clear)
        grp_list_layout.addLayout(btns_list_layout)
        grp_list.setLayout(grp_list_layout)

        right_panel.addWidget(grp_config)
        right_panel.addWidget(grp_constructor)
        right_panel.addWidget(grp_list)
        right_panel.addStretch() 

        main_layout.addLayout(left_panel, 7)
        main_layout.addLayout(right_panel, 3)

    def _vram_to_grid(self, addr, bit):
        grid_row = addr
        grid_col = 15 - bit
        return grid_row, grid_col

    def _grid_to_vram(self, row, col):
        addr = row
        bit = 15 - col
        return addr, bit

    def on_recreate_vram(self):
        """Полное создание НОВОГО объекта памяти."""
        word_count = self.spin_words.value()
        
        # 1. Создаем абсолютно новый объект, а не перезаписываем старый
        new_vram = Vram(word_count)
        self.vram = new_vram
        
        # 2. Обновляем UI локально
        self.spin_fault_addr.setRange(0, word_count - 1)
        self.list_faults.clear()
        self.apply_grid_settings()
        
        # 3. Сообщаем всем (Main -> TestingTab) о подмене
        self.vram_changed.emit(self.vram, word_count)

    def apply_grid_settings(self):
        words = self.spin_words.value()
        self.ram_grid.update_dimensions(words)
        self.ram_grid.table.setHorizontalHeaderLabels([str(15 - i) for i in range(16)])
        self.ram_grid.table.setVerticalHeaderLabels([f"0x{i:04X}" for i in range(words)])

    def on_cell_clicked(self, row, col):
        addr, bit = self._grid_to_vram(row, col)
        if self.rb_assign.isChecked():
            self.spin_fault_addr.setValue(addr)
            self.spin_fault_bit.setValue(bit)
        else:
            try:
                val = self.vram.read(addr)
                bit_val = (val >> bit) & 1
                err = self.vram.get_error(addr, bit)
                err_ru = self.FAULT_TRANSLATIONS.get(err.name, err.name)
                
                msg = (f"Адрес слова: 0x{addr:04X}\n"
                       f"Бит: {bit}\n"
                       f"Значение: {bit_val}\n"
                       f"Ошибка: {err_ru}")
                QMessageBox.information(self, "Инфо", msg)
            except Exception as e:
                print(e)

    def add_fault(self, load_data=None):
        if load_data:
            addr, bit, err_name_key = load_data
            if err_name_key in self.FAULT_TRANSLATIONS:
                ru_name = self.FAULT_TRANSLATIONS[err_name_key]
                err_type = getattr(Vram.ErrType, err_name_key)
            else:
                return 
        else:
            addr = self.spin_fault_addr.value()
            bit = self.spin_fault_bit.value()
            ru_name = self.combo_fault_type.currentText()
            if ru_name not in self.ru_to_type: return
            err_type = self.ru_to_type[ru_name]

        try:
            self.vram.set_error(addr, bit, err_type)
        except Exception as e:
            if not load_data: QMessageBox.critical(self, "Ошибка", str(e))
            return

        item_text = f"Addr 0x{addr:04X} | Bit {bit:02d} | {ru_name}"
        item = QListWidgetItem(item_text)
        key_name = err_type.name
        item.setData(Qt.ItemDataRole.UserRole, (addr, bit, key_name))
        self.list_faults.addItem(item)
        
        r, c = self._vram_to_grid(addr, bit)
        self.ram_grid.set_cell_state(r, c, text="!", color=AppConstants.COLOR_BG_ERROR)

    def remove_fault(self):
        items = self.list_faults.selectedItems()
        for item in items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                addr, bit, _ = data
                self.vram.set_error(addr, bit, Vram.ErrType.NO)
                r, c = self._vram_to_grid(addr, bit)
                self.ram_grid.set_cell_state(r, c, text="", color=AppConstants.COLOR_BG_DEFAULT)
            self.list_faults.takeItem(self.list_faults.row(item))

    def clear_all_faults(self):
        while self.list_faults.count() > 0:
            item = self.list_faults.item(0)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                addr, bit, _ = data
                self.vram.set_error(addr, bit, Vram.ErrType.NO)
                r, c = self._vram_to_grid(addr, bit)
                self.ram_grid.set_cell_state(r, c, text="", color=AppConstants.COLOR_BG_DEFAULT)
            self.list_faults.takeItem(0)

    def save_config(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить", "", "JSON (*.json)")
        if not file_path: return
        
        faults_data = []
        for i in range(self.list_faults.count()):
            item = self.list_faults.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            faults_data.append({"addr": data[0], "bit": data[1], "type": data[2]})
            
        config = {
            "ram_size_words": self.spin_words.value(),
            "faults": faults_data
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Успех", "Сохранено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить", "", "JSON (*.json)")
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            words = config.get("ram_size_words", 16)
            self.spin_words.setValue(words)
            
            # Пересоздаем память (это также вызовет сигнал vram_changed)
            self.on_recreate_vram()
            
            # Накидываем ошибки на НОВУЮ память
            for f in config.get("faults", []):
                self.add_fault((f["addr"], f["bit"], f["type"]))
                
            QMessageBox.information(self, "Успех", "Загружено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))