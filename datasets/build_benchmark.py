import os
import re


SOURCE_FILE = "online_benchmark_F46_F120.txt"
OUTPUT_FILE = "online_benchmark_F46_F120_converted.txt"


def strip_comments_and_blanks(text):
    formulas = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        formulas.append(stripped)
    return formulas


def to_course_syntax(formula):
    formula = formula.replace("/\\", " and ")
    formula = formula.replace("\\/", " or ")
    formula = re.sub(r"~\s*", "not ", formula)
    formula = re.sub(r"\s+", " ", formula)
    return formula.strip()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(here, "sources", SOURCE_FILE)
    out_path = os.path.join(here, OUTPUT_FILE)

    with open(src_path, "r", encoding="utf-8") as f:
        annotated = f.read()

    raw_formulas = strip_comments_and_blanks(annotated)
    converted = [to_course_syntax(formula) for formula in raw_formulas]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(converted) + "\n")

    print(f"Read    : {len(raw_formulas)} formulas from {src_path}")
    print(f"Wrote   : {len(converted)} formulas to {out_path}")


if __name__ == "__main__":
    main()
