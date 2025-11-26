# app/widgets/ram_grid.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from app.utils.constants import AppConstants

class RamGridWidget(QWidget):
    def __init__(self, read_only=False):
        super().__init__()
        self.read_only = read_only
        self.rows = AppConstants.DEFAULT_WORD_COUNT
        self.cols = AppConstants.GRID_COLS
        self.cell_size = AppConstants.DEFAULT_CELL_SIZE
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(self.rows, self.cols)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Заголовки
        self.table.horizontalHeader().setVisible(True)
        self.table.verticalHeader().setVisible(True)
        
        font = QFont()
        font.setPointSize(8)
        self.table.setFont(font)
        
        self._resize_cells()
        self.reset_grid()

        layout.addWidget(self.table)

    def _resize_cells(self):
        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(self.cell_size)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        v_header = self.table.verticalHeader()
        v_header.setDefaultSectionSize(self.cell_size)
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

    def update_dimensions(self, rows):
        """Обновление количества строк (слов)."""
        self.rows = int(rows)
        # Колонки фиксированы (16 бит)
        self.cols = AppConstants.GRID_COLS
        
        self.table.setRowCount(self.rows)
        self.table.setColumnCount(self.cols)
        self._resize_cells()
        self.reset_grid()

    def reset_grid(self):
        self.table.setUpdatesEnabled(False)
        for r in range(self.rows):
            for c in range(self.cols):
                self.set_cell_state(r, c, text="", color=AppConstants.COLOR_BG_DEFAULT)
        self.table.setUpdatesEnabled(True)

    def set_cell_state(self, row, col, text=None, color=None):
        if row >= self.rows or col >= self.cols:
            return

        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)
        
        if text is not None:
            item.setText(text)
        
        if color is not None:
            item.setBackground(QColor(color))

    def highlight_row(self, row, color):
        """Подсветка всей строки (слова)."""
        if row >= self.rows:
            return
        for c in range(self.cols):
            self.set_cell_state(row, c, color=color)