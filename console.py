from abc import ABC, abstractmethod

class Console(ABC):

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self, message):
        pass


class StdIoConsole(Console):

    def __init__(self, prompt):
        self.prompt = prompt
    
    def read(self):
        return input(self.prompt)

    def write(self, message):
        print(message)

class StaticConsole(Console):

    def __init__(self, lines):
        self.input = iter(lines)
        self.output = []

    def read(self):
        return next(self.input)

    def write(self, message):
        self.output.append(message)
