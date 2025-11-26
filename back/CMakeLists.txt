cmake_minimum_required(VERSION 3.11)
project(kidsvt VERSION 0.0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# === Настройки компилятора ===
# Разделяем флаги для MSVC и GCC/Clang
if(MSVC)
    # /W4 - высокий уровень предупреждений, /Od - отключить оптимизацию (для отладки)
    set(BACK_WARNINGS /W4 /Od) 
else()
    # Твои старые флаги для GCC/Clang
    set(BACK_WARNINGS -Og -g -W -Wall -Wextra -Wformat)
endif()

file(GLOB_RECURSE BACK_SOURCES "src/*.cpp")
set(BACK_HEADERS "include/")

# === main executable ===
add_executable(kidsvt ${BACK_SOURCES})
target_include_directories(kidsvt PRIVATE ${BACK_HEADERS})
target_compile_options(kidsvt PRIVATE ${BACK_WARNINGS})

# === pybind11 python module ===
add_subdirectory(extern/pybind11)

file(GLOB PYBIND_SOURCES "bindings/*.cpp")

# ВАЖНО: Добавляем src/vram.cpp, src/vram_test.cpp И src/vmach.cpp
# Если этого не сделать, модуль скомпилируется, но упадет при запуске.
pybind11_add_module(vram_backend 
    ${PYBIND_SOURCES} 
    src/vram.cpp 
    src/vram_test.cpp 
    src/vmach.cpp
)

target_include_directories(vram_backend PRIVATE ${BACK_HEADERS})

# Применяем флаги
target_compile_options(vram_backend PRIVATE ${BACK_WARNINGS})