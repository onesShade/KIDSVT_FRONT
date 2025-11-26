#include "vram.hpp"

#include <cstddef>
#include <stdexcept>

Vram::Word Vram::read(size_t const i) const {
    Word word = _data[i];
    try {
        auto const errs = _errors.at(i);
        for (unsigned pos = 0; pos < errs.size(); pos++) switch (errs[pos]) {
            case NO: break;
            case STUCK_AT_0: word &= ~(1 << pos); break;
            case STUCK_AT_1: word |= (1 << pos); break;
            case WRITE_OR_READ_DESTRUCTIVE_0:
                if (!(word & (1 << pos))) {
                    _data[i] |= (1 << pos);
                    word = _data[i];
                }
                break;
            case WRITE_OR_READ_DESTRUCTIVE_1:
                if (word & (1 << pos)) {
                    _data[i] &= ~(1 << pos);
                    word = _data[i];
                }
                break;
            case INCORRECT_READ_0:
                if (!(word & (1 << pos))) word |= (1 << pos);
                break;
            case INCORRECT_READ_1:
                if (word & (1 << pos)) word &= ~(1 << pos);
                break;
            case DECEPTIVE_READ_0:
                if (!(word & (1 << pos))) _data[i] |= (1 << pos);
                break;
            case DECEPTIVE_READ_1:
                if (word & (1 << pos)) _data[i] &= ~(1 << pos);
                break;

            default:;
            }
    } catch (std::out_of_range const &e) {}
    return word;
}

void Vram::write(size_t const i, Word word) {
    try {
        auto const errs = _errors.at(i);
        for (unsigned pos = 0; pos < errs.size(); pos++) switch (errs[pos]) {
            case NO: break;
            case TRANSITION_0_TO_1:
                if (word & (1 << pos)) word &= ~(1 << pos);
                break;
            case TRANSITION_1_TO_0:
                if (!(word & (1 << pos))) word |= (1 << pos);
                break;
            case WRITE_OR_READ_DESTRUCTIVE_0:
                if (!(word & (1 << pos))) word |= (1 << pos);
                break;
            case WRITE_OR_READ_DESTRUCTIVE_1:
                if (word & (1 << pos)) word &= ~(1 << pos);
                break;

            default:;
            }
    } catch (std::out_of_range const &e) {}
    _data[i] = word;
}
