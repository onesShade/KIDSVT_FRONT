#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Необходим для автоматической конвертации std::vector

#include "../include/vram.hpp"
#include "../include/vram_test.hpp" // Не забудь добавить этот хедер

namespace py = pybind11;

PYBIND11_MODULE(vram_backend, m) {
    // ===========================
    // Vram Binding
    // ===========================
    py::class_<Vram> vram(m, "Vram");

    py::enum_<Vram::ErrType>(vram, "ErrType")
        .value("NO", Vram::ErrType::NO)
        .value("STUCK_AT_0", Vram::ErrType::STUCK_AT_0)
        .value("STUCK_AT_1", Vram::ErrType::STUCK_AT_1)
        .value("TRANSITION_0_TO_1", Vram::ErrType::TRANSITION_0_TO_1)
        .value("TRANSITION_1_TO_0", Vram::ErrType::TRANSITION_1_TO_0)
        .value("WRITE_OR_READ_DESTRUCTIVE_0", Vram::ErrType::WRITE_OR_READ_DESTRUCTIVE_0)
        .value("WRITE_OR_READ_DESTRUCTIVE_1", Vram::ErrType::WRITE_OR_READ_DESTRUCTIVE_1)
        .value("INCORRECT_READ_0", Vram::ErrType::INCORRECT_READ_0)
        .value("INCORRECT_READ_1", Vram::ErrType::INCORRECT_READ_1)
        .value("DECEPTIVE_READ_0", Vram::ErrType::DECEPTIVE_READ_0)
        .value("DECEPTIVE_READ_1", Vram::ErrType::DECEPTIVE_READ_1)
        .export_values();

    vram.def(py::init<size_t>())
        .def("read", &Vram::read)
        .def("write", &Vram::write)
        .def("set_error", &Vram::set_error)
        .def("get_error", &Vram::get_error);

    // ===========================
    // TestRunner (VramTest) Binding
    // ===========================
    
    // Биндим VramTest под именем TestRunner, как просили
    py::class_<VramTest> test_runner(m, "TestRunner");

    // Биндим вложенную структуру StepResult внутрь TestRunner
    py::class_<VramTest::StepResult> step_result(test_runner, "StepResult");

    // Биндим enum Type внутри StepResult
    py::enum_<VramTest::StepResult::Type>(step_result, "Type")
        .value("WRITE", VramTest::StepResult::WRITE)
        .value("TEST_SUCCEEDED", VramTest::StepResult::TEST_SUCCEEDED)
        .value("TEST_FAILED", VramTest::StepResult::TEST_FAILED)
        .value("ENDED", VramTest::StepResult::ENDED)
        .export_values();

    // Открываем поля структуры StepResult для чтения
    step_result.def_readonly("type", &VramTest::StepResult::type)
               .def_readonly("i", &VramTest::StepResult::i);

    // Методы самого TestRunner
    test_runner
        // Конструктор принимает ссылку на Vram и путь к файлу
        // pybind11 корректно обработает ссылку на существующий объект Vram
        .def(py::init<Vram&, std::string const>())
        
        .def("step", &VramTest::step)
        
        // stl.h автоматически сконвертирует std::vector в Python list
        .def("detected_errors", &VramTest::detected_errors);
}