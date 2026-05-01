from src.ast import (
    Var, Const, Predicate,
    Not, And, Or, Implies, Forall, Exists,
)
from src.sequent import Sequent
from src.substitution import substitute_formula, free_variables_formula


# Fresh-name supply

class FreshSupply:
    """Generate fresh constants and variables that do not collide with names
    already present (free or bound) in a given sequent. A single instance is
    used per proof; callers reset between proofs via reset_fresh_counter().
    """

    def __init__(self):
        self._const_counter = 0
        self._var_counter = 0

    def reset(self):
        self._const_counter = 0
        self._var_counter = 0

    def fresh_const(self, sequent=None):
        used = _sequent_names(sequent) if sequent is not None else set()
        while True:
            self._const_counter += 1
            name = f"c{self._const_counter}"
            if name not in used:
                return Const(name)

    def fresh_var(self, sequent=None):
        used = _sequent_names(sequent) if sequent is not None else set()
        while True:
            self._var_counter += 1
            name = f"v{self._var_counter}"
            if name not in used:
                return Var(name)


_supply = FreshSupply()


def reset_fresh_counter():
    _supply.reset()


def get_fresh_constant():
    # Backwards-compatible name string used by older callers/tests.
    return _supply.fresh_const().name


# Sequent inspection helpers

def _all_names_formula(formula):
    if isinstance(formula, Predicate):
        return {t.name for t in formula.terms}
    if isinstance(formula, Not):
        return _all_names_formula(formula.formula)
    if isinstance(formula, (And, Or, Implies)):
        return _all_names_formula(formula.left) | _all_names_formula(formula.right)
    if isinstance(formula, (Forall, Exists)):
        return {formula.var} | _all_names_formula(formula.body)
    return set()


def _sequent_names(sequent: Sequent):
    names = set()
    for f in list(sequent.left) + list(sequent.right):
        names |= _all_names_formula(f)
    return names


def _consts_in_formula(formula):
    if isinstance(formula, Predicate):
        return [t for t in formula.terms if isinstance(t, Const)]
    if isinstance(formula, Not):
        return _consts_in_formula(formula.formula)
    if isinstance(formula, (And, Or, Implies)):
        return _consts_in_formula(formula.left) + _consts_in_formula(formula.right)
    if isinstance(formula, (Forall, Exists)):
        return _consts_in_formula(formula.body)
    return []


def existing_terms(sequent: Sequent):
    """Constants and free variables already present in the sequent, deduped by
    name. Bound variables inside quantifier bodies are excluded so that
    instantiation does not pick up placeholder names.
    """
    seen = set()
    result = []
    for f in list(sequent.left) + list(sequent.right):
        for term in _consts_in_formula(f):
            if term.name in seen:
                continue
            seen.add(term.name)
            result.append(term)
    free = set()
    for f in list(sequent.left) + list(sequent.right):
        free |= free_variables_formula(f)
    for name in sorted(free):
        if name in seen:
            continue
        seen.add(name)
        result.append(Var(name))
    return result


# Closure

def is_identity(sequent: Sequent) -> bool:
    for left_formula in sequent.left:
        for right_formula in sequent.right:
            if left_formula == right_formula:
                return True
    return False


# Implies

def apply_implies_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Implies):
            new_left = list(sequent.left) + [formula.left]
            new_right = [f for f in sequent.right if f is not formula]
            new_right.append(formula.right)
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


def apply_implies_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Implies):
            remaining_left = [f for f in sequent.left if f is not formula]
            left1 = list(remaining_left)
            right1 = list(sequent.right) + [formula.left]

            left2 = list(remaining_left) + [formula.right]
            right2 = list(sequent.right)

            new_sequents.append([
                Sequent(left1, right1),
                Sequent(left2, right2),
            ])
    return new_sequents


# And

def apply_and_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, And):
            base = [f for f in sequent.right if f is not formula]
            right1 = list(base) + [formula.left]
            right2 = list(base) + [formula.right]
            new_sequents.append([
                Sequent(list(sequent.left), right1),
                Sequent(list(sequent.left), right2),
            ])
    return new_sequents


def apply_and_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, And):
            new_left = [f for f in sequent.left if f is not formula]
            new_left.extend([formula.left, formula.right])
            new_sequents.append(Sequent(new_left, list(sequent.right)))
    return new_sequents


# Or

def apply_or_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Or):
            new_right = [f for f in sequent.right if f is not formula]
            new_right.extend([formula.left, formula.right])
            new_sequents.append(Sequent(list(sequent.left), new_right))
    return new_sequents


def apply_or_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Or):
            base = [f for f in sequent.left if f is not formula]
            left1 = list(base) + [formula.left]
            left2 = list(base) + [formula.right]
            new_sequents.append([
                Sequent(left1, list(sequent.right)),
                Sequent(left2, list(sequent.right)),
            ])
    return new_sequents


# Not

def apply_not_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Not):
            new_left = list(sequent.left) + [formula.formula]
            new_right = [f for f in sequent.right if f is not formula]
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


def apply_not_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Not):
            new_left = [f for f in sequent.left if f is not formula]
            new_right = list(sequent.right) + [formula.formula]
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


# Quantifier rules

def apply_forall_right(sequent: Sequent):
    """Eigenvariable rule: introduce a fresh Var not free in the sequent."""
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Forall):
            eigen = _supply.fresh_var(sequent)
            new_formula = substitute_formula(formula.body, formula.var, eigen)

            new_right = [f for f in sequent.right if f is not formula]
            new_right.append(new_formula)

            new_sequents.append(Sequent(list(sequent.left), new_right))
    return new_sequents


def apply_exists_left(sequent: Sequent):
    """Eigenvariable rule: introduce a fresh Var not free in the sequent."""
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Exists):
            eigen = _supply.fresh_var(sequent)
            new_formula = substitute_formula(formula.body, formula.var, eigen)

            new_left = [f for f in sequent.left if f is not formula]
            new_left.append(new_formula)

            new_sequents.append(Sequent(new_left, list(sequent.right)))
    return new_sequents


def _instantiation_candidates(sequent: Sequent):
    """Existing terms first; fall back to one fresh constant only when the
    sequent is term-empty. Falling back unconditionally would generate a new
    Const each call and prevent the search from ever exhausting a quantifier.
    """
    terms = existing_terms(sequent)
    if terms:
        return terms
    return [_supply.fresh_const(sequent)]


def apply_forall_left(sequent: Sequent):
    """Pick one untried instantiation per Forall on the left. The Forall stays
    in the sequent so further iterations can try other terms.
    """
    new_sequents = []
    for formula in sequent.left:
        if not isinstance(formula, Forall):
            continue
        for term in _instantiation_candidates(sequent):
            new_formula = substitute_formula(formula.body, formula.var, term)
            if new_formula in sequent.left:
                continue
            new_left = list(sequent.left) + [new_formula]
            new_sequents.append(Sequent(new_left, list(sequent.right)))
            break
    return new_sequents


def apply_exists_right(sequent: Sequent):
    """Pick one untried instantiation per Exists on the right."""
    new_sequents = []
    for formula in sequent.right:
        if not isinstance(formula, Exists):
            continue
        for term in _instantiation_candidates(sequent):
            new_formula = substitute_formula(formula.body, formula.var, term)
            if new_formula in sequent.right:
                continue
            new_right = list(sequent.right) + [new_formula]
            new_sequents.append(Sequent(list(sequent.left), new_right))
            break
    return new_sequents
