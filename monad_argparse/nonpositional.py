from dataclasses import Field, dataclass, fields
from functools import reduce
from typing import Any, Generator, TypeVar

from monad_argparse.done import done
from monad_argparse.flag import flag
from monad_argparse.key_value import KeyValue
from monad_argparse.option import option
from monad_argparse.parser import Parser
from monad_argparse.sequence import Sequence
from monad_argparse.type_ import type_

A = TypeVar("A")


def nonpositional(*parsers: "Parser[Sequence[A]]") -> "Parser[Sequence[A]]":
    """
    >>> from monad_argparse.argument import argument
    >>> from monad_argparse.flag import flag
    >>> p = nonpositional(flag("verbose", default=False), flag("debug", default=False))
    >>> p.parse_args("--verbose", "--debug")
    [('verbose', True), ('debug', True)]
    >>> p.parse_args("--debug", "--verbose")
    [('debug', True), ('verbose', True)]
    >>> p.parse_args()
    [('verbose', False), ('debug', False)]
    >>> p.parse_args("--debug")
    [('verbose', False), ('debug', True)]
    >>> p.parse_args("--verbose")
    [('verbose', True), ('debug', False)]
    >>> p = nonpositional(flag("verbose", default=False), flag("debug", default=False))
    >>> p.parse_args("--verbose", "--debug")
    [('verbose', True), ('debug', True)]
    >>> p.parse_args("--verbose")
    [('verbose', True), ('debug', False)]
    >>> p.parse_args("--debug")
    [('verbose', False), ('debug', True)]
    >>> p.parse_args()
    [('verbose', False), ('debug', False)]
    >>> p = nonpositional(flag("verbose", default=False), flag("debug", default=False), argument("a"))
    >>> p.parse_args("--debug", "hello", "--verbose")
    [('debug', True), ('a', 'hello'), ('verbose', True)]
    """
    if not parsers:
        return Parser[Sequence[A]].empty()

    def get_alternatives():
        for i, head in enumerate(parsers):
            tail = [p for j, p in enumerate(parsers) if j != i]
            yield head >> nonpositional(*tail) >> done()

    return reduce(lambda p1, p2: p1 | p2, get_alternatives())


@dataclass
class Args:
    """
    >>> @dataclass
    ... class MyArgs(Args):
    ...     t: bool = True
    ...     f: bool = False
    ...     i: int = 1
    ...     s: str = "a"
    >>> p = MyArgs()
    >>> MyArgs().parse_args("--no-t", "-f", "-i", "2", "-s", "b")
    [('t', False), ('f', True), ('i', 2), ('s', 'b')]
    >>> MyArgs().parse_args("--no-t")
    [('t', False), ('f', False), ('i', 1), ('s', 'a')]
    """

    @property
    def parser(self) -> Parser[Sequence[KeyValue[Any]]]:
        def get_parsers() -> Generator[Parser, None, None]:
            field: Field
            for field in fields(self):
                if field.type == bool:
                    assert isinstance(
                        field.default, bool
                    ), f"If `field.type == bool`, `field.default` must be a bool, not '{field.default}'."
                    if field.default is True:
                        string = f"--no-{field.name}"
                    else:
                        string = None
                    yield flag(dest=field.name, string=string, default=field.default)
                else:
                    opt = option(dest=field.name, default=field.default)
                    try:
                        t = field.metadata["type"]
                    except (TypeError, KeyError):
                        t = field.type

                    yield type_(t, opt)

        return nonpositional(*get_parsers())

    def parse_args(self, *args):
        return self.parser.parse_args(*args)
