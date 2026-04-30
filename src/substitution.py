from src.ast import *

def substitute_term(term: Term, var_name: str, replacement: Term) -> Term:
    if isinstance(term, Var) and term.name == var_name:
        return replacement
    return term

def substitute_formula(formula: Formula, var_name: str, replacement: Term) -> Formula:
    if isinstance(formula, Predicate):
        new_terms = [
            substitute_term(term, var_name, replacement)
            for term in formula.terms
        ]
        return Predicate(formula.name, new_terms)

    if isinstance(formula, Not):
        return Not(substitute_formula(formula.formula, var_name, replacement))

    if isinstance(formula, And):
        return And(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement)
        )

    if isinstance(formula, Or):
        return Or(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement)
        )

    if isinstance(formula, Implies):
        return Implies(
            substitute_formula(formula.left, var_name, replacement),
            substitute_formula(formula.right, var_name, replacement)
        )

    if isinstance(formula, Forall):
        if formula.var == var_name:
            return formula
        return Forall(
            formula.var,
            substitute_formula(formula.body, var_name, replacement)
        )

    if isinstance(formula, Exists):
        if formula.var == var_name:
            return formula
        return Exists(
            formula.var,
            substitute_formula(formula.body, var_name, replacement)
        )

    return formula