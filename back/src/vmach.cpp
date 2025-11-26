#include "vmach.hpp"

#include <algorithm>
#include <cstdio>
#include <iostream>
#include <optional>

template <typename T>
static std::optional<T> sane_stoull(std::string const &str) {
    static_assert(std::is_unsigned<T>());

    // the first character must be '-', '+' or a decimal digit; letter values are only written like
    // 0F00 or 0xF00
    if (str[0] != '-' && str[0] != '+' && !isdigit(str[0])) return std::nullopt;
    try {
        return std::make_optional<T>(std::stoull(str, NULL, 16));
    } catch (std::invalid_argument const &e) { return std::nullopt; }
}

template <typename T>
static T sane_pop(std::stack<T> &stack) {
    if (stack.empty()) throw std::range_error("Stack underflowed!");
    T const t = std::move(stack.top());
    stack.pop();
    return t;
}

/************
 ** public **
 ************/

std::string const Vmach::opcode_loop = "loop", Vmach::opcode_endloop = "endloop";
std::string const Vmach::opcode_asc = "asc", Vmach::opcode_desc = "desc";
std::string const Vmach::opcode_then = "then", Vmach::opcode_endthen = "endthen";
std::string const Vmach::opcode_assert = "assert!";
std::string const Vmach::opcode_read = "read", Vmach::opcode_write = "write";
std::string const Vmach::opcode_swap = "swap", Vmach::opcode_drop = "drop";
std::string const Vmach::opcode_cur = "cur", Vmach::opcode_last = "last";
std::string const Vmach::opcode_equal = "equal?", Vmach::opcode_greater = "greater?",
                  Vmach::opcode_less = "less?";
std::string const Vmach::opcode_not = "not", Vmach::opcode_xor = "xor", Vmach::opcode_or = "or",
                  Vmach::opcode_and = "and", Vmach::opcode_lshift = "lsh";
std::string const Vmach::opcode_add = "add", Vmach::opcode_neg = "neg";
std::string const Vmach::opcode_push_i = "i", Vmach::opcode_pop_i = "i=";

void Vmach::reset() {
    _i = 0;
    while (!_stack.empty()) _stack.pop();
    while (!_hidden_stack.empty()) _hidden_stack.pop();

    _state = OK;
    _program.clear(), _program.seekg(0, std::ios::beg);
}
void Vmach::step() {
    if (_state != OK) return;
    try {
        auto const op = _last_op = next_op();
        auto const constant = sane_stoull<Word>(op);

        if (constant.has_value()) {
            op_const(constant.value());
        } else {
            if (op.empty()) throw PROGRAM_ENDED;

            try {
                _ops.at(op)();
            } catch (std::out_of_range const &e) { throw PROGRAM_UNKNOWN_OP; }
        }
    } catch (State const &state_change) { _state = state_change; }
}

void Vmach::dump_stack() const {
    std::stack<Word> tmp = _stack;
    std::vector<Word> elems;
    while (!tmp.empty()) {
        elems.push_back(tmp.top());
        tmp.pop();
    }
    std::reverse(elems.begin(), elems.end());
    std::cout << "[STACK i=" << _i << "] ";
    for (auto w : elems) std::cout << std::hex << w << " ";
    std::cout << std::endl;
}

/*************
 ** private **
 *************/

std::map<std::string, std::string> const Vmach::_opcode_opposites = {
    {Vmach::opcode_loop, Vmach::opcode_endloop},
    {Vmach::opcode_endloop, Vmach::opcode_loop},
    {Vmach::opcode_then, Vmach::opcode_endthen},
    {Vmach::opcode_endthen, Vmach::opcode_then},
};

std::string Vmach::next_op() {
    std::string op;
    if (!(_program >> op)) throw PROGRAM_ENDED;
    // makes the machine case-insensitive
    std::transform(op.begin(), op.end(), op.begin(), tolower);
    return op;
}
std::string Vmach::prev_op() {
    std::string op;
    do { _program.seekg(-2, std::ios::cur); } while (_program && !isspace(_program.get()));
    do { _program.seekg(-2, std::ios::cur); } while (_program && isspace(_program.get()));
    if (!_program) throw PROGRAM_ERROR;

    size_t const pos = _program.tellg();
    op = next_op();
    _program.seekg(pos);

    return op;
}

void Vmach::goto_matching_op(std::string const &target_op, int const dir) {
    if (dir < 0) prev_op();  // skip the last op

    int nesting_lvl = 1;
    std::string op;
    do {
        op = dir > 0 ? next_op() : prev_op();

        if (op == target_op)
            nesting_lvl--;
        else if (_opcode_opposites.count(target_op) && op == _opcode_opposites.at(target_op))
            nesting_lvl++;
    } while (!op.empty() && nesting_lvl > 0);

    dir > 0 ? prev_op() : next_op();  // after the backward-searched / at the forward-searched
}

Vmach::Word Vmach::stack_pop() {
    try {
        return sane_pop(_stack);
    } catch (std::range_error const &e) { throw STACK_UNDERFLOW; }
}
void Vmach::stack_push(Vmach::Word const value) { _stack.push(value); }

void Vmach::op_const(Word const value) { stack_push(value); }
void Vmach::op_loop() { _hidden_stack.push(_i), _i = stack_pop(); }
void Vmach::op_endloop() {
    if (_i == 0) {
        try {
            _i = sane_pop(_hidden_stack);
        } catch (std::range_error const &e) { throw PROGRAM_ERROR; }
    } else {
        goto_matching_op(opcode_loop, -1);
    }
}
void Vmach::op_asc() { _i = (_i + 1) % _ram.len; }
void Vmach::op_desc() { _i = (_i - 1) % _ram.len; }

void Vmach::op_then() {
    if (!stack_pop()) goto_matching_op(opcode_endthen, 1);
}
void Vmach::op_endthen() {}

void Vmach::op_assert() {
    if (!stack_pop()) throw ASSERTION_FAILED;
}

void Vmach::op_read() { stack_push(_ram.read(_i)); }
void Vmach::op_write() { _ram.write(_i, stack_pop()); }

void Vmach::op_swap() {
    Word const cur = stack_pop(), last = stack_pop();
    stack_push(cur), stack_push(last);
}
void Vmach::op_drop() { stack_pop(); }
void Vmach::op_last() {
    Word const cur = stack_pop(), last = stack_pop();
    stack_push(last), stack_push(cur), stack_push(last);
}
void Vmach::op_cur() {
    Word const cur = stack_pop();
    stack_push(cur), stack_push(cur);
}

void Vmach::op_equal() { stack_push(stack_pop() == stack_pop() ? -1 : 0); }
void Vmach::op_greater() { stack_push(stack_pop() > stack_pop() ? -1 : 0); }
void Vmach::op_less() { stack_push(stack_pop() < stack_pop() ? -1 : 0); }

void Vmach::op_not() { stack_push(~stack_pop()); }
void Vmach::op_xor() { stack_push(stack_pop() ^ stack_pop()); }
void Vmach::op_and() { stack_push(stack_pop() & stack_pop()); }
void Vmach::op_or() { stack_push(stack_pop() | stack_pop()); }
void Vmach::op_lshift() { stack_push(stack_pop() << 1); }

void Vmach::op_add() { stack_push(stack_pop() + stack_pop()); }
void Vmach::op_neg() { stack_push(-stack_pop()); }

void Vmach::op_push_i() { stack_push(_i); }
void Vmach::op_pop_i() { _i = stack_pop(); }
