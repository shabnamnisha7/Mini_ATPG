# Mini-ATPG: Automated Test Pattern Generation and Fault Coverage Analysis

## Overview

Mini-ATPG is a Python-based educational tool that demonstrates digital circuit testing concepts used in Design for Testability (DFT). It evaluates a combinational logic circuit, simulates single stuck-at faults, searches for input vectors that detect those faults, and generates fault coverage reports.

The tool also implements a greedy test-set compaction heuristic to select a smaller collection of input vectors that collectively detect the modeled faults.

## Objectives

- Model a combinational logic circuit using Python.
- Simulate single stuck-at-0 and stuck-at-1 faults.
- Automatically find input vectors that distinguish faulty circuit behavior from fault-free behavior.
- Calculate modeled fault coverage.
- Reduce the number of selected test vectors using a greedy heuristic.
- Export fault and test-set reports as CSV files.
- Validate functionality using automated unit tests.

## Circuit Under Test

The tool models the following circuit:

```text
n1 = A AND B
Y  = n1 OR C
```

Equivalent Boolean expression:

**Y = (A · B) + C**

The circuit has three binary inputs, A, B, and C, producing eight possible input combinations.

## Fault Model

The current implementation models single stuck-at faults on five signals:

- A
- B
- C
- n1
- Y

Each signal is tested for two fault conditions:

- Stuck-at-0
- Stuck-at-1

This gives a total of 10 modeled single stuck-at faults.

A fault is considered detected when the faulty circuit output differs from the fault-free output for a particular input vector.

## Methodology

1. Evaluate the fault-free circuit.
2. Generate all eight possible input vectors.
3. Inject each modeled stuck-at fault.
4. Compare faulty and fault-free outputs.
5. Find a detecting vector for each fault, where one exists.
6. Calculate fault coverage for the modeled fault set.
7. Apply greedy test-set compaction to select vectors that detect uncovered faults.
8. Export the results to CSV files.

## Greedy Test-Set Compaction

The compaction algorithm repeatedly selects the input vector that detects the largest number of faults not yet covered. It continues until all detectable modeled faults are covered or no remaining vector can detect an uncovered fault.

This is a greedy heuristic. It does not guarantee the mathematically minimum test set.

## Technologies Used

- Python 3
- Python standard library: `itertools`, `csv`, `pathlib`, and `unittest`
- Visual Studio Code
- PowerShell

No third-party Python packages are required.

## Project Structure

```text
Mini_ATPG/
├── README.md
├── src/
│   ├── circuit.py
│   ├── fault_simulator.py
│   └── test_generator.py
├── tests/
│   └── test_atpg.py
├── results/
│   ├── sample_fault_report.csv
│   └── compact_test_set.csv
└── docs/
```

## How to Run

Run the fault and test-pattern generator from the project root:

```powershell
python .\src\test_generator.py
```

Run the automated unit tests:

```powershell
python -m unittest discover -s tests -v
```

## Current Validation Results

- Modeled single stuck-at faults: 10
- Faults detected: 10
- Modeled fault coverage: 100%
- Selected vectors in the observed greedy run: 4
- Uncovered faults in the observed greedy run: 0
- Automated unit tests passed: 9

These are results for the implemented educational circuit model, not measurements from a fabricated chip or an industrial ATPG tool.

## Output Files

### `results/sample_fault_report.csv`

Contains each modeled fault, its detection status, and a detecting input vector.

### `results/compact_test_set.csv`

Contains the selected input vectors and the faults newly detected by each vector during greedy compaction.

## Limitations

- Supports one small combinational circuit.
- Uses exhaustive enumeration of the circuit's input combinations.
- Models only single stuck-at faults.
- Does not support sequential circuits, timing faults, scan chains, or physical chip testing.
- Uses a greedy compaction heuristic rather than an optimal set-cover solver.
- Has not been compared against a commercial ATPG tool or validated against fabricated hardware.

## Future Improvements

- Support user-defined circuits with multiple logic gates.
- Add more circuit models and fault types.
- Visualize circuit structure and fault propagation.
- Compare greedy compaction with an exact minimum set-cover solution.
- Integrate Verilog simulation using free EDA tools.

## Author

Shabnam Nisha
Electronics and Communication Engineering Student

## Disclaimer

This project is an educational implementation intended to demonstrate basic ATPG and DFT concepts. It is not a replacement for industrial ATPG software.
