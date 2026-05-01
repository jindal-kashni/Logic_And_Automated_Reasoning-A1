import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.parser import parse
from src.sequent import initial_sequent
from src.baseline import prove


def _prove(text):
    return prove(initial_sequent(parse(text)))


def test_propositional_identity():
    result = _prove("P(a) -> P(a)")
    assert result.status == "VALID"


def test_excluded_middle():
    result = _prove("P(a) or not P(a)")
    assert result.status == "VALID"


def test_and_right_requires_both_branches():
    result = _prove("P(a) -> (P(a) and P(a))")
    assert result.status == "VALID"


def test_or_introduction_right():
    result = _prove("P(a) -> (P(a) or Q(a))")
    assert result.status == "VALID"


def test_forall_instantiation_with_existing_constant():
    # The original baseline always used fresh constants and could never close
    # this sequent. After the fix it instantiates with existing terms.
    result = _prove("(forall x. P(x)) -> P(a)")
    assert result.status == "VALID"


def test_modus_ponens_via_forall_left():
    result = _prove("((forall x. (P(x) -> Q(x))) and P(a)) -> Q(a)")
    assert result.status == "VALID"


def test_unprovable_propositional_returns_unknown_or_timeout():
    # Not a tautology: P(a) -> Q(a) cannot close.
    result = _prove("P(a) -> Q(a)")
    assert result.status != "VALID"


def test_consecutive_proofs_isolate_fresh_counter():
    # Ensure fresh-counter reset between calls keeps results independent.
    r1 = _prove("(forall x. P(x)) -> P(a)")
    r2 = _prove("(forall x. P(x)) -> P(a)")
    assert r1.status == "VALID"
    assert r2.status == "VALID"
    assert r1.nodes == r2.nodes
