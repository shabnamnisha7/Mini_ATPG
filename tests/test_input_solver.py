
import unittest

from src.input_solver import find_inputs_for_output


class TestInputSolver(unittest.TestCase):

    def test_finds_all_inputs_for_output_one(self):
        solutions = find_inputs_for_output(1)

        self.assertEqual(len(solutions), 5)
        self.assertTrue(all(row["Y"] == 1 for row in solutions))

    def test_finds_all_inputs_for_output_zero(self):
        solutions = find_inputs_for_output(0)

        self.assertEqual(len(solutions), 3)
        self.assertTrue(all(row["Y"] == 0 for row in solutions))

    def test_all_input_combinations_are_unique(self):
        for desired_output in (0, 1):
            solutions = find_inputs_for_output(desired_output)
            inputs = [
                (row["A"], row["B"], row["C"])
                for row in solutions
            ]

            self.assertEqual(len(inputs), len(set(inputs)))

    def test_invalid_output_is_rejected(self):
        for invalid_output in (-1, 2, "1", True):
            with self.subTest(value=invalid_output):
                with self.assertRaises(ValueError):
                    find_inputs_for_output(invalid_output)


if __name__ == "__main__":
    unittest.main()
