#!/usr/bin/env python3
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
func_regex = re.compile(r'( {4}def [a-z][a-z_]+\(.*?\) -> )Result.*?\n( {8}""".+?"""\n {8})', flags=re.S)

HEAD = """\
from typing import Any, Coroutine, List, Tuple, TypeVar, Union

from .commands import AbstractCommands
from .connection import RawConnection
from .typing import ArgType, CommandArgs, Literal, ResultType, ReturnAs

__all__ = ('CommandsPipeline',)


class CommandsPipeline(AbstractCommands):
    _conn: RawConnection
    _pipeline: List[CommandArgs]

    def __init__(self, raw_connection: RawConnection):
        ...

    def _execute(self, args: CommandArgs, return_as: ReturnAs) -> None:
        ...

    async def execute(self, return_as: ReturnAs = None) -> List[ResultType]:
        ...

"""


def main():
    commands_text = (ROOT_DIR / 'async_redis' / 'commands.py').read_text()

    matches = func_regex.findall(commands_text[commands_text.find('String commands'):])

    funcs = []
    for func_def, docstring in matches:
        if '\n' in func_def:
            func_def = func_def.replace('(\n', '(  # type: ignore\n')
            f = f'{func_def}None:\n{docstring}pass\n'
        else:
            f = f'{func_def}None:  # type: ignore\n{docstring}pass\n'
        funcs.append(f)

    stubs = HEAD + '\n'.join(funcs)
    path = ROOT_DIR / 'async_redis' / 'pipeline_commands.pyi'
    path.write_text(stubs)
    print(f'pipeline_commands.py stubs written to {path}')


if __name__ == '__main__':
    main()
