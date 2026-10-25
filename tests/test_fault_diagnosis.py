
import unittest

from src.fault_diagnosis import diagnose_faults


class TestFaultDiagnosis(unittest.TestCase):

    def test_identifies_c_stuck_at_zero(self):
        observations = [
            {"A": 0, "B": 0, "C": 1, "observed_Y": 0},
        ]

        result = diagnose_faults(observations)

        self.assertFalse(result["healthy_circuit_matches"])
        self.assertIn(
            {"signal": "C", "stuck_at": 0},
            result["candidate_faults"],
        )

    def test_healthy_observations_match_healthy_circuit(self):
        observations = [
            {"A": 0, "B": 0, "C": 0, "observed_Y": 0},
            {"A": 1, "B": 1, "C": 0, "observed_Y": 1},
            {"A": 0, "B": 0, "C": 1, "observed_Y": 1},
        ]

        result = diagnose_faults(observations)

        self.assertTrue(result["healthy_circuit_matches"])
        self.assertEqual(result["candidate_faults"], [])

    def test_multiple_observations_narrow_candidates(self):
        observations = [
            {"A": 0, "B": 0, "C": 1, "observed_Y": 0},
            {"A": 1, "B": 1, "C": 0, "observed_Y": 1},
        ]

        result = diagnose_faults(observations)

        self.assertFalse(result["healthy_circuit_matches"])
        self.assertEqual(
            result["candidate_faults"],
            [{"signal": "C", "stuck_at": 0}],
        )

    def test_rejects_empty_observations(self):
        with self.assertRaises(ValueError):
            diagnose_faults([])

    def test_rejects_missing_output(self):
        with self.assertRaises(ValueError):
            diagnose_faults([{"A": 0, "B": 0, "C": 0}])

    def test_rejects_non_binary_values(self):
        with self.assertRaises(ValueError):
            diagnose_faults([
                {"A": 2, "B": 0, "C": 0, "observed_Y": 0}
            ])


if __name__ == "__main__":
    unittest.main()
