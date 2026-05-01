import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ast import Var, Const, Predicate, Forall, Exists, Implies
from src.sequent import Sequent
from src.substitution import free_variables_formula
from src.rules import (
    reset_fresh_counter,
    is_identity,
    existing_terms,
    apply_forall_right,
    apply_exists_left,
    apply_forall_left,
    apply_exists_right,
)


def setup_function(_):
    reset_fresh_counter()


def test_is_identity_matches_same_formula():
    p = Predicate("P", (Const("a"),))
    assert is_identity(Sequent([p], [p]))


def test_is_identity_no_match():
    p = Predicate("P", (Const("a"),))
    q = Predicate("Q", (Const("a"),))
    assert not is_identity(Sequent([p], [q]))


def test_forall_right_uses_fresh_var_not_in_sequent():
    body = Predicate("P", (Var("x"),))
    formula = Forall("x", body)
    sequent = Sequent([], [formula])

    children = apply_forall_right(sequent)

    assert len(children) == 1
    new_right = children[0].right
    new_formula = new_right[0]
    # The introduced eigenvariable must be a Var (not Const) and must be fresh.
    assert isinstance(new_formula, Predicate)
    assert isinstance(new_formula.terms[0], Var)

    fresh_name = new_formula.terms[0].name
    free_in_initial = set()
    for f in sequent.left + sequent.right:
        free_in_initial |= free_variables_formula(f)
    assert fresh_name not in free_in_initial


def test_exists_left_uses_fresh_var_not_in_sequent():
    body = Predicate("P", (Var("x"),))
    formula = Exists("x", body)
    sequent = Sequent([formula], [])

    children = apply_exists_left(sequent)

    assert len(children) == 1
    new_formula = children[0].left[-1]
    assert isinstance(new_formula, Predicate)
    assert isinstance(new_formula.terms[0], Var)


def test_forall_left_instantiates_with_existing_constant():
    # forall x. P(x), <something with constant a>  |- P(a)
    forall = Forall("x", Predicate("P", (Var("x"),)))
    sequent = Sequent([forall], [Predicate("P", (Const("a"),))])

    children = apply_forall_left(sequent)

    assert len(children) == 1
    last = children[0].left[-1]
    # First existing term in this sequent is "a", so the witness is P(a).
    assert last == Predicate("P", (Const("a"),))


def test_forall_left_falls_back_to_fresh_when_no_terms():
    forall = Forall("x", Predicate("P", (Var("x"),)))
    sequent = Sequent([forall], [])

    children = apply_forall_left(sequent)

    assert len(children) == 1
    last = children[0].left[-1]
    assert isinstance(last, Predicate)
    assert isinstance(last.terms[0], Const)


def test_exists_right_instantiates_with_existing_constant():
    exists = Exists("x", Predicate("P", (Var("x"),)))
    sequent = Sequent([Predicate("P", (Const("a"),))], [exists])

    children = apply_exists_right(sequent)

    assert len(children) == 1
    last = children[0].right[-1]
    assert last == Predicate("P", (Const("a"),))


def test_existing_terms_dedupes_by_name():
    f = Predicate("P", (Const("a"), Const("a"), Var("x")))
    sequent = Sequent([f], [])
    names = [t.name for t in existing_terms(sequent)]
    assert names == ["a", "x"]
