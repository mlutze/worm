import itertools
from typing import TypeVar, Generic, List, Callable

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


class Validation(Generic[T, E]):
    pass


class Success(Generic[T, E], Validation[T, E]):
    def __init__(self, value: T):
        self.value = value


class Failure(Generic[T, E], Validation[T, E]):
    def __init__(self, value: List[E]):
        self.value = value


def flatmap(val: Validation[T, E], func: Callable[[T], Validation[U, E]]) -> Validation[U, E]:
    if isinstance(val, Success):
        return func(val.value)
    elif isinstance(val, Failure):
        return val
    else:
        raise TypeError


def sequence(vals: List[Validation[T, E]]) -> Validation[List[T], E]:
    successes = [val for val in vals if isinstance(val, Success)]
    failures = [val for val in vals if isinstance(val, Failure)]
    if failures:
        return Failure([i for i in itertools.chain.from_iterable(failure.value for failure in failures)])
    else:
        return Success([success.value for success in successes])
