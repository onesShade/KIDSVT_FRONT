#ifndef VRAM_TEST_HPP
#define VRAM_TEST_HPP

#include <fstream>

#include "vmach.hpp"
#include "vram.hpp"

class VramTest {
   public:
    using Word = Vram::Word;
    struct StepResult {
        enum Type { WRITE, TEST_SUCCEEDED, TEST_FAILED, ENDED } type;
        Word i;
    };

   public:
    VramTest(Vram &ram, std::string const kidscript_path)
    : _ram(ram), _kidscript(kidscript_path, std::ios::binary), _vmach(_kidscript, _ram) {};

    inline std::vector<Word> const detected_errors() { return _detected_errors; }

    StepResult step();

   private:
    Vram &_ram;

    std::ifstream _kidscript;
    Vmach _vmach;

    std::vector<Word> _detected_errors;
};

#endif
