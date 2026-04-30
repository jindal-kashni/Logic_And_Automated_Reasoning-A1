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
├── datasets/
│   └── benchmark_dataset.txt
├── results/
│   ├── baseline_results.csv
│   ├── improved_results.csv
│   ├── table1_overall.csv
│   ├── table2_categories.csv
│   ├── table3_node_savings.csv
│   └── table4_new_solved.csv
├── src/
│   └── source code for parser, rules, baseline, improved algorithm and main runner
├── tests/
│   └── basic unit tests
├── README.md
└── requirements.txt