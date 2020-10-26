from abc import ABC, abstractmethod


class CompilationError(ABC):

    @abstractmethod
    def get_message(self) -> str:
        pass
