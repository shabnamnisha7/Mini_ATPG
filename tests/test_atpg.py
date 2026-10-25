
import sys
import unittest
from pathlib import Path

# Make the src directory importable during testing.
PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from circuit import evaluate_circuit
from fault_simulator import detect_fault, evaluate_with_fault
from test_generator import (
    generate_all_faults,
    generate_fault_report,
    find_test_for_fault,
)


class TestCircuit(unittest.TestCase):

    def test_truth_table_has_eight_rows(self):
        from circuit import generate_truth_table

        self.assertEqual(len(generate_truth_table()), 8)

    def test_known_circuit_outputs(self):
        # Y = (A AND B) OR C
        self.assertEqual(evaluate_circuit(0, 0, 0)["Y"], 0)
        self.assertEqual(evaluate_circuit(0, 0, 1)["Y"], 1)
        self.assertEqual(evaluate_circuit(1, 1, 0)["Y"], 1)
        self.assertEqual(evaluate_circuit(1, 0, 0)["Y"], 0)


class TestFaultSimulator(unittest.TestCase):

    def test_intermediate_stuck_at_zero(self):
        # For ABC=110, healthy Y=1; faulty n1=0 makes Y=0.
        self.assertTrue(detect_fault(1, 1, 0, "n1", 0))

    def test_output_stuck_at_zero(self):
        self.assertTrue(detect_fault(0, 0, 1, "Y", 0))

    def test_output_stuck_at_one(self):
        self.assertTrue(detect_fault(0, 0, 0, "Y", 1))

    def test_invalid_stuck_value(self):
        with self.assertRaises(ValueError):
            evaluate_with_fault(0, 0, 0, "n1", 2)


class TestPatternGenerator(unittest.TestCase):

    def test_ten_faults_are_modeled(self):
        self.assertEqual(len(generate_all_faults()), 10)

    def test_every_reported_vector_detects_its_fault(self):
        for row in generate_fault_report():
            signal, stuck_value = row["fault"].split(" stuck-at-")
            stuck_value = int(stuck_value)

            self.assertEqual(row["status"], "DETECTED")

            vector = tuple(int(bit) for bit in row["test_vector"])

            self.assertEqual(len(vector), 3)
            self.assertTrue(
                detect_fault(*vector, signal, stuck_value),
                msg=f"Invalid detecting vector for {row['fault']}",
            )

    def test_all_faults_have_a_test_vector(self):
        for fault in generate_all_faults():
            self.assertIsNotNone(find_test_for_fault(fault))


if __name__ == "__main__":
    unittest.main(verbosity=2)
