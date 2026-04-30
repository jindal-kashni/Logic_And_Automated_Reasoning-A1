fresh_counter = 0

def get_fresh_constant():
    global fresh_counter
    fresh_counter += 1
    return f"c{fresh_counter}"


def reset_fresh_counter():
    global fresh_counter
    fresh_counter = 0


from src.sequent import Sequent


def is_identity(sequent: Sequent) -> bool:
    for left_formula in sequent.left:
        for right_formula in sequent.right:
            if left_formula == right_formula:
                return True
    return False


from src.ast import Implies


def apply_implies_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Implies):
            new_left = sequent.left + [formula.left]
            new_right = [f for f in sequent.right if f != formula]
            new_right.append(formula.right)
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


def apply_implies_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Implies):
            left1 = [f for f in sequent.left if f != formula]
            right1 = sequent.right + [formula.left]

            left2 = [f for f in sequent.left if f != formula] + [formula.right]
            right2 = sequent.right

            new_sequents.append([
                Sequent(left1, right1),
                Sequent(left2, right2),
            ])
    return new_sequents


from src.ast import And


def apply_and_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, And):
            right1 = [f for f in sequent.right if f != formula] + [formula.left]
            right2 = [f for f in sequent.right if f != formula] + [formula.right]
            new_sequents.append([
                Sequent(sequent.left, right1),
                Sequent(sequent.left, right2),
            ])
    return new_sequents


def apply_and_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, And):
            new_left = [f for f in sequent.left if f != formula]
            new_left.extend([formula.left, formula.right])
            new_sequents.append(Sequent(new_left, sequent.right))
    return new_sequents


from src.ast import Or


def apply_or_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Or):
            new_right = [f for f in sequent.right if f != formula]
            new_right.extend([formula.left, formula.right])
            new_sequents.append(Sequent(sequent.left, new_right))
    return new_sequents


def apply_or_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Or):
            left1 = [f for f in sequent.left if f != formula] + [formula.left]
            left2 = [f for f in sequent.left if f != formula] + [formula.right]
            new_sequents.append([
                Sequent(left1, sequent.right),
                Sequent(left2, sequent.right),
            ])
    return new_sequents


from src.ast import Not


def apply_not_right(sequent: Sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Not):
            new_left = sequent.left + [formula.formula]
            new_right = [f for f in sequent.right if f != formula]
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


def apply_not_left(sequent: Sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Not):
            new_left = [f for f in sequent.left if f != formula]
            new_right = sequent.right + [formula.formula]
            new_sequents.append(Sequent(new_left, new_right))
    return new_sequents


from src.ast import Forall, Const
from src.substitution import substitute_formula


def apply_forall_left(sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Forall):
            term = Const(get_fresh_constant())
            new_formula = substitute_formula(formula.body, formula.var, term)

            new_left = sequent.left.copy()
            new_left.append(new_formula)

            new_sequents.append(Sequent(new_left, sequent.right))
    return new_sequents


def apply_forall_right(sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Forall):
            term = Const(get_fresh_constant())
            new_formula = substitute_formula(formula.body, formula.var, term)

            new_right = [f for f in sequent.right if f != formula]
            new_right.append(new_formula)

            new_sequents.append(Sequent(sequent.left, new_right))
    return new_sequents


from src.ast import Exists


def apply_exists_left(sequent):
    new_sequents = []
    for formula in sequent.left:
        if isinstance(formula, Exists):
            term = Const(get_fresh_constant())
            new_formula = substitute_formula(formula.body, formula.var, term)

            new_left = [f for f in sequent.left if f != formula]
            new_left.append(new_formula)

            new_sequents.append(Sequent(new_left, sequent.right))
    return new_sequents


def apply_exists_right(sequent):
    new_sequents = []
    for formula in sequent.right:
        if isinstance(formula, Exists):
            term = Const(get_fresh_constant())
            new_formula = substitute_formula(formula.body, formula.var, term)

            new_right = sequent.right.copy()
            new_right.append(new_formula)

            new_sequents.append(Sequent(sequent.left, new_right))
    return new_sequents