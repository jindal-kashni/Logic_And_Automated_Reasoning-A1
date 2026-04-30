from dataclasses import dataclass
from typing import List


@dataclass
class Term:
    pass


@dataclass
class Var(Term):
    name: str


@dataclass
class Const(Term):
    name: str


@dataclass
class Formula:
    pass


@dataclass
class Predicate(Formula):
    name: str
    terms: List[Term]


@dataclass
class Not(Formula):
    formula: Formula


@dataclass
class And(Formula):
    left: Formula
    right: Formula


@dataclass
class Or(Formula):
    left: Formula
    right: Formula


@dataclass
class Implies(Formula):
    left: Formula
    right: Formula


@dataclass
class Forall(Formula):
    var: str
    body: Formula


@dataclass
class Exists(Formula):
    var: str
    body: Formula