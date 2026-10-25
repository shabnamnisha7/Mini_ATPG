
import unittest

try:
    from src.configurable_circuit import ConfigurableCircuit
    from src.fault_diagnosis import diagnose_faults
    from src.configurable_fault_simulator import evaluate_with_fault
except ImportError:
    from configurable_circuit import ConfigurableCircuit
    from fault_diagnosis import diagnose_faults
    from configurable_fault_simulator import evaluate_with_fault


class TestConfigurableFaultDiagnosis(unittest.TestCase):

    def setUp(self):
        self.circuit = ConfigurableCircuit(
            inputs=["P", "Q"],
            gates=[
                {"type": "NOT", "inputs": ["P"], "output": "not_P"},
                {"type": "AND", "inputs": ["not_P", "Q"], "output": "OUT"},
            ],
            output="OUT",
        )

    def test_healthy_observations_return_no_candidates(self):
        observations = [
            {"P": 0, "Q": 0, "observed_Y": 0},
            {"P": 0, "Q": 1, "observed_Y": 1},
            {"P": 1, "Q": 1, "observed_Y": 0},
        ]

        result = diagnose_faults(observations, circuit=self.circuit)

        self.assertTrue(result["healthy_circuit_matches"])
        self.assertEqual(result["candidate_faults"], [])
        self.assertEqual(result["observations_count"], 3)

    def test_detects_modeled_fault_with_custom_input_names(self):
        observations = [
            {"P": 0, "Q": 1, "observed_Y": 0},
            {"P": 1, "Q": 1, "observed_Y": 0},
        ]

        result = diagnose_faults(observations, circuit=self.circuit)

        self.assertFalse(result["healthy_circuit_matches"])
        self.assertIn(
            {"signal": "not_P", "stuck_at": 0},
            result["candidate_faults"],
        )

    def test_configurable_fault_simulator_handles_not_gate(self):
        inputs = {"P": 0, "Q": 1}

        healthy_output = self.circuit.evaluate(inputs)
        faulty_output = evaluate_with_fault(
            self.circuit,
            inputs,
            "not_P",
            0,
        )

        self.assertEqual(healthy_output, 1)
        self.assertEqual(faulty_output, 0)

    def test_rejects_missing_input(self):
        observations = [
            {"P": 0, "observed_Y": 0},
        ]

        with self.assertRaises(ValueError):
            diagnose_faults(observations, circuit=self.circuit)


if __name__ == "__main__":
    unittest.main()
