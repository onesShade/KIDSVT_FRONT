#include <cstdio>

#include "vram.hpp"
#include "vram_test.hpp"

#define PRINT_COLS (8)

static void printram(Vram const &ram) {
    printf("===== RAM dump =====\n");
    for (unsigned i = 0; i < ram.len / PRINT_COLS; i++) {
        for (unsigned j = 0; j < PRINT_COLS; j++) printf("%04X ", ram.read(i * PRINT_COLS + j));
        printf("\n");
    }
    printf("===== RAM dump end =====\n\n");
}

int main() {
    Vram vram(32);
    vram.set_error(3, 4, Vram::DECEPTIVE_READ_0);
    vram.set_error(1, 4, Vram::TRANSITION_1_TO_0);

    VramTest test_manager(vram, "./res/test.kids");
    while (true) {
        VramTest::StepResult const r = test_manager.step();
        switch (r.type) {
        case VramTest::StepResult::WRITE: printf("wrote into %i\n", r.i); break;
        case VramTest::StepResult::TEST_SUCCEEDED:
            printf("assertion succeeded on %i\n", r.i);
            break;
        case VramTest::StepResult::TEST_FAILED: printf("assertion failed on %i\n", r.i); break;
        case VramTest::StepResult::ENDED: goto test_ended;
        }
    }
test_ended:;

    printram(vram);
    printram(vram);

    return 0;
}
