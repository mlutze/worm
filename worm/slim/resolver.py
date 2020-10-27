from enum import Enum
from typing import List, Dict
import re

from worm.slim.error import CompilationError
from worm.slim.namer import NamedProgram, NamedCommand
from worm.util.validation import Validation, Success, Failure, sequence


class Value(Enum):
    Register = 1
    Label = 2


COMMANDS: Dict[str, List[Value]] = {
    "add": [Value.Register, Value.Register, Value.Register],
    "sub": [Value.Register, Value.Register, Value.Register],
    "mul": [Value.Register, Value.Register, Value.Register],
    "div": [Value.Register, Value.Register, Value.Register],
    "quo": [Value.Register, Value.Register, Value.Register],
    "rem": [Value.Register, Value.Register, Value.Register],
    "seq": [Value.Register, Value.Register, Value.Register],
    "sne": [Value.Register, Value.Register, Value.Register],
    "slt": [Value.Register, Value.Register, Value.Register],
    "sgt": [Value.Register, Value.Register, Value.Register],
    "sle": [Value.Register, Value.Register, Value.Register],
    "sge": [Value.Register, Value.Register, Value.Register],
    "ld": [Value.Register, Value.Register],
    "st": [Value.Register, Value.Register],
    "li": [Value.Register, Value.Label],
    "read": [Value.Register],
    "write": [Value.Register],
    "j": [Value.Register],
    "jeqz": [Value.Register, Value.Register],
    "halt": [],
}


class ResolvedLine:
    pass


class ResolvedCommand(ResolvedLine):
    def __init__(self, cmd: str, args: List[int]):
        self.cmd = cmd
        self.args = args


class UnknownOpcodeError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        return f"Unknown opcode '{self.name}' in line {self.line}."


class MissingArgumentError(CompilationError):
    def __init__(self, line: int):
        self.line = line

    def get_message(self) -> str:
        return f"Missing argument in line {self.line}."


class TooManyArgumentsError(CompilationError):
    def __init__(self, line: int):
        self.line = line

    def get_message(self) -> str:
        return f"Too many arguments in line {self.line}."


class BadWordError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


class UnknownNameError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        return f"Unknown name '{self.name}' in line {self.line}."


class ExpectedRegisterError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


class ExpectedLabelError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


def resolve(program: NamedProgram) -> Validation[List[ResolvedLine], CompilationError]:
    def visit_arg(arg: str, expected: Value, line: int) -> Validation[int, CompilationError]:
        if re.fullmatch(r"-?\d+", arg):
            return Success(int(arg))
        elif arg in program.registers:
            if expected == Value.Register:
                return Success(program.registers[arg])
            else:
                return Failure([ExpectedLabelError(arg, line)])
        elif arg in program.labels:
            if expected == Value.Label:
                return Success(program.labels[arg])
            else:
                return Failure([ExpectedRegisterError(arg, line)])
        else:
            return Failure([UnknownNameError(arg, line)])

    def visit(line: NamedCommand) -> Validation[ResolvedLine, CompilationError]:
        if isinstance(line, NamedCommand):
            if line.cmd not in COMMANDS:
                return Failure([UnknownOpcodeError(line.cmd, line.line)])
            elif len(line.args) < len(COMMANDS[line.cmd]):
                return Failure([MissingArgumentError(line.line)])
            elif len(line.args) > len(COMMANDS[line.cmd]):
                return Failure([TooManyArgumentsError(line.line)])
            else:
                errors: List[CompilationError] = []
                resolved_args: List[int] = []
                for i in range(len(line.args)):
                    arg_result = visit_arg(line.args[i], COMMANDS[line.cmd][i], line.line)
                    if isinstance(arg_result, Failure):
                        errors.extend(arg_result.value)
                    elif isinstance(arg_result, Success):
                        resolved_args.append(arg_result.value)
                if errors:
                    return Failure(errors)
                else:
                    return Success(ResolvedCommand(line.cmd, resolved_args))
        else:
            raise Exception

    return sequence([visit(line) for line in program.lines])
