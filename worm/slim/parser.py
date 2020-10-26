import re
from typing import List

from worm.slim.error import CompilationError
from worm.util.option import Option, Some, Nothing, flatten
from worm.util.validation import Validation, Success


class ParsedLine:
    pass


class ParsedCommand(ParsedLine):
    def __init__(self, cmd: str, args: List[str], line: int):
        self.cmd = cmd
        self.args = args
        self.line = line


class ParsedLabel(ParsedLine):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line


class ParsedAlloc(ParsedLine):
    def __init__(self, name: List[str], line: int):
        self.names = name
        self.line = line


NAME_REGEX = r"[\D][^\s,]*"


def parse(code: List[str]) -> Validation[List[ParsedLine], CompilationError]:
    # removes comments and leading/trailing whitespace
    def clean_line(line: str) -> str:
        return line.split(";", maxsplit=1)[0].strip()

    def visit(line: str, line_num: int) -> Option[ParsedLine]:
        if line == "":
            return Nothing()
        # TODO allow space between name and colon?
        elif match := re.fullmatch("(" + NAME_REGEX + "):", line):
            return Some(ParsedLabel(match[1], line_num))  # type: ignore
        elif match := re.fullmatch(r"allocate-registers\s+(" + NAME_REGEX + r"(?:\s*,\s*" + NAME_REGEX + ")*)", line):
            names = [name.strip() for name in match[1].split(",")]  # type: ignore
            return Some(ParsedAlloc(names, line_num))
        elif match := re.fullmatch(r"([a-z]+)(\s+(?:" + NAME_REGEX + r"|\d+)(?:\s*,\s*(?:" +
                                   NAME_REGEX + r"|\d+))*)?", line):
            cmd = match[1]  # type: ignore
            arg_string = match[2]  # type: ignore
            if arg_string is None:
                args = []
            else:
                args = [arg.strip() for arg in arg_string.split(",")]

            return Some(ParsedCommand(cmd, args, line_num))
        else:
            raise Exception  # TODO collect

    parsed_lines = [visit(clean_line(line), i) for i, line in enumerate(code, start=1)]
    return Success(flatten(parsed_lines))
