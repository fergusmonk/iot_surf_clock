cmake_minimum_required(VERSION 3.16)
project(iot_assistant CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(USE_MOCK_HAL "Use mock hardware abstraction (for dev without Pi)" ON)

# vcpkg toolchain is set via -DCMAKE_TOOLCHAIN_FILE at configure time
find_package(nlohmann_json CONFIG REQUIRED)
find_package(GTest CONFIG REQUIRED)

# Collect sources
file(GLOB_RECURSE SOURCES src/*.cpp)

add_executable(iot_assistant ${SOURCES})

target_include_directories(iot_assistant PRIVATE src)

target_link_libraries(iot_assistant PRIVATE
    nlohmann_json::nlohmann_json
)

if(USE_MOCK_HAL)
    target_compile_definitions(iot_assistant PRIVATE USE_MOCK_HAL)
else()
    # Link pigpio and ALSA only when building for real hardware
    target_link_libraries(iot_assistant PRIVATE pigpio asound)
endif()

# Tests
enable_testing()
file(GLOB_RECURSE TEST_SOURCES tests/*.cpp)
list(FILTER SOURCES EXCLUDE REGEX ".*/main\\.cpp$")
add_executable(iot_tests ${TEST_SOURCES} ${SOURCES})
target_include_directories(iot_tests PRIVATE src)
target_compile_definitions(iot_tests PRIVATE USE_MOCK_HAL)
target_link_libraries(iot_tests PRIVATE GTest::gtest_main nlohmann_json::nlohmann_json)
add_test(NAME all_tests COMMAND iot_tests)
