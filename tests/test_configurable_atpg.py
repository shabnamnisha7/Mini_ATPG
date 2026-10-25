
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configurable_circuit import (
    ConfigurableCircuit,
    example_circuit,
    load_circuit_from_json,
)
from configurable_fault_simulator import (
    detect_fault,
    evaluate_with_fault,
)
from configurable_test_generator import (
    generate_input_vectors,
    generate_fault_list,
    find_test_vector,
    generate_report,
    get_detected_faults,
    compact_test_set,
    calculate_coverage,
    save_report_csv,
    save_compact_test_set_csv,
)


class TestConfigurableCircuit(unittest.TestCase):

    def setUp(self):
        self.circuit = example_circuit()

    def test_circuit_has_eight_input_vectors(self):
        self.assertEqual(len(generate_input_vectors(self.circuit.inputs)), 8)

    def test_known_outputs(self):
        self.assertEqual(self.circuit.evaluate({"A": 0, "B": 0, "C": 0}), 0)
        self.assertEqual(self.circuit.evaluate({"A": 0, "B": 0, "C": 1}), 1)
        self.assertEqual(self.circuit.evaluate({"A": 1, "B": 1, "C": 0}), 1)

    def test_not_gate(self):
        circuit = ConfigurableCircuit(
            inputs=["A"],
            gates=[{"type": "NOT", "inputs": ["A"], "output": "Y"}],
            output="Y",
        )
        self.assertEqual(circuit.evaluate({"A": 0}), 1)
        self.assertEqual(circuit.evaluate({"A": 1}), 0)

    def test_rejects_undefined_output(self):
        with self.assertRaises(ValueError):
            ConfigurableCircuit(inputs=["A"], gates=[], output="Y")

    def test_rejects_duplicate_input_names(self):
        with self.assertRaises(ValueError):
            ConfigurableCircuit(inputs=["A", "A"], gates=[], output="A")

    def test_rejects_boolean_input_values(self):
        with self.assertRaises(ValueError):
            self.circuit.evaluate({"A": True, "B": 0, "C": 0})


class TestConfigurableFaultSimulation(unittest.TestCase):

    def setUp(self):
        self.circuit = example_circuit()

    def test_intermediate_fault_changes_output(self):
        self.assertTrue(
            detect_fault(self.circuit, {"A": 1, "B": 1, "C": 0}, "n1", 0)
        )

    def test_output_fault_changes_output(self):
        self.assertTrue(
            detect_fault(self.circuit, {"A": 0, "B": 0, "C": 0}, "Y", 1)
        )

    def test_invalid_fault_value_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(
                self.circuit, {"A": 0, "B": 0, "C": 0}, "n1", 2
            )

    def test_rejects_boolean_stuck_value(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(
                self.circuit, {"A": 0, "B": 0, "C": 0}, "n1", True
            )

    def test_rejects_unknown_fault_signal(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(
                self.circuit, {"A": 0, "B": 0, "C": 0}, "UNKNOWN", 0
            )

    def test_rejects_missing_input(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(
                self.circuit, {"A": 0, "B": 0}, "n1", 0
            )

    def test_rejects_non_binary_input(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(
                self.circuit, {"A": 0, "B": 2, "C": 0}, "n1", 0
            )


class TestConfigurableTestGenerator(unittest.TestCase):

    def setUp(self):
        self.circuit = example_circuit()

    def test_ten_faults_are_generated(self):
        self.assertEqual(len(generate_fault_list(self.circuit)), 10)

    def test_all_faults_have_detecting_vectors(self):
        for fault in generate_fault_list(self.circuit):
            self.assertIsNotNone(find_test_vector(self.circuit, fault))

    def test_report_contains_all_faults(self):
        report = generate_report(self.circuit)
        self.assertEqual(len(report), 10)
        self.assertTrue(all(row["status"] == "DETECTED" for row in report))

    def test_coverage_calculation(self):
        report = generate_report(self.circuit)
        self.assertEqual(calculate_coverage(report), (10, 10, 100.0))


class TestJSONCircuitLoading(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.json_path = Path(self.temp_dir.name) / "circuit.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_json(self, data):
        self.json_path.write_text(json.dumps(data), encoding="utf-8")

    def test_loads_valid_json_circuit(self):
        self.write_json({
            "inputs": ["A", "B", "C"],
            "gates": [
                {"type": "AND", "inputs": ["A", "B"], "output": "n1"},
                {"type": "OR", "inputs": ["n1", "C"], "output": "Y"},
            ],
            "output": "Y",
        })
        circuit = load_circuit_from_json(self.json_path)
        self.assertEqual(circuit.evaluate({"A": 1, "B": 1, "C": 0}), 1)
        self.assertEqual(circuit.evaluate({"A": 0, "B": 0, "C": 0}), 0)

    def test_rejects_invalid_json(self):
        self.json_path.write_text('{"inputs": ["A"],', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_circuit_from_json(self.json_path)

    def test_rejects_missing_json_file(self):
        with self.assertRaises(FileNotFoundError):
            load_circuit_from_json(Path(self.temp_dir.name) / "missing.json")

    def test_rejects_missing_required_key(self):
        self.write_json({"inputs": ["A"], "gates": []})
        with self.assertRaises(ValueError):
            load_circuit_from_json(self.json_path)

    def test_rejects_unsupported_gate_from_json(self):
        self.write_json({
            "inputs": ["A"],
            "gates": [{"type": "XOR", "inputs": ["A", "A"], "output": "Y"}],
            "output": "Y",
        })
        with self.assertRaises(ValueError):
            load_circuit_from_json(self.json_path)


class TestTestSetCompaction(unittest.TestCase):

    def setUp(self):
        self.circuit = example_circuit()

    def test_compaction_covers_every_detectable_fault(self):
        selected, detectable, uncovered, _ = compact_test_set(self.circuit)
        self.assertEqual(uncovered, set())

        covered = set()
        for row in selected:
            vector = dict(
                zip(self.circuit.inputs, map(int, row["test_vector"]))
            )
            covered.update(get_detected_faults(self.circuit, vector))

        self.assertTrue(detectable.issubset(covered))

    def test_compaction_uses_four_vectors_for_example(self):
        selected, _, uncovered, _ = compact_test_set(self.circuit)
        self.assertEqual(len(selected), 4)
        self.assertEqual(uncovered, set())

    def test_compact_vectors_are_unique(self):
        selected, _, _, _ = compact_test_set(self.circuit)
        vectors = [row["test_vector"] for row in selected]
        self.assertEqual(len(vectors), len(set(vectors)))

    def test_every_selected_vector_has_new_faults(self):
        selected, _, _, _ = compact_test_set(self.circuit)
        self.assertTrue(all(row["new_faults"] > 0 for row in selected))


class TestCSVExports(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.circuit = example_circuit()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fault_report_csv_export(self):
        report = generate_report(self.circuit)
        output_path = self.output_dir / "fault_report.csv"

        saved_path = save_report_csv(report, output_path)

        self.assertTrue(saved_path.exists())
        with saved_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 10)
        self.assertEqual(
            set(rows[0].keys()), {"fault", "status", "test_vector"}
        )

    def test_compact_test_set_csv_export(self):
        selected, _, _, _ = compact_test_set(self.circuit)
        output_path = self.output_dir / "compact.csv"

        saved_path = save_compact_test_set_csv(selected, output_path)

        self.assertTrue(saved_path.exists())
        with saved_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 4)
        self.assertEqual(
            set(rows[0].keys()), {"test_vector", "new_faults", "faults"}
        )

    def test_csv_export_creates_missing_parent_directory(self):
        output_path = self.output_dir / "new_folder" / "report.csv"
        save_report_csv(generate_report(self.circuit), output_path)
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
