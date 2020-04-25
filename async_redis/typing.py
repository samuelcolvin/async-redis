from typing import Union, Literal, List, Sequence

__all__ = 'ArgType', 'CommandArgs', 'DecodeType', 'ResultType'

ArgType = Union[bytes, bytearray, str, int, float]
CommandArgs = Sequence[ArgType]
DecodeType = Literal[None, 'str', 'int', 'float']
ResultTypeScalar = Union[bytes, str, int, float]
ResultType = Union[ResultTypeScalar, List[ResultTypeScalar]]
