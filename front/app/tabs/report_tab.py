# app/tabs/report_tab.py
from datetime import datetime
from collections import Counter
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, 
                             QHBoxLayout, QPushButton, QFileDialog)
from PyQt6.QtGui import QFont

class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.report_area = QPlainTextEdit()
        self.report_area.setReadOnly(True)
        # Моноширинный шрифт
        font = QFont("Courier New", 10)
        self.report_area.setFont(font)
        self.report_area.setPlaceholderText("Ожидание результатов тестирования...")

        controls_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить в .txt")
        btn_clear = QPushButton("Очистить журнал")
        
        btn_save.clicked.connect(self.save_report)
        btn_clear.clicked.connect(self.report_area.clear)
        
        controls_layout.addWidget(btn_save)
        controls_layout.addWidget(btn_clear)
        controls_layout.addStretch()

        layout.addWidget(self.report_area)
        layout.addLayout(controls_layout)

    def append_formatted_result(self, test_name, errors):
        """Вывод результата простым текстом без рамок + группировка."""
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        # Считаем общее количество ошибок (событий)
        total_err_count = len(errors)
        
        # Группировка: Уникальные адреса и их количество
        # Counter создаст словарь {адрес: кол-во}
        error_counts = Counter(errors)
        unique_addresses = sorted(error_counts.keys())
        unique_count = len(unique_addresses)
        
        status_str = "УСПЕШНО" if total_err_count == 0 else "ПРОВАЛЕН"
        
        lines = []
        lines.append("==================================================")
        lines.append(f"ОТЧЕТ ОТ {timestamp}")
        lines.append("==================================================")
        lines.append(f"Тест       : {test_name}")
        lines.append(f"Статус     : {status_str}")
        lines.append(f"Событий    : {total_err_count}")
        lines.append(f"Битых ячеек: {unique_count}")
        lines.append("--------------------------------------------------")
        
        if unique_count > 0:
            lines.append("Детализация (Адрес [Кол-во раз]):")
            
            max_lines = 100
            for i, addr in enumerate(unique_addresses):
                if i >= max_lines:
                    lines.append(f"... и еще {unique_count - max_lines} адресов.")
                    break
                
                count = error_counts[addr]
                # Формат: 1. 0x00A1 (5)
                # Если ошибка 1 раз, можно не писать число, или писать (1) для единообразия.
                # Сделаем: если > 1, пишем число.
                suffix = f" ({count})" if count > 1 else ""
                lines.append(f"{i+1}. 0x{addr:04X}{suffix}")
        else:
            lines.append("Ошибок не обнаружено.")

        lines.append("\n") 
            
        final_text = "\n".join(lines)
        self.report_area.appendPlainText(final_text)

    def save_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", "", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.report_area.toPlainText())
            except Exception as e:
                print(e)