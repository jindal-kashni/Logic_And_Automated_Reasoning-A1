import time
import heapq

from src.ast import *
from src.sequent import Sequent
from src.substitution import substitute_formula
import src.rules as _rules
from src.rules import (
    is_identity,
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

# Result class

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

# Closure Check

def is_closed(sequent):
    if is_identity(sequent):
        return True

    for left_formula in sequent.left:
        for right_formula in sequent.right:
            if left_formula == right_formula:
                return True

    return False

# Term Extraction

def collect_terms_from_formula(formula):
    terms = []

    if isinstance(formula, Predicate):
        for term in formula.terms:
            if isinstance(term, Const):
                terms.append(term)

    elif isinstance(formula, Not):
        terms.extend(collect_terms_from_formula(formula.formula))

    elif isinstance(formula, (And, Or, Implies)):
        terms.extend(collect_terms_from_formula(formula.left))
        terms.extend(collect_terms_from_formula(formula.right))

    elif isinstance(formula, (Forall, Exists)):
        terms.extend(collect_terms_from_formula(formula.body))

    return terms


def existing_terms(sequent):
    terms = []

    for formula in sequent.left + sequent.right:
        terms.extend(collect_terms_from_formula(formula))

    unique = []
    seen = set()

    for term in terms:
        key = str(term)
        if key not in seen:
            seen.add(key)
            unique.append(term)

    return unique

# Fresh constant

MAX_FRESH = 50
fresh_counter = 0

def reset_fresh_counter():
    global fresh_counter
    fresh_counter = 0


def get_fresh_constant():
    global fresh_counter

    if fresh_counter >= MAX_FRESH:
        return None

    fresh_counter += 1
    return Const(f"k{fresh_counter}")

# Quantifier Rules

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

        remaining_left = (
            sequent.left[:index]
            + sequent.left[index + 1:]
        )

        branch_1 = Sequent(
            remaining_left,
            sequent.right + [formula.left],
        )

        branch_2 = Sequent(
            remaining_left + [formula.right],
            sequent.right,
        )

        return [[branch_1, branch_2]]

    return []


def improved_forall_left(sequent, memory):
    terms = existing_terms(sequent)

    if not terms:
        fresh = get_fresh_constant()
        if fresh is None:
            return []
        terms = [fresh]

    forall_formulas = [
        formula for formula in sequent.left
        if isinstance(formula, Forall)
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
        for term in terms:
            key = (str(formula), str(term))

            if key in memory:
                continue

            memory.add(key)

            new_formula = substitute_formula(
                formula.body,
                formula.var,
                term,
            )

            if new_formula in sequent.left:
                continue

            new_left = sequent.left.copy()
            new_left.append(new_formula)

            return [Sequent(new_left, sequent.right)]

    return []


def improved_exists_right(sequent, memory):
    terms = existing_terms(sequent)

    if not terms:
        fresh = get_fresh_constant()
        if fresh is None:
            return []
        terms = [fresh]

    for formula in sequent.right:
        if isinstance(formula, Exists):
            for term in terms:
                key = (str(formula), str(term))

                if key in memory:
                    continue

                memory.add(key)

                new_formula = substitute_formula(
                    formula.body,
                    formula.var,
                    term,
                )

                new_right = sequent.right.copy()
                new_right.append(new_formula)

                return [Sequent(sequent.left, new_right)]

    return []

# Complexity

def formula_complexity(formula):
    if isinstance(formula, Predicate):
        return 1

    if isinstance(formula, Not):
        return 1 + formula_complexity(formula.formula)

    if isinstance(formula, (And, Or, Implies)):
        return (
            1
            + formula_complexity(formula.left)
            + formula_complexity(formula.right)
        )

    if isinstance(formula, (Forall, Exists)):
        return 1 + formula_complexity(formula.body)

    return 1


def sequent_complexity(sequent):
    return sum(
        formula_complexity(formula)
        for formula in sequent.left + sequent.right
    )

# Caching (sequent key)

def sequent_key(sequent):
    left = tuple(sorted(str(formula) for formula in sequent.left))
    right = tuple(sorted(str(formula) for formula in sequent.right))
    return left, right

# Rule application

def apply_one_improved_rule(sequent, memory):
    sequent = simplify_sequent(sequent)

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

# Prove Search

def prove(initial, max_nodes=2000, max_depth=80, timeout_seconds=5):
    reset_fresh_counter()
    _rules.reset_fresh_counter()

    start = time.time()
    nodes = 0
    visited = set()
    queue = []
    counter = 0

    initial = simplify_sequent(initial)

    heapq.heappush(
        queue,
        (
            sequent_complexity(initial),
            counter,
            initial,
            0,
            set(),
        ),
    )

    while queue:
        if time.time() - start > timeout_seconds:
            return ProofResult(
                "TIMEOUT",
                nodes,
                (time.time() - start) * 1000,
            )

        _, _, sequent, depth, memory = heapq.heappop(queue)
        nodes += 1

        if nodes > max_nodes or depth > max_depth:
            return ProofResult(
                "UNKNOWN",
                nodes,
                (time.time() - start) * 1000,
            )

        sequent = simplify_sequent(sequent)

        key = sequent_key(sequent)

        if key in visited:
            continue

        visited.add(key)

        if is_closed(sequent):
            continue

        result = apply_one_improved_rule(sequent, memory)

        if result is None:
            return ProofResult(
                "UNKNOWN",
                nodes,
                (time.time() - start) * 1000,
            )

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
                        memory.copy(),
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
                    memory.copy(),
                ),
            )

    return ProofResult(
        "VALID",
        nodes,
        (time.time() - start) * 1000,
    )