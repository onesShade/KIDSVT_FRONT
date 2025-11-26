#include "vram_test.hpp"

VramTest::StepResult VramTest::step() {
    while (true) {
        Word const i = _vmach.i();
        _vmach.step();

        switch (_vmach.state()) {
        case Vmach::PROGRAM_ENDED: return {StepResult::ENDED};

        case Vmach::PROGRAM_ERROR: throw std::runtime_error("Program error!");
        case Vmach::PROGRAM_UNKNOWN_OP: throw std::runtime_error("Unknown operation!");
        case Vmach::STACK_UNDERFLOW: throw std::runtime_error("Program stack underflow!");

        default:;
        }

        if (_vmach.last_op() == Vmach::opcode_write) {
            return {StepResult::WRITE, i};
        } else if (_vmach.last_op() == Vmach::opcode_assert) {
            if (_vmach.state() == Vmach::ASSERTION_FAILED) {
                _vmach.contin();
                _detected_errors.push_back(i);
                return {StepResult::TEST_FAILED, i};
            } else {
                return {StepResult::TEST_SUCCEEDED, i};
            }
        }
    }
}
