from dataclasses import Field, dataclass, fields
from functools import reduce
from typing import Generator, TypeVar, Union

from monad_argparse.parser.done import Done
from monad_argparse.parser.flag import Flag
from monad_argparse.parser.option import Option
from monad_argparse.parser.parser import Parser
from monad_argparse.parser.sequence import Sequence
from monad_argparse.parser.type_ import Type

A = TypeVar("A")


def nonpositional(*parsers: "Parser[Sequence[A]]") -> "Parser[Sequence[A]]":
    """
    >>> from monad_argparse import Argument, Flag
    >>> p = nonpositional(Flag("verbose"), Flag("debug"))
    >>> p.parse_args("--verbose", "--debug")
    [('verbose', True), ('debug', True)]
    >>> p.parse_args("--debug", "--verbose")
    [('debug', True), ('verbose', True)]
    >>> p.parse_args()
    MissingError(missing='--debug')
    >>> p.parse_args("--debug")
    MissingError(missing='--verbose')
    >>> p.parse_args("--verbose")
    UnequalError(left='--verbose', right='--debug')
    >>> p = nonpositional(
    ...   Flag("verbose") | Parser.key_values(verbose=False),
    ...   Flag("debug") | Parser.key_values(debug=False)
    ... )
    >>> p.parse_args("--verbose", "--debug")
    [('verbose', True), ('debug', True)]
    >>> p.parse_args("--verbose")
    [('verbose', True), ('debug', False)]
    >>> p.parse_args("--debug")
    [('verbose', False), ('debug', True)]
    >>> p.parse_args()
    [('verbose', False), ('debug', False)]
    >>> p = nonpositional(Flag("verbose"), Flag("debug"), Argument("a"))
    >>> p.parse_args("--debug", "hello", "--verbose")
    [('debug', True), ('a', 'hello'), ('verbose', True)]
    """
    if not parsers:
        return Parser[Sequence[A]].empty()

    def get_alternatives():
        for i, head in enumerate(parsers):
            tail = [p for j, p in enumerate(parsers) if j != i]
            yield head >> nonpositional(*tail) >> Done()

    return reduce(lambda p1, p2: p1 | p2, get_alternatives())


@dataclass
class Args:
    # """
    # >>> @dataclass
    # ... class MyArgs(Args):
    # ...     t: bool = True
    # ...     f: bool = False
    # ...     i: int = 1
    # ...     s: str = "a"
    # >>> MyArgs().parse_args("-t", "-f", "-i", "2", "-s", "b")
    # [('t', True), ('f', True), ('i', 2), ('s', 'b')]
    # """

    @property
    def parser(self) -> Parser:
        def get_parsers() -> Generator[Union[Flag, Type], None, None]:
            field: Field
            for field in fields(self):
                if field.type == bool:
                    assert isinstance(
                        field.default, bool
                    ), f"If `field.type == bool`, `field.default` must be a bool, not '{field.default}'."
                    # if field.default is False:
                    #     if len(field.name) == 1:
                    #         short = field.name
                    #         long = None
                    #     else:
                    #         short = None
                    #         long = field.name
                    # else:
                    short = None
                    long = f"no-{field.name}"
                    yield Flag(long=long, short=short, dest=field.name)
                else:

                    # if len(field.name) == 1:
                    #     short = field.name
                    #     long = None
                    # else:
                    #     short = None
                    #     long = field.name
                    option = Option(short=None, long=field.name)
                    try:
                        t = field.metadata["type"]
                    except (TypeError, KeyError):
                        t = field.type

                    yield Type(t, option)

        return nonpositional(*get_parsers())

    def parse_args(self, *args):
        return self.parser.parse_args(*args)


if __name__ == "__main__":
    from monad_argparse import Argument

    p = nonpositional(
        Flag("verbose"),
        Flag("debug"),
        Argument("a"),
    )
    print(repr(p.parse_args("hello", "--debug")))

    # @dataclass
    # class MyArgs(Args):
    #     t: bool = True
    #     f: bool = False
    #     i: int = 1
    #     s: str = "a"

    # print(repr(MyArgs().parse_args("--no-t", "-f", "-i", "2", "-s", "b")))
    # print(repr(MyArgs().parse_args()))
