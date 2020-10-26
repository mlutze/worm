from typing import List, Dict

from worm.slim.error import CompilationError
from worm.slim.parser import ParsedLine, ParsedAlloc, ParsedCommand, ParsedLabel
from worm.util.validation import Validation, Success, Failure


class NamedCommand:
    def __init__(self, cmd: str, args: List[str], line: int):
        self.cmd = cmd
        self.args = args
        self.line = line


class NamedProgram:
    def __init__(self, lines: List[NamedCommand], registers: Dict[str, int], labels: Dict[str, int]):
        self.lines = lines
        self.registers = registers
        self.labels = labels


class NamingResult:
    pass


class Label(NamingResult):
    def __init__(self, name: str):
        self.name = name


class Line(NamingResult):
    def __init__(self, value: NamedCommand):
        self.value = value


class Noop(NamingResult):
    pass


class NoMoreRegistersError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


class RegisterInUseError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


class LabelInUseError(CompilationError):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def get_message(self) -> str:
        raise NotImplementedError


NUM_REGISTERS = 32


def do_name(code: List[ParsedLine]) -> Validation[NamedProgram, CompilationError]:
    registers: Dict[str, int] = {}
    labels: Dict[str, int] = {}

    # TODO docs
    def visit(line: ParsedLine, line_num: int, acc_labels: List[str]) -> Validation[NamingResult, CompilationError]:
        """
        Performs naming on the given line.
        :param line: the line on which to perform naming
        :param line_num: the line number of this line in the output
        :param acc_labels: the labels to associate with this line
        :return: a tuple (line, label) of the new line and next label, or a list of naming errors
        """
        if isinstance(line, ParsedAlloc):
            errors: List[CompilationError] = []
            for name in line.names:
                if name in registers or name in labels:
                    errors.append(RegisterInUseError(name, line.line))
                elif len(registers) >= NUM_REGISTERS:
                    errors.append(NoMoreRegistersError(name, line.line))
                else:
                    registers[name] = len(registers)
            if errors:
                return Failure(errors)
            else:
                return Success(Noop())
        elif isinstance(line, ParsedCommand):
            for label in acc_labels:
                labels[label] = line_num
            return Success(Line(NamedCommand(line.cmd, line.args, line.line)))
        elif isinstance(line, ParsedLabel):
            if line.name in registers or line.name in labels:
                return Failure([LabelInUseError(line.name, line.line)])
            else:
                return Success(Label(line.name))
        else:
            raise TypeError

    errors = []
    named_lines = []
    label_list: List[str] = []
    line_num = 0
    for line in code:
        result = visit(line, line_num, label_list)
        if isinstance(result, Success):
            if isinstance(result.value, Label):
                label_list.append(result.value.name)
            elif isinstance(result.value, Line):
                named_lines.append(result.value.value)
                line_num += 1
                label_list = []
        elif isinstance(result, Failure):
            errors.extend(result.value)
    if errors:
        return Failure(errors)
    else:
        return Success(NamedProgram(named_lines, registers, labels))
