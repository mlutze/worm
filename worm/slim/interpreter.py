#!/usr/bin/env python3

import sys
from typing import Dict, List, Tuple

from worm.slim import parser, namer, resolver
from worm.slim.resolver import ResolvedCommand
from worm.util.console import Console, StdIoConsole
from worm.util.validation import Failure, Success, flatmap


class HaltException(Exception):
    pass


def bound_int(i: int) -> int:
    return (i + 2 ** 31) % (2 ** 32) - 2 ** 31


def sign(i: int) -> int:
    if i > 0:
        return 1
    elif i == 0:
        return 0
    else:
        return -1


def swap_sign(a: int, b: int) -> Tuple[int, int]:
    if sign(a) == sign(b):
        return a, b
    else:
        return -a, -b


class SLIM:
    def __init__(self, commands: List[ResolvedCommand], console: Console):
        self.mem: Dict[int, int] = {}
        self.registers = [0 for _ in range(32)]
        self.commands = commands
        self.pointer = 0
        self.console = console

    def execute(self):
        while 0 <= self.pointer < len(self.commands):
            try:
                self.exec_command(self.commands[self.pointer])
            except HaltException:
                break

    def exec_command(self, command: ResolvedCommand) -> None:
        getattr(self, command.cmd)(*command.args)

    def next_line(self):
        self.pointer += 1

    def add(self, dest, src1, src2):
        self.registers[dest] = bound_int(self.registers[src1] + self.registers[src2])
        self.next_line()

    def sub(self, dest, src1, src2):
        self.registers[dest] = bound_int(self.registers[src1] - self.registers[src2])
        self.next_line()

    def mul(self, dest, src1, src2):
        self.registers[dest] = bound_int(self.registers[src1] * self.registers[src2])
        self.next_line()

    def div(self, dest, src1, src2):
        self.registers[dest] = bound_int(self.registers[src1] // self.registers[src2])
        self.next_line()

    def quo(self, dest, src1, src2):
        self.registers[dest] = bound_int(self.registers[src1] // self.registers[src2])
        self.next_line()

    def rem(self, dest, src1, src2):
        a, b = swap_sign(self.registers[src1], self.registers[src2])
        self.registers[dest] = bound_int(a % b)
        self.next_line()

    def seq(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] == self.registers[src2])
        self.next_line()

    def sne(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] != self.registers[src2])
        self.next_line()

    def slt(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] < self.registers[src2])
        self.next_line()

    def sgt(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] > self.registers[src2])
        self.next_line()

    def sle(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] <= self.registers[src2])
        self.next_line()

    def sge(self, dest, src1, src2):
        self.registers[dest] = int(self.registers[src1] >= self.registers[src2])
        self.next_line()

    def ld(self, dest, addr):
        self.registers[dest] = self.mem[self.registers[addr]]
        self.next_line()

    def st(self, src, addr):
        self.mem[self.registers[addr]] = self.registers[src]
        self.next_line()

    def li(self, dest, const):
        self.registers[dest] = const
        self.next_line()

    def read(self, dest):
        self.registers[dest] = int(self.console.read())
        self.next_line()

    def write(self, src):
        self.console.write(str(self.registers[src]))
        self.next_line()

    def j(self, addr):
        self.pointer = self.registers[addr]

    def jeqz(self, src, addr):
        if self.registers[src] == 0:
            self.pointer = self.registers[addr]
        else:
            self.next_line()

    def halt(self):
        raise HaltException


class Interpreter:

    def __init__(self, console: Console):
        self.console = console

    def interpret(self, code: str) -> None:

        parsed_val = parser.parse(code.splitlines())
        named_val = flatmap(parsed_val, namer.do_name)
        resolved_val = flatmap(named_val, resolver.resolve)

        if isinstance(resolved_val, Failure):
            for error in resolved_val.value:
                self.console.write_error(error.get_message())
        elif isinstance(resolved_val, Success):
            compiled = resolved_val.value
            SLIM(compiled, self.console).execute()


def main():
    with open(sys.argv[1]) as input_file:
        lines = [line for line in input_file.readlines()]
    Interpreter(StdIoConsole("")).interpret("".join(lines))


if __name__ == "__main__":
    main()
