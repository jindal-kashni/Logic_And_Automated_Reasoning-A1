import time

from src.sequent import Sequent
from src.rules import (
    is_identity,
    reset_fresh_counter,
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
    apply_forall_left,
    apply_exists_right,
)


class ProofResult:
    def __init__(self, status, nodes, time_ms):
        self.status = status
        self.nodes = nodes
        self.time_ms = time_ms

    def __str__(self):
        return f"{self.status} | nodes={self.nodes} | time={self.time_ms:.2f}ms"


def apply_one_rule(sequent: Sequent):
    non_branching_rules = [
        apply_implies_right,
        apply_not_left,
        apply_not_right,
        apply_and_left,
        apply_or_right,
        apply_forall_right,
        apply_exists_left,
    ]

    branching_rules = [
        apply_and_right,
        apply_or_left,
        apply_implies_left,
    ]

    quantifier_repeat_rules = [
        apply_forall_left,
        apply_exists_right,
    ]

    for rule in non_branching_rules:
        results = rule(sequent)
        if results:
            return results[0]

    for rule in branching_rules:
        results = rule(sequent)
        if results:
            return results[0]

    for rule in quantifier_repeat_rules:
        results = rule(sequent)
        if results:
            return results[0]

    return None


def prove(initial: Sequent, max_nodes=1000, max_depth=50, timeout_seconds=5):
    reset_fresh_counter()

    start_time = time.time()
    nodes = 0

    stack = [(initial, 0)]

    while stack:
        if time.time() - start_time > timeout_seconds:
            time_ms = (time.time() - start_time) * 1000
            return ProofResult("TIMEOUT", nodes, time_ms)

        sequent, depth = stack.pop()
        nodes += 1

        if nodes > max_nodes:
            time_ms = (time.time() - start_time) * 1000
            return ProofResult("UNKNOWN", nodes, time_ms)

        if depth > max_depth:
            time_ms = (time.time() - start_time) * 1000
            return ProofResult("UNKNOWN", nodes, time_ms)

        if is_identity(sequent):
            continue

        result = apply_one_rule(sequent)

        if result is None:
            time_ms = (time.time() - start_time) * 1000
            return ProofResult("UNKNOWN", nodes, time_ms)

        if isinstance(result, list):
            for child in result:
                stack.append((child, depth + 1))
        else:
            stack.append((result, depth + 1))

    time_ms = (time.time() - start_time) * 1000
    return ProofResult("VALID", nodes, time_ms)