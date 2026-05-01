import time
import heapq

from src.ast import (
    Var, Const, Predicate,
    Not, And, Or, Implies, Forall, Exists,
)
from src.sequent import Sequent
from src.substitution import substitute_formula
import src.rules as _rules
from src.rules import (
    is_identity,
    existing_terms,
    apply_implies_right,
    apply_not_left,
    apply_not_right,
    apply_and_left,
    apply_or_right,
    apply_forall_right,
    apply_exists_left,
    apply_and_right,
    apply_or_left,
    apply_implies_left,
)


class ProofResult:
    def __init__(self, status, nodes, time_ms):
        self.status = status
        self.nodes = nodes
        self.time_ms = time_ms

    def __str__(self):
        return f"{self.status} | nodes={self.nodes} | time={self.time_ms:.2f}ms"


# Simplification

def simplify_formula(formula):
    if isinstance(formula, Not):
        inner = simplify_formula(formula.formula)
        if isinstance(inner, Not):
            return simplify_formula(inner.formula)
        return Not(inner)

    if isinstance(formula, And):
        return And(
            simplify_formula(formula.left),
            simplify_formula(formula.right),
        )

    if isinstance(formula, Or):
        return Or(
            simplify_formula(formula.left),
            simplify_formula(formula.right),
        )

    if isinstance(formula, Implies):
        return Implies(
            simplify_formula(formula.left),
            simplify_formula(formula.right),
        )

    if isinstance(formula, Forall):
        return Forall(formula.var, simplify_formula(formula.body))

    if isinstance(formula, Exists):
        return Exists(formula.var, simplify_formula(formula.body))

    return formula


def simplify_sequent(sequent):
    return Sequent(
        [simplify_formula(f) for f in sequent.left],
        [simplify_formula(f) for f in sequent.right],
    )


# Quantifier helpers

def innermost_quantifier_body(formula):
    current = formula
    while isinstance(current, Forall):
        current = current.body
    return current


def formula_is_available(formula, left_formulas):
    if formula in left_formulas:
        return True

    if isinstance(formula, And):
        return (
            formula_is_available(formula.left, left_formulas)
            and formula_is_available(formula.right, left_formulas)
        )

    if isinstance(formula, Or):
        return (
            formula_is_available(formula.left, left_formulas)
            or formula_is_available(formula.right, left_formulas)
        )

    return False


def apply_ready_implies_left(sequent):
    for index, formula in enumerate(sequent.left):
        if not isinstance(formula, Implies):
            continue

        if not formula_is_available(formula.left, sequent.left):
            continue

        remaining_left = sequent.left[:index] + sequent.left[index + 1:]

        branch_1 = Sequent(remaining_left, list(sequent.right) + [formula.left])
        branch_2 = Sequent(list(remaining_left) + [formula.right], list(sequent.right))

        return [[branch_1, branch_2]]

    return []


def _improved_candidates(sequent):
    terms = existing_terms(sequent)
    if terms:
        return terms
    fresh = _rules._supply.fresh_const(sequent)
    return [fresh]


def improved_forall_left(sequent, memory):
    forall_formulas = [
        formula for formula in sequent.left if isinstance(formula, Forall)
    ]

    def forall_priority(formula):
        body = innermost_quantifier_body(formula)
        if isinstance(body, Or):
            return 0
        if isinstance(body, Implies):
            return 1
        if isinstance(body, Exists):
            return 4
        return 2

    forall_formulas.sort(key=forall_priority)

    for formula in forall_formulas:
        for term in _improved_candidates(sequent):
            key = (str(formula), str(term))
            if key in memory:
                continue

            new_formula = substitute_formula(formula.body, formula.var, term)
            if new_formula in sequent.left:
                # Already present in this branch; do not poison memory so
                # later sequents (with different left sets) can still try it.
                continue

            memory.add(key)
            new_left = list(sequent.left) + [new_formula]
            return [Sequent(new_left, list(sequent.right))]

    return []


def improved_exists_right(sequent, memory):
    for formula in sequent.right:
        if not isinstance(formula, Exists):
            continue
        for term in _improved_candidates(sequent):
            key = (str(formula), str(term))
            if key in memory:
                continue

            new_formula = substitute_formula(formula.body, formula.var, term)
            if new_formula in sequent.right:
                continue

            memory.add(key)
            new_right = list(sequent.right) + [new_formula]
            return [Sequent(list(sequent.left), new_right)]

    return []


# Complexity / cache key

def formula_complexity(formula):
    if isinstance(formula, Predicate):
        return 1
    if isinstance(formula, Not):
        return 1 + formula_complexity(formula.formula)
    if isinstance(formula, (And, Or, Implies)):
        return 1 + formula_complexity(formula.left) + formula_complexity(formula.right)
    if isinstance(formula, (Forall, Exists)):
        return 1 + formula_complexity(formula.body)
    return 1


def sequent_complexity(sequent):
    return sum(formula_complexity(f) for f in list(sequent.left) + list(sequent.right))


def sequent_key(sequent):
    left = tuple(sorted(str(f) for f in sequent.left))
    right = tuple(sorted(str(f) for f in sequent.right))
    return left, right


# Rule application

def apply_one_improved_rule(sequent, memory):
    non_branching = [
        apply_implies_right,
        apply_not_left,
        apply_not_right,
        apply_and_left,
        apply_or_right,
        apply_forall_right,
        apply_exists_left,
    ]

    for rule in non_branching:
        result = rule(sequent)
        if result:
            return result[0]

    result = apply_and_right(sequent)
    if result:
        branches = result[0]
        branches.sort(key=sequent_complexity)
        return branches

    result = apply_ready_implies_left(sequent)
    if result:
        branches = result[0]
        branches.sort(key=sequent_complexity)
        return branches

    result = improved_exists_right(sequent, memory)
    if result:
        return result[0]

    result = improved_forall_left(sequent, memory)
    if result:
        return result[0]

    result = apply_or_left(sequent)
    if result:
        branches = result[0]
        branches.sort(key=sequent_complexity)
        return branches

    result = apply_implies_left(sequent)
    if result:
        branches = result[0]
        branches.sort(key=sequent_complexity)
        return branches

    return None


# Search

def prove(initial, max_nodes=2000, max_depth=80, timeout_seconds=5):
    _rules.reset_fresh_counter()

    start = time.time()
    nodes = 0
    visited = set()
    queue = []
    counter = 0

    initial = simplify_sequent(initial)

    heapq.heappush(
        queue,
        (sequent_complexity(initial), counter, initial, 0, set()),
    )

    while queue:
        if time.time() - start > timeout_seconds:
            return ProofResult("TIMEOUT", nodes, (time.time() - start) * 1000)

        _, _, sequent, depth, memory = heapq.heappop(queue)
        nodes += 1

        if nodes > max_nodes or depth > max_depth:
            return ProofResult("UNKNOWN", nodes, (time.time() - start) * 1000)

        key = sequent_key(sequent)
        if key in visited:
            continue
        visited.add(key)

        if is_identity(sequent):
            continue

        result = apply_one_improved_rule(sequent, memory)

        if result is None:
            return ProofResult("UNKNOWN", nodes, (time.time() - start) * 1000)

        if isinstance(result, list):
            for child in result:
                counter += 1
                heapq.heappush(
                    queue,
                    (
                        sequent_complexity(child),
                        counter,
                        child,
                        depth + 1,
                        set(memory),
                    ),
                )
        else:
            counter += 1
            heapq.heappush(
                queue,
                (
                    sequent_complexity(result),
                    counter,
                    result,
                    depth + 1,
                    memory,
                ),
            )

    return ProofResult("VALID", nodes, (time.time() - start) * 1000)
