# app/utils/constants.py
import os

class AppConstants:
    WINDOW_TITLE = "KIDSVT UI - Симуляция неисправностей RAM"
    WINDOW_WIDTH = 1300
    WINDOW_HEIGHT = 800
    
    # Размеры по умолчанию
    DEFAULT_WORD_COUNT = 16
    BITS_PER_WORD = 16
    
    # Визуализация
    GRID_COLS = 16
    DEFAULT_CELL_SIZE = 40

    # Пути
    TEST_FILES_PATH = r"./res"

    # Цвета (HEX)
    COLOR_BG_DEFAULT = "#FFFFFF"
    COLOR_BG_ACTIVE = "#FFFACD"   # Светло-желтый (текущая операция)
    COLOR_BG_SUCCESS = "#90EE90"  # Светло-зеленый (проверено, ок)
    
    # Изменено на насыщенный красный по просьбе
    COLOR_BG_ERROR = "#FF3333"    
    
    COLOR_TEXT_DEFAULT = "#000000"