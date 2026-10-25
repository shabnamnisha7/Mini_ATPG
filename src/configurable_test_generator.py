
import argparse
import csv
import sys
from itertools import product
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configurable_circuit import (
    example_circuit,
    load_circuit_from_json,
)
from configurable_fault_simulator import detect_fault


def generate_input_vectors(input_names):
    """Generate every possible binary input vector."""
    return [
        dict(zip(input_names, values))
        for values in product([0, 1], repeat=len(input_names))
    ]


def generate_fault_list(circuit):
    """Generate stuck-at-0 and stuck-at-1 faults for each modeled signal."""
    signals = list(circuit.inputs)

    for gate in circuit.gates:
        signals.append(gate["output"])

    return [
        (signal, stuck_value)
        for signal in signals
        for stuck_value in (0, 1)
    ]


def find_test_vector(circuit, fault):
    """Find the first input vector that detects a fault."""
    signal, stuck_value = fault

    for vector in generate_input_vectors(circuit.inputs):
        if detect_fault(circuit, vector, signal, stuck_value):
            return vector

    return None


def generate_report(circuit):
    """Generate a detecting-vector report for every modeled fault."""
    report = []

    for signal, stuck_value in generate_fault_list(circuit):
        vector = find_test_vector(circuit, (signal, stuck_value))

        report.append({
            "fault": f"{signal} stuck-at-{stuck_value}",
            "status": "DETECTED" if vector is not None else "UNDETECTED",
            "test_vector": (
                "".join(str(vector[name]) for name in circuit.inputs)
                if vector is not None
                else "N/A"
            ),
        })

    return report


def get_detected_faults(circuit, vector):
    """Return all modeled faults detected by one input vector."""
    detected = set()

    for fault in generate_fault_list(circuit):
        signal, stuck_value = fault

        if detect_fault(circuit, vector, signal, stuck_value):
            detected.add(fault)

    return detected


def compact_test_set(circuit):
    """
    Greedily select input vectors that cover the most remaining detectable
    faults. This is a heuristic and does not guarantee a minimum-size set.
    """
    vectors = generate_input_vectors(circuit.inputs)
    faults = generate_fault_list(circuit)

    coverage = {
        tuple(vector[name] for name in circuit.inputs):
            get_detected_faults(circuit, vector)
        for vector in vectors
    }

    all_detectable = set().union(*coverage.values()) if coverage else set()
    uncovered = set(all_detectable)
    selected = []

    while uncovered:
        best_vector = None
        best_new_faults = set()

        for vector in vectors:
            key = tuple(vector[name] for name in circuit.inputs)
            new_faults = coverage[key] & uncovered

            if len(new_faults) > len(best_new_faults):
                best_vector = vector
                best_new_faults = new_faults

        if best_vector is None or not best_new_faults:
            break

        selected.append({
            "test_vector": "".join(
                str(best_vector[name]) for name in circuit.inputs
            ),
            "new_faults": len(best_new_faults),
            "faults": [
                f"{signal} stuck-at-{value}"
                for signal, value in sorted(best_new_faults)
            ],
        })

        uncovered -= best_new_faults

    return selected, all_detectable, uncovered, faults


def calculate_coverage(report):
    """Return detected count, total count, and modeled fault coverage."""
    total = len(report)
    detected = sum(row["status"] == "DETECTED" for row in report)
    coverage = detected / total * 100 if total else 0.0
    return detected, total, coverage


def save_report_csv(report, output_path):
    """Save the fault report as CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["fault", "status", "test_vector"],
        )
        writer.writeheader()
        writer.writerows(report)

    return output_path


def save_compact_test_set_csv(selected, output_path):
    """Save the greedy compact test set as CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["test_vector", "new_faults", "faults"],
        )
        writer.writeheader()

        for row in selected:
            writer.writerow({
                "test_vector": row["test_vector"],
                "new_faults": row["new_faults"],
                "faults": "; ".join(row["faults"]),
            })

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate and compact test vectors for a logic circuit."
    )

    parser.add_argument(
        "--circuit",
        type=Path,
        default=PROJECT_DIR / "circuits" / "example_circuit.json",
        help="Path to a JSON circuit definition",
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=PROJECT_DIR / "results" / "configurable_fault_report.csv",
        help="Path for the fault report CSV",
    )

    parser.add_argument(
        "--compact-csv",
        type=Path,
        default=PROJECT_DIR / "results" / "configurable_compact_test_set.csv",
        help="Path for the compact test-set CSV",
    )

    parser.add_argument(
        "--use-example",
        action="store_true",
        help="Use the built-in example circuit instead of a JSON file",
    )

    args = parser.parse_args()

    if args.use_example:
        circuit = example_circuit()
        description = "built-in example circuit"
    else:
        circuit = load_circuit_from_json(args.circuit)
        description = str(args.circuit)

    report = generate_report(circuit)
    detected, total, coverage = calculate_coverage(report)
    report_path = save_report_csv(report, args.csv)

    selected, detectable, uncovered, _ = compact_test_set(circuit)
    compact_path = save_compact_test_set_csv(selected, args.compact_csv)

    print("Mini-ATPG: Configurable Test-Pattern Generator")
    print("=" * 65)
    print(f"Circuit: {description}")
    print(f"Inputs: {', '.join(circuit.inputs)}")
    print(f"Output: {circuit.output}")
    print("-" * 65)
    print(f"{'Fault':<25} {'Status':<12} {'Test Vector'}")
    print("-" * 65)

    for row in report:
        print(
            f"{row['fault']:<25} "
            f"{row['status']:<12} "
            f"{row['test_vector']}"
        )

    print("-" * 65)
    print(f"Detected faults: {detected}/{total}")
    print(f"Fault coverage: {coverage:.2f}%")
    print(f"Fault report saved to: {report_path}")

    print("\nGreedy Test-Set Compaction")
    print("-" * 65)

    for index, row in enumerate(selected, start=1):
        print(
            f"{index}. Vector {row['test_vector']} | "
            f"New faults covered: {row['new_faults']}"
        )

    print(f"Selected test vectors: {len(selected)}")
    print(f"Detectable faults covered: {len(detectable) - len(uncovered)}")
    print(f"Uncovered detectable faults: {len(uncovered)}")
    print("Method: greedy heuristic; minimum size is not guaranteed.")
    print(f"Compact test set saved to: {compact_path}")


if __name__ == "__main__":
    main()
