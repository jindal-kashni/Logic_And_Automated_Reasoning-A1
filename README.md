# Logic-A1

Automated reasoning system for first-order logic using the LK' sequent calculus.

This project implements a baseline version of Algorithm 2 and an improved proof search algorithm for first-order logic. The system reads formulae from a text file, parses them into an internal structure, runs both algorithms, and compares their performance using benchmark results.

## Features

- Reads formulae from a text file
- Supports one formula per line
- Parses first-order logic formulae into an internal AST
- Implements the baseline Algorithm 2 proof search
- Implements an improved proof search method
- Compares baseline and improved results
- Reports validity status, runtime and proof search nodes
- Generates benchmark CSV files and summary tables

## Project Structure

```text
Logic_A1/
    datasets/
        benchmark_dataset.txt
        build_benchmark.py
        sources/
            online_benchmark_F46_F120.txt
    results/
        baseline_results.csv
        improved_results.csv
        table1_overall.csv
        table2_categories.csv
        table3_node_savings.csv
        table4_new_solved.csv
    src/
        source code for parser, rules, baseline, improved algorithm and main runner
    tests/
        basic unit tests
    README.md
    requirements.txt
```

## Dataset Provenance

The benchmark file is `datasets/benchmark_dataset.txt`. It contains four tiers separated by blank lines: Easy with 31 problems, Medium with 30, Hard with 30, and Complex with 30. The Easy tier consists of standard textbook propositional and single-quantifier identities. The other three tiers are problems F46 to F120 of an online benchmark drawn from the following sources:

- [P86] Pelletier, F.J. (1986). Seventy-Five Problems for Testing Automatic Theorem Provers. Journal of Automated Reasoning, 2(2), 191 to 216.
- [TPTP] Sutcliffe, G. (2017). The TPTP Problem Library and Associated Infrastructure. Journal of Automated Reasoning, 59(4), 483 to 502. https://www.tptp.org
- [H09] Harrison, J. (2009). Handbook of Practical Logic and Automated Reasoning. Cambridge University Press.

The annotated source file is `datasets/sources/online_benchmark_F46_F120.txt`. Each formula has a trailing comment with the tier, validity, and source reference. The original file uses textbook syntax with `/\`, `\/`, and `~`. The prover expects course syntax with `and`, `or`, and `not`.

To reproduce the conversion, run:

```bash
python datasets/build_benchmark.py
```

The script reads the annotated source, strips the comments, rewrites the connectives, and writes `datasets/online_benchmark_F46_F120_converted.txt`. The file `benchmark_dataset.txt` contains the Easy tier followed by these converted formulas, with blank lines between tiers so `read_formulas` can detect the categories.
