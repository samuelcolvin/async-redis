from enum import IntEnum
from typing import Any, Callable, List, Sequence, Union

__all__ = 'ArgType', 'CommandArgs', 'Decoders', 'ResultType'

ArgType = Union[bytes, bytearray, str, int, float]
CommandArgs = Sequence[ArgType]
ResultTypeScalar = Union[bytes, str, int, float]
ResultType = Union[ResultTypeScalar, List[ResultTypeScalar]]

IntFloat = Union[int, float]


class Decoders(IntEnum):
    ok = 1
    bytes = 2
    str = 3
    int = 4
    float = 5
    bool = 6

    def func(self) -> Callable[[Any], IntFloat]:
        return {self.int: int, self.float: float, self.bool: bool}[self]
