import sys
from abc import ABC, abstractmethod
from typing import List


class Console(ABC):

    @abstractmethod
    def read(self) -> str:
        pass

    @abstractmethod
    def write(self, message: str) -> None:
        pass

    @abstractmethod
    def write_error(self, message: str) -> None:
        pass


class StdIoConsole(Console):

    def __init__(self, prompt):
        self.prompt = prompt

    def read(self) -> str:
        return input(self.prompt)

    def write(self, message: str) -> None:
        print(message)

    def write_error(self, message: str) -> None:
        print(message, file=sys.stderr)


class StaticConsole(Console):

    def __init__(self, lines: List[str]):
        self.input = iter(lines)
        self.output: List[str] = []
        self.error: List[str] = []

    def read(self) -> str:
        return next(self.input)

    def write(self, message: str) -> None:
        self.output.append(message)

    def write_error(self, message: str) -> None:
        self.error.append(message)
