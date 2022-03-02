from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type, TypeVar

from monad_argparse.monad.monoid import MonadPlus, Monoid
from monad_argparse.parser.error import ArgumentError  # , MissingError

A = TypeVar("A", covariant=True)
B = TypeVar("B", covariant=True, bound=Monoid)
C = TypeVar("C", bound=Monoid)


@dataclass
class Result(MonadPlus[B]):
    get: B | Exception

    def __add__(self, other: Result[C]) -> Result[B | C]:
        # if isinstance(self.get, MissingError):
        #     if isinstance(other.get, MissingError):
        #         return Result(MissingError(self.get.default | self.get.default))
        #     if not isinstance(other.get, Exception):
        #         return Result(self.get.default | other.get)
        #     if isinstance(other.get, Exception):
        #         return Result(self.get.default | other.get)
        #     raise RuntimeError("unreachable")
        # if isinstance(self.get, Exception):
        #     return other
        # if not isinstance(self.get, Exception):
        #     if not isinstance(other.get, Exception):
        #         return Result(self.get | other.get)
        #     return other | self
        if not isinstance(self.get, Exception):
            return self
        if not isinstance(other.get, Exception):
            return other
        return self

    def __repr__(self):
        return f"Result({self.get})"

    def bind(self, f: Callable[[B], Result[C]]) -> Result[C]:
        y = self.get
        if isinstance(y, Exception):
            return Result(y)
        return f(y)

    @classmethod
    def return_(cls: "Type[Result[B]]", a: C) -> "Result[C]":
        return Result(a)

    @classmethod
    def zero(cls: "Type[Result[B]]") -> "Result[B]":
        return Result(ArgumentError(description="zero"))
