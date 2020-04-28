from __future__ import annotations

import sys
from typing import List, Optional, Sequence, Union

__all__ = 'Literal', 'ArgType', 'CommandArgs', 'ReturnAs', 'ResultType'

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

ArgType = Union[bytes, bytearray, str, int, float]
CommandArgs = Sequence[ArgType]
ResultTypeScalar = Union[None, bytes, str, int, float]
ResultType = Union[ResultTypeScalar, List[ResultTypeScalar]]

ReturnAs = Optional[Literal['ok', 'str', 'int', 'float', 'bool']]
