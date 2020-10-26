from typing import TypeVar, Generic, List

T = TypeVar("T")


class Option(Generic[T]):
    pass


class Some(Generic[T], Option[T]):
    def __init__(self, value: T):
        self.value = value


class Nothing(Generic[T], Option[T]):
    pass


def flatten(xs: List[Option[T]]) -> List[T]:
    return [x.value for x in xs if isinstance(x, Some)]
