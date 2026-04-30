import os
import csv
from statistics import mean, median

from src.parser import parse
from src.io_utils import read_formulas
from src.sequent import initial_sequent

from src.baseline import prove as baseline_prove
from src.improved import prove as improved_prove


# report

def print_report_header(total_formulas):
    print()
    print("=" * 70)
    print("LOGIC PROVER BENCHMARK REPORT")
    print("=" * 70)
    print()
    print(f"Total formulas tested : {total_formulas}")
    print()


def print_formula_result(index, formula_text, category, baseline_result, improved_result):
    print("-" * 70)
    print(f"Formula {index:03d}")
    print(f"Category: {category}")
    print(f"Input: {formula_text}")
    print("-" * 70)

    print(
        f"Baseline : {baseline_result.status:<8} "
        f"| nodes: {baseline_result.nodes:<4} "
        f"| time: {baseline_result.time_ms:.2f} ms"
    )

    print(
        f"Improved : {improved_result.status:<8} "
        f"| nodes: {improved_result.nodes:<4} "
        f"| time: {improved_result.time_ms:.2f} ms"
    )

    comparison = get_comparison_message(baseline_result, improved_result)
    print(f"Result   : {comparison}")
    print()


def get_comparison_message(baseline_result, improved_result):
    if baseline_result.status == "UNKNOWN" and improved_result.status == "VALID":
        return "improved algorithm proved this formula"

    if baseline_result.status == "VALID" and improved_result.status == "VALID":
        if improved_result.nodes < baseline_result.nodes:
            return "both valid, improved used fewer nodes"

        if improved_result.time_ms < baseline_result.time_ms:
            return "both valid, improved was faster"

        return "both algorithms proved this formula"

    if baseline_result.status == improved_result.status:
        return "no change"

    return "result changed"


def print_error_result(index, formula_text, category, error):
    print("-" * 70)
    print(f"Formula {index:03d}")
    print(f"Category: {category}")
    print(f"Input: {formula_text}")
    print("-" * 70)
    print("Result   : ERROR")
    print(f"Reason   : {error}")
    print()


def print_summary(total, baseline_valid, improved_valid, improved_gain, error_count):
    baseline_unknown = total - baseline_valid - error_count
    improved_unknown = total - improved_valid - error_count

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Total formulas        : {total}")
    print(f"Successfully tested   : {total - error_count}")
    print(f"Errors                : {error_count}")
    print()
    print(f"Baseline VALID        : {baseline_valid}")
    print(f"Baseline UNKNOWN      : {baseline_unknown}")
    print()
    print(f"Improved VALID        : {improved_valid}")
    print(f"Improved UNKNOWN      : {improved_unknown}")
    print()
    print(f"Improvement gained    : {improved_gain}")
    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print()


# categories

def count_quantifiers(formula_text):
    text = formula_text.lower()
    return text.count("forall") + text.count("exists")


def get_formula_category(formula_text):
    text = formula_text.lower()

    quantifier_count = count_quantifiers(formula_text)
    connective_count = (
        text.count("->")
        + text.count("and")
        + text.count("or")
        + text.count("not")
    )

    if quantifier_count == 0:
        return "Easy propositional"

    if quantifier_count == 1:
        return "Easy FOL"

    if quantifier_count == 2 and connective_count <= 3:
        return "Medium"

    if quantifier_count <= 3:
        return "Hard"

    return "Complex"


def get_reasoning_type(formula_text):
    text = formula_text.lower()

    has_forall = "forall" in text
    has_exists = "exists" in text
    implication_count = text.count("->")
    quantifier_count = count_quantifiers(formula_text)

    if quantifier_count == 0:
        return "Propositional reasoning"

    if has_forall and has_exists:
        return "Mixed forall/exists reasoning"

    if has_forall and implication_count >= 2:
        return "Chained forall instantiation"

    if has_forall:
        return "Forall instantiation"

    if has_exists:
        return "Existential reasoning"

    return "Quantifier reasoning"


# csv helpers

def write_csv(file_path, rows, headers):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def average(values):
    if not values:
        return ""
    return round(mean(values), 2)


def median_value(values):
    if not values:
        return ""
    return round(median(values), 2)


def max_value(values):
    if not values:
        return ""
    return max(values)


def solve_rate(valid_count, total_count):
    if total_count == 0:
        return ""
    return f"{(valid_count / total_count) * 100:.1f}%"


def result_with_nodes(row):
    return f"{row['status']} ({row['nodes']})"


def node_reduction(baseline_nodes, improved_nodes):
    return baseline_nodes - improved_nodes


def node_speedup(baseline_nodes, improved_nodes):
    if improved_nodes == 0:
        return ""
    return f"{baseline_nodes / improved_nodes:.2f}x"


# improvement labels

def get_improvement_responsible(formula_text):
    text = formula_text.lower()

    if "not not" in text or "~~" in text:
        return "Improvement 1: double-negation priority"

    if "forall" in text and "exists" not in text:
        return "Improvement 2: existing-term quantifier instantiation"

    if "forall" in text and "exists" in text:
        return "Improvement 4: DFS backtracking for quantifier choices"

    if "->" in text and ("and" in text or "or" in text):
        return "Improvement 3: memoisation / repeated sequent avoidance"

    return "Improved rule ordering and search control"


# tables

def create_table_1(results_dir, baseline_rows, improved_rows):
    total = len(baseline_rows)

    baseline_valid = sum(1 for r in baseline_rows if r["status"] == "VALID")
    improved_valid = sum(1 for r in improved_rows if r["status"] == "VALID")

    valid_nodes = [
        r["nodes"]
        for r in baseline_rows + improved_rows
        if r["status"] == "VALID"
    ]

    valid_times = [
        r["time_ms"]
        for r in baseline_rows + improved_rows
        if r["status"] == "VALID"
    ]

    table = [
        {
            "Total formulas": total,
            "Baseline VALID": baseline_valid,
            "Improved VALID": improved_valid,
            "Solve rate baseline": solve_rate(baseline_valid, total),
            "Solve rate improved": solve_rate(improved_valid, total),
            "Avg nodes": average(valid_nodes),
            "Avg time": average(valid_times),
        }
    ]

    write_csv(
        os.path.join(results_dir, "table1_overall.csv"),
        table,
        [
            "Total formulas",
            "Baseline VALID",
            "Improved VALID",
            "Solve rate baseline",
            "Solve rate improved",
            "Avg nodes",
            "Avg time",
        ]
    )


def create_table_2(results_dir, baseline_rows, improved_rows):
    category_order = [
        "Easy propositional",
        "Easy FOL",
        "Medium",
        "Hard",
        "Complex",
    ]

    categories = [
        category
        for category in category_order
        if any(r["category"] == category for r in baseline_rows)
    ]

    table = []

    for category in categories:
        baseline_category = [r for r in baseline_rows if r["category"] == category]
        improved_category = [r for r in improved_rows if r["category"] == category]

        count = len(baseline_category)
        baseline_solved = sum(1 for r in baseline_category if r["status"] == "VALID")
        improved_solved = sum(1 for r in improved_category if r["status"] == "VALID")

        table.append({
            "Category": category,
            "Count": count,
            "Baseline solved": baseline_solved,
            "Improved solved": improved_solved,
            "Baseline %": solve_rate(baseline_solved, count),
            "Improved %": solve_rate(improved_solved, count),
        })

    write_csv(
        os.path.join(results_dir, "table2_categories.csv"),
        table,
        [
            "Category",
            "Count",
            "Baseline solved",
            "Improved solved",
            "Baseline %",
            "Improved %",
        ]
    )


def create_table_3(results_dir, baseline_rows, improved_rows):
    candidates = []

    for baseline, improved in zip(baseline_rows, improved_rows):
        both_valid = baseline["status"] == "VALID" and improved["status"] == "VALID"
        improved_uses_fewer_nodes = improved["nodes"] < baseline["nodes"]

        if both_valid and improved_uses_fewer_nodes:
            candidates.append({
                "Formula": baseline["formula_label"],
                "Category": baseline["category"],
                "Baseline nodes": baseline["nodes"],
                "Improved nodes": improved["nodes"],
                "Nodes reduced": node_reduction(baseline["nodes"], improved["nodes"]),
                "Node speedup": node_speedup(baseline["nodes"], improved["nodes"]),
                "Improvement responsible": get_improvement_responsible(baseline["formula"]),
                "Formula text": baseline["formula"],
            })

    candidates.sort(key=lambda row: row["Nodes reduced"], reverse=True)
    table = candidates[:5]

    write_csv(
        os.path.join(results_dir, "table3_node_savings.csv"),
        table,
        [
            "Formula",
            "Category",
            "Baseline nodes",
            "Improved nodes",
            "Nodes reduced",
            "Node speedup",
            "Improvement responsible",
            "Formula text",
        ]
    )


def create_table_4(results_dir, baseline_rows, improved_rows):
    candidates = []

    for baseline, improved in zip(baseline_rows, improved_rows):
        newly_solved = baseline["status"] != "VALID" and improved["status"] == "VALID"

        if newly_solved:
            candidates.append({
                "Formula": baseline["formula_label"],
                "Category": baseline["category"],
                "Baseline result (nodes)": result_with_nodes(baseline),
                "Improved result (nodes)": result_with_nodes(improved),
                "Improvement responsible": get_improvement_responsible(baseline["formula"]),
                "Formula text": baseline["formula"],
            })

    candidates.sort(key=lambda row: row["Formula"])
    table = candidates[:10]

    write_csv(
        os.path.join(results_dir, "table4_new_solved.csv"),
        table,
        [
            "Formula",
            "Category",
            "Baseline result (nodes)",
            "Improved result (nodes)",
            "Improvement responsible",
            "Formula text",
        ]
    )


def create_all_csv_files(results_dir, baseline_rows, improved_rows):
    raw_headers = [
        "formula_id",
        "formula_label",
        "formula",
        "category",
        "status",
        "nodes",
        "time_ms",
    ]

    write_csv(
        os.path.join(results_dir, "baseline_results.csv"),
        baseline_rows,
        raw_headers
    )

    write_csv(
        os.path.join(results_dir, "improved_results.csv"),
        improved_rows,
        raw_headers
    )

    create_table_1(results_dir, baseline_rows, improved_rows)
    create_table_2(results_dir, baseline_rows, improved_rows)
    create_table_3(results_dir, baseline_rows, improved_rows)
    create_table_4(results_dir, baseline_rows, improved_rows)

# main

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    file_path = os.path.join(base_dir, "datasets", "benchmark_dataset.txt")
    results_dir = os.path.join(base_dir, "results")

    os.makedirs(results_dir, exist_ok=True)

    formulas = read_formulas(file_path)

    baseline_valid = 0
    improved_valid = 0
    improved_gain = 0
    error_count = 0

    baseline_rows = []
    improved_rows = []

    print_report_header(len(formulas))

    for index, formula_text in enumerate(formulas, start=1):
        category = get_formula_category(formula_text)
        formula_label = f"F{index}"

        try:
            formula = parse(formula_text)
            sequent = initial_sequent(formula)

            baseline_result = baseline_prove(sequent)
            improved_result = improved_prove(sequent)

            print_formula_result(
                index,
                formula_text,
                category,
                baseline_result,
                improved_result
            )

            baseline_rows.append({
                "formula_id": index,
                "formula_label": formula_label,
                "formula": formula_text,
                "category": category,
                "status": baseline_result.status,
                "nodes": baseline_result.nodes,
                "time_ms": round(baseline_result.time_ms, 2),
            })

            improved_rows.append({
                "formula_id": index,
                "formula_label": formula_label,
                "formula": formula_text,
                "category": category,
                "status": improved_result.status,
                "nodes": improved_result.nodes,
                "time_ms": round(improved_result.time_ms, 2),
            })

            if baseline_result.status == "VALID":
                baseline_valid += 1

            if improved_result.status == "VALID":
                improved_valid += 1

            if baseline_result.status != "VALID" and improved_result.status == "VALID":
                improved_gain += 1

        except Exception as error:
            error_count += 1

            print_error_result(
                index,
                formula_text,
                category,
                error
            )

            baseline_rows.append({
                "formula_id": index,
                "formula_label": formula_label,
                "formula": formula_text,
                "category": category,
                "status": "ERROR",
                "nodes": 0,
                "time_ms": 0.0,
            })

            improved_rows.append({
                "formula_id": index,
                "formula_label": formula_label,
                "formula": formula_text,
                "category": category,
                "status": "ERROR",
                "nodes": 0,
                "time_ms": 0.0,
            })

    create_all_csv_files(results_dir, baseline_rows, improved_rows)

    print_summary(
        len(formulas),
        baseline_valid,
        improved_valid,
        improved_gain,
        error_count
    )

    print("CSV files saved in results folder:")


if __name__ == "__main__":
    main()