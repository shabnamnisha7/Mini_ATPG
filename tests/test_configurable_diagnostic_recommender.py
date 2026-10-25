
import unittest

try:
    from src.configurable_circuit import ConfigurableCircuit
    from src.diagnostic_recommender import recommend_diagnostic_tests
except ImportError:
    from configurable_circuit import ConfigurableCircuit
    from diagnostic_recommender import recommend_diagnostic_tests


class TestConfigurableDiagnosticRecommender(unittest.TestCase):

    def setUp(self):
        self.circuit = ConfigurableCircuit(
            inputs=["P", "Q"],
            gates=[
                {"type": "NOT", "inputs": ["P"], "output": "not_P"},
                {"type": "AND", "inputs": ["not_P", "Q"], "output": "OUT"},
            ],
            output="OUT",
        )

    def test_recommends_vectors_for_custom_input_names(self):
        candidates = [
            {"signal": "P", "stuck_at": 0},
            {"signal": "P", "stuck_at": 1},
        ]

        recommendations = recommend_diagnostic_tests(
            candidates,
            circuit=self.circuit,
        )

        self.assertTrue(recommendations)
        self.assertTrue(
            all(
                set(item["inputs"]) == {"P", "Q"}
                for item in recommendations
            )
        )

    def test_recommendations_distinguish_candidate_predictions(self):
        candidates = [
            {"signal": "P", "stuck_at": 0},
            {"signal": "P", "stuck_at": 1},
        ]

        recommendations = recommend_diagnostic_tests(
            candidates,
            circuit=self.circuit,
        )

        self.assertTrue(
            any(
                item["distinguished_pair_count"] > 0
                for item in recommendations
            )
        )

        for item in recommendations:
            self.assertEqual(
                item["distinguished_pair_count"],
                len(item["distinguished_pairs"]),
            )

    def test_returns_empty_when_faults_are_indistinguishable(self):
        candidates = [
            {"signal": "not_P", "stuck_at": 0},
            {"signal": "OUT", "stuck_at": 0},
        ]

        recommendations = recommend_diagnostic_tests(
            candidates,
            circuit=self.circuit,
        )

        self.assertEqual(recommendations, [])

    def test_rejects_unknown_fault_signal(self):
        candidates = [
            {"signal": "UNKNOWN", "stuck_at": 0},
            {"signal": "OUT", "stuck_at": 0},
        ]

        with self.assertRaises(ValueError):
            recommend_diagnostic_tests(
                candidates,
                circuit=self.circuit,
            )

    def test_rejects_invalid_stuck_value(self):
        candidates = [
            {"signal": "P", "stuck_at": 2},
            {"signal": "OUT", "stuck_at": 0},
        ]

        with self.assertRaises(ValueError):
            recommend_diagnostic_tests(
                candidates,
                circuit=self.circuit,
            )


if __name__ == "__main__":
    unittest.main()
