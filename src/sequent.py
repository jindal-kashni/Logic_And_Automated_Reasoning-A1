from dataclasses import dataclass
from typing import List
from src.ast import Formula

@dataclass
class Sequent:
    left: List[Formula]
    right: List[Formula]

    def __str__(self):
        left_str = ", ".join(str(f) for f in self.left)
        right_str = ", ".join(str(f) for f in self.right)
        return f"{left_str} |- {right_str}"

def initial_sequent(formula: Formula) -> Sequent:
    return Sequent(left=[], right=[formula])