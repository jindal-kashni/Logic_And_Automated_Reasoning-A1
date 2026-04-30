import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.parser import parse
from src.ast import Predicate, Const, Var, Implies, Forall, Exists


def test_parse_simple_predicate():
    formula = parse("P(a)")

    assert isinstance(formula, Predicate)
    assert formula.name == "P"
    assert len(formula.terms) == 1
    assert isinstance(formula.terms[0], Const)
    assert formula.terms[0].name == "a"


def test_parse_identity_implication():
    formula = parse("P(a) -> P(a)")

    assert isinstance(formula, Implies)

    assert isinstance(formula.left, Predicate)
    assert formula.left.name == "P"
    assert formula.left.terms[0].name == "a"

    assert isinstance(formula.right, Predicate)
    assert formula.right.name == "P"
    assert formula.right.terms[0].name == "a"


def test_parse_forall_formula():
    formula = parse("forall x. P(x) -> P(a)")

    assert isinstance(formula, Implies)

    assert isinstance(formula.left, Forall)
    assert formula.left.var == "x"
    assert isinstance(formula.left.body, Predicate)
    assert formula.left.body.name == "P"
    assert isinstance(formula.left.body.terms[0], Var)
    assert formula.left.body.terms[0].name == "x"

    assert isinstance(formula.right, Predicate)
    assert formula.right.name == "P"
    assert isinstance(formula.right.terms[0], Const)
    assert formula.right.terms[0].name == "a"


def test_parse_exists_formula():
    formula = parse("exists x. P(x) -> exists y. P(y)")

    assert isinstance(formula, Implies)

    assert isinstance(formula.left, Exists)
    assert formula.left.var == "x"
    assert isinstance(formula.left.body, Predicate)
    assert formula.left.body.name == "P"

    assert isinstance(formula.right, Exists)
    assert formula.right.var == "y"
    assert isinstance(formula.right.body, Predicate)
    assert formula.right.body.name == "P"


def test_invalid_formula_raises_error():
    try:
        parse("P(a")
        assert False, "Expected parser to raise an error for invalid formula"
    except Exception:
        assert True

