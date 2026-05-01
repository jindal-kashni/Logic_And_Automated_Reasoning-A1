import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.parser import parse
from src.sequent import initial_sequent
from src.improved import prove


def _prove(text):
    return prove(initial_sequent(parse(text)))


def test_propositional_identity():
    assert _prove("P(a) -> P(a)").status == "VALID"


def test_double_negation():
    assert _prove("not not P(a) -> P(a)").status == "VALID"


def test_forall_instantiation():
    assert _prove("(forall x. P(x)) -> P(a)").status == "VALID"


def test_exists_introduction():
    assert _prove("P(a) -> (exists x. P(x))").status == "VALID"


def test_chained_modus_ponens():
    formula = "((P(a) -> Q(a)) and (Q(a) -> R(a))) -> (P(a) -> R(a))"
    assert _prove(formula).status == "VALID"


def test_unprovable_returns_non_valid():
    assert _prove("P(a) -> Q(a)").status != "VALID"
