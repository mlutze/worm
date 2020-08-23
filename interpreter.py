#!/usr/bin/env python3

from collections import namedtuple
from typing import List, Union, NamedTuple
import re
import sys

# non-digit followed by anything but whitespace or comma
NAME_REGEX = "[\D][^\s,]*"
COMMANDS = [
    "add", "sub", "mul", "div", "quo", "rem",
    "seq", "sne", "slt", "sgt", "sle", "sge",
    "ld", "st",
    "li",
    "read", "write",
    "j", "jeqz",
    "halt"
]

class Literal(NamedTuple):
    value: int

class Name(NamedTuple):
    value: str

Value = Union[Literal, Name]

class Command(NamedTuple):
    cmd: str
    args: List[Value]

class ResolvedCommand(NamedTuple):
    cmd: str
    args: List[int]

class Label(NamedTuple):
    name: str

class Alloc(NamedTuple):
    names: List[str]

class Noop(NamedTuple):
    pass

Line = Union[Command, Label, Alloc, Noop]

# parse lines of code into proper syntactic lines
def parse_slim(lines: List[str]) -> List[Line]:

    # removes comments and leading/trailing whitespace
    def clean_line(line):
        return line.split(";", maxsplit=1)[0].strip()

    def parse_value(value):
        if value.isdecimal():
            return Literal(int(value))
        else:
            return Name(value)

    # parses a cleaned line
    def parse_one(line):
        if line == "":
            return Noop()
        elif match := re.fullmatch("(" + NAME_REGEX + "):", line): # TODO allow space between name and colon?
            return Label(match[1])
        elif match := re.fullmatch(r"allocate-registers\s+(" + NAME_REGEX + r"(?:\s*,\s*" + NAME_REGEX + ")*)", line):
            names = [name.strip() for name in match[1].split(",")]
            return Alloc(names)
        elif match := re.fullmatch(r"([a-z]+)\s+((?:" + NAME_REGEX + r"|\d+)(?:\s*,\s*(?:" + NAME_REGEX + r"|\d+))*)", line):
            cmd = match[1]
            args = [parse_value(value.strip()) for value in match[2].split(",")]
            return Command(cmd, args)
        else:
            pass # TODO throw error
    

    return [parse_one(clean_line(line)) for line in lines]


# questions:
# can we allocate registers after commands -- yes
# what happens if we allocate more than 32 registers? -- says "no more registers available for $reg"; does this for each error
# what happens if we put 2 labels in a row? -- nothing special
# what happens if we put a label ahead of nothing -- ignored
# what happens if we allocate the same register twice? "Register name 'b' already in use on line 1."; does this for each error
def compile_slim(lines: List[Line]) -> List[Line]:
    registers = []
    for line in lines:
        if isinstance(line, Alloc):
            for name in line.names:
                if name in registers:
                    pass # throw error
                else:
                    registers.append(name)
    
    labeled_commands = []
    labels = []
    for line in lines:
        if isinstance(line, Label):
            labels.append(line)
        elif isinstance(line, Command):
            labeled_commands.append((labels, line))
            labels = []
   
    name_lookup = {}
     
    for i, labeled_command in enumerate(labeled_commands):
        for label in labeled_command[0]:
            name_lookup[label.name] = i

    for i, register in enumerate(registers):
        name_lookup[register] = i

    def resolve_arg(value):
        if isinstance(value, Name):
            return name_lookup[value.value] # TODO throw specific error
        else: # literal
            return value.value

    def resolve_command(command):
        args = [resolve_arg(arg) for arg in command.args] #TODO get mad about command name here?
        return Command(command.cmd, args)

    return [resolve_command(labeled_command[1]) for labeled_command in labeled_commands]
    

class SLIM:
    def __init__(self, commands: List[Command]):
        self.mem = {}
        self.registers = [0 for _ in range(32)]
        self.commands = commands
        self.pointer = 0

    def execute(self):
        while 0 <= self.pointer < len(self.commands):
            self.exec_command(self.commands[self.pointer])
        # TODO halt or something

    def exec_command(self, command: Command) -> None:
        print(command)
        if command.cmd not in COMMANDS:
            raise Exception

        getattr(self, command.cmd)(*command.args)

    def next_line(self):
        self.pointer += 1
        
    def add(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] + self.registers[src2]
        self.next_line()
    
    def sub(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] - self.registers[src2]
        self.next_line()

    def mul(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] * self.registers[src2]
        self.next_line()

    def div(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] // self.registers[src2]
        self.next_line()

    def quo(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] // self.registers[src2]
        self.next_line()

    def rem(self, dest, src1, src2):
        self.registers[dest] = self.registers[src1] % self.registers[src2]
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
        self.registers[dest] = self.memory[addr]
        self.next_line()

    def st(self, src, addr):
        self.memory[addr] = self.registers[src]
        self.next_line()

    
    def li(self, dest, const):
        self.registers[dest] = const
        self.next_line()

    
    def read(self, dest):
        self.registers[dest] = int(input())
        self.next_line()

    def write(self, src):
        print(self.registers[src])
        self.next_line()


    def j(self, addr):
        self.pointer = addr

    def jeqz(self, src, addr):
        if self.registers[src] == 0:
            self.pointer = self.registers[addr] # TODO something's wrong here

    def halt(self):
        pass

def main():
    with open(sys.argv[1]) as input_file:
        lines = [line for line in input_file.readlines()]
    parsed = parse_slim(lines)
    compiled = compile_slim(parsed)
    slim = SLIM(compiled)
    slim.execute()

if __name__ == "__main__":
    main()

