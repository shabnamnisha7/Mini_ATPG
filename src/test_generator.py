
import csv
from itertools import product
from pathlib import Path

from circuit import evaluate_circuit
from fault_simulator import detect_fault


FAULT_SIGNALS = ["A", "B", "C", "n1", "Y"]
STUCK_VALUES = [0, 1]


def generate_all_vectors():
    """Generate all possible three-input binary vectors."""
    return list(product([0, 1], repeat=3))


def generate_all_faults():
    """Generate all modeled single stuck-at faults."""
    return [
        (signal, value)
        for signal in FAULT_SIGNALS
        for value in STUCK_VALUES
    ]


def find_test_for_fault(fault):
    """Find the first input vector that detects a fault."""
    signal, stuck_value = fault

    for vector in generate_all_vectors():
        if detect_fault(*vector, signal, stuck_value):
            return vector

    return None


def generate_fault_report():
    """Generate a report for every modeled fault."""
    report = []

    for signal, stuck_value in generate_all_faults():
        vector = find_test_for_fault((signal, stuck_value))

        report.append({
            "fault": f"{signal} stuck-at-{stuck_value}",
            "status": "DETECTED" if vector is not None else "UNDETECTED",
            "test_vector": (
                "".join(map(str, vector))
                if vector is not None
                else "N/A"
            ),
        })

    return report


def get_detected_faults(vector):
    """Return all faults detected by a particular input vector."""
    detected = set()

    for signal, stuck_value in generate_all_faults():
        if detect_fault(*vector, signal, stuck_value):
            detected.add((signal, stuck_value))

    return detected


def compact_test_set():
    """
    Greedily select vectors that detect the largest number
    of currently undetected faults.
    """
    all_faults = set(generate_all_faults())
    uncovered = set(all_faults)
    selected_vectors = []

    vector_coverage = {
        vector: get_detected_faults(vector)
        for vector in generate_all_vectors()
    }

    while uncovered:
        best_vector = max(
            vector_coverage,
            key=lambda vector: len(vector_coverage[vector] & uncovered),
        )

        newly_detected = vector_coverage[best_vector] & uncovered

        if not newly_detected:
            break

        selected_vectors.append({
            "vector": "".join(map(str, best_vector)),
            "new_faults_detected": len(newly_detected),
            "faults": ", ".join(
                f"{signal} stuck-at-{value}"
                for signal, value in sorted(newly_detected)
            ),
        })

        uncovered -= newly_detected
        del vector_coverage[best_vector]

    return selected_vectors, uncovered


def save_fault_report(report):
    """Save the individual fault report to CSV."""
    output_dir = Path(__file__).resolve().parent.parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "sample_fault_report.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["fault", "status", "test_vector"],
        )
        writer.writeheader()
        writer.writerows(report)

    print(f"Fault report saved to: {output_file}")


def save_compact_test_set(test_set):
    """Save the compact test set to CSV."""
    output_dir = Path(__file__).resolve().parent.parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "compact_test_set.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        fieldnames = ["vector", "new_faults_detected", "faults"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_set)

    print(f"Compact test set saved to: {output_file}")


def main():
    report = generate_fault_report()
    save_fault_report(report)

    print("\nMini-ATPG: Fault Detection Report")
    print("=" * 58)
    print(f"{'Fault':<22} {'Status':<12} {'Test Vector (ABC)'}")
    print("-" * 58)

    for row in report:
        print(
            f"{row['fault']:<22} "
            f"{row['status']:<12} "
            f"{row['test_vector']}"
        )

    detected_count = sum(
        row["status"] == "DETECTED"
        for row in report
    )
    total_faults = len(report)
    coverage = (
        detected_count / total_faults * 100
        if total_faults
        else 0.0
    )

    print("-" * 58)
    print(f"Detected faults: {detected_count}/{total_faults}")
    print(f"Fault coverage: {coverage:.2f}%")

    compact_set, uncovered = compact_test_set()
    save_compact_test_set(compact_set)

    print("\nGreedy Test-Set Compaction")
    print("=" * 58)

    for index, item in enumerate(compact_set, start=1):
        print(
            f"{index}. Vector {item['vector']} "
            f"| Newly detected faults: {item['new_faults_detected']}"
        )
        print(f"   {item['faults']}")

    print("-" * 58)
    print(f"Selected test vectors: {len(compact_set)}")
    print(f"Uncovered faults: {len(uncovered)}")


if __name__ == "__main__":
    main()
