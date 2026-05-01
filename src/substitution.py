from src.ast import (
    Term, Var, Const, Formula, Predicate,
    Not, And, Or, Implies, Forall, Exists,
)


def free_variables_term(term: Term):
    if isinstance(term, Var):
        return {term.name}
    return set()


def free_variables_formula(formula: Formula):
    if isinstance(formula, Predicate):
        result = set()
        for term in formula.terms:
            result |= free_variables_term(term)
        return result
    if isinstance(formula, Not):
        return free_variables_formula(formula.formula)
    if isinstance(formula, (And, Or, Implies)):
        return free_variables_formula(formula.left) | free_variables_formula(formula.right)
    if isinstance(formula, (Forall, Exists)):
        return free_variables_formula(formula.body) - {formula.var}
    return set()


def _fresh_name(base: str, used):
    candidate = base
    i = 0
    while candidate in used:
        i += 1
        candidate = f"{base}_{i}"
    return candidate


def substitute_term(term: Term, var_name: str, replacement: Term) -> Term:
    if isinstance(term, Var) and term.name == var_name:
        return replacement
    return term


def substitute_formula(formula: Formula, var_name: str, replacement: Term) -> Formula:
    if isinstance(formula, Predicate):
        new_terms = tuple(
            substitute_term(term, var_name, replacement)
            for term in formula.terms
        )
        return Predicate(formula.name, new_terms)

    if isinstance(formula, Not):
        return Not(substitute_formula(formula.formula, var_name, replacement))

    if isinstance(formula, And):
        return And(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement),
        )

    if isinstance(formula, Or):
        return Or(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement),
        )

    if isinstance(formula, Implies):
        return Implies(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement),
        )

    if isinstance(formula, (Forall, Exists)):
        if formula.var == var_name:
            return formula

        replacement_free = free_variables_term(replacement)

        # Capture-avoidance: rename the bound variable when the replacement
        # would otherwise be captured by it.
        if formula.var in replacement_free:
            used = (
                free_variables_formula(formula.body)
                | replacement_free
                | {var_name}
            )
            new_bound = _fresh_name(formula.var, used)
            renamed_body = substitute_formula(
                formula.body, formula.var, Var(new_bound)
            )
            new_body = substitute_formula(renamed_body, var_name, replacement)
            return type(formula)(new_bound, new_body)

        new_body = substitute_formula(formula.body, var_name, replacement)
        return type(formula)(formula.var, new_body)

    return formula
