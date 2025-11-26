cmake_minimum_required(VERSION 3.11)
project(kidsvt VERSION 0.0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

### main ###

set(MAIN main)
file(GLOB_RECURSE MAIN_SRCS "src/*.cpp")
set(MAIN_INCLUDES "include/")

add_executable(${MAIN})

target_sources(${MAIN} PRIVATE ${MAIN_SRCS})
target_include_directories(${MAIN} PRIVATE ${MAIN_INCLUDES})

set(MAIN_COMMON_FLAGS
    -Og -g -W -Wall -Wextra -Wformat)
target_compile_options(${MAIN} PRIVATE
    ${COMPILE_AND_LINK_OPTS})
target_link_options(${MAIN} PRIVATE
    ${COMPILE_AND_LINK_OPTS})
target_compile_definitions(${MAIN} PRIVATE
    )
