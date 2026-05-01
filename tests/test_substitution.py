import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ast import Var, Const, Predicate, Forall, Exists, And, Implies
from src.substitution import (
    free_variables_formula,
    substitute_formula,
)


def test_free_variables_simple():
    f = Predicate("P", (Var("x"), Const("a")))
    assert free_variables_formula(f) == {"x"}


def test_free_variables_under_quantifier():
    f = Forall("y", Predicate("P", (Var("x"), Var("y"))))
    assert free_variables_formula(f) == {"x"}


def test_substitute_does_not_capture():
    # forall y. P(x, y)  with  x := y  must rename the bound y first.
    body = Predicate("P", (Var("x"), Var("y")))
    formula = Forall("y", body)

    result = substitute_formula(formula, "x", Var("y"))

    assert isinstance(result, Forall)
    # bound variable must have been alpha-renamed away from "y"
    assert result.var != "y"
    # the inner P should reference (y, <renamed>), where y is the substituted x
    assert isinstance(result.body, Predicate)
    assert result.body.terms[0] == Var("y")
    assert result.body.terms[1] == Var(result.var)


def test_substitute_skips_bound_var():
    formula = Forall("x", Predicate("P", (Var("x"),)))
    # substituting x is a no-op because x is bound here
    result = substitute_formula(formula, "x", Const("a"))
    assert result == formula


def test_substitute_existing_var_in_predicate():
    formula = Predicate("P", (Var("x"), Var("y")))
    result = substitute_formula(formula, "x", Const("a"))
    assert result == Predicate("P", (Const("a"), Var("y")))


def test_substitute_into_implies():
    formula = Implies(
        Predicate("P", (Var("x"),)),
        Predicate("Q", (Var("x"),)),
    )
    result = substitute_formula(formula, "x", Const("a"))
    assert result == Implies(
        Predicate("P", (Const("a"),)),
        Predicate("Q", (Const("a"),)),
    )


def test_capture_avoidance_in_exists():
    # exists y. P(x, y)  with  x := y  must rename the bound y.
    formula = Exists("y", Predicate("P", (Var("x"), Var("y"))))
    result = substitute_formula(formula, "x", Var("y"))
    assert isinstance(result, Exists)
    assert result.var != "y"
