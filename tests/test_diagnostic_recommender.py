
import unittest

from src.diagnostic_recommender import recommend_diagnostic_tests


class TestDiagnosticRecommender(unittest.TestCase):

    def test_finds_vector_distinguishing_two_faults(self):
        candidates = [
            {"signal": "C", "stuck_at": 0},
            {"signal": "Y", "stuck_at": 0},
        ]

        recommendations = recommend_diagnostic_tests(candidates)

        self.assertTrue(recommendations)

        first = recommendations[0]
        self.assertEqual(first["inputs"], {"A": 1, "B": 1, "C": 0})

        predictions = {
            (
                item["fault"]["signal"],
                item["fault"]["stuck_at"],
            ): item["predicted_output"]
            for item in first["fault_predictions"]
        }

        self.assertEqual(predictions[("C", 0)], 1)
        self.assertEqual(predictions[("Y", 0)], 0)

    def test_rejects_too_few_candidates(self):
        with self.assertRaises(ValueError):
            recommend_diagnostic_tests([
                {"signal": "C", "stuck_at": 0}
            ])

    def test_rejects_unknown_signal(self):
        with self.assertRaises(ValueError):
            recommend_diagnostic_tests([
                {"signal": "UNKNOWN", "stuck_at": 0},
                {"signal": "Y", "stuck_at": 0},
            ])

    def test_rejects_invalid_stuck_value(self):
        with self.assertRaises(ValueError):
            recommend_diagnostic_tests([
                {"signal": "C", "stuck_at": 2},
                {"signal": "Y", "stuck_at": 0},
            ])


if __name__ == "__main__":
    unittest.main()
