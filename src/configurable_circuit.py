
import json
from pathlib import Path


class ConfigurableCircuit:
    """Evaluate a combinational circuit described by logic gates."""

    def __init__(self, inputs, gates, output):
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("Circuit inputs must be a non-empty list")

        if len(inputs) != len(set(inputs)):
            raise ValueError("Circuit input names must be unique")

        if not all(isinstance(name, str) and name for name in inputs):
            raise ValueError("Every input must have a non-empty string name")

        if not isinstance(gates, list):
            raise ValueError("Circuit gates must be a list")

        self.inputs = inputs
        self.gates = gates
        self.output = output

        available_signals = set(inputs)

        for gate in gates:
            if not isinstance(gate, dict):
                raise ValueError("Every gate must be a JSON object")

            if not all(key in gate for key in ("type", "inputs", "output")):
                raise ValueError(
                    "Every gate must contain type, inputs, and output"
                )

            if not isinstance(gate["type"], str):
                raise ValueError("Gate type must be a string")

            gate_type = gate["type"].upper()
            gate_output = gate["output"]
            gate_inputs = gate["inputs"]

            if gate_type not in ("AND", "OR", "NOT"):
                raise ValueError(f"Unsupported gate type: {gate_type}")

            if not isinstance(gate_output, str) or not gate_output:
                raise ValueError("Gate output must be a non-empty string")

            if not isinstance(gate_inputs, list):
                raise ValueError("Gate inputs must be a list")

            expected_inputs = 1 if gate_type == "NOT" else 2

            if len(gate_inputs) != expected_inputs:
                raise ValueError(
                    f"{gate_type} gate requires {expected_inputs} input(s)"
                )

            for signal in gate_inputs:
                if signal not in available_signals:
                    raise ValueError(
                        f"Signal '{signal}' is undefined or used before definition"
                    )

            if gate_output in available_signals:
                raise ValueError(
                    f"Signal '{gate_output}' is defined more than once"
                )

            available_signals.add(gate_output)

        if not isinstance(output, str) or output not in available_signals:
            raise ValueError(f"Output signal '{output}' is undefined")

    def evaluate(self, input_values):
        """Evaluate the circuit for a dictionary of binary input values."""
        if not isinstance(input_values, dict):
            raise ValueError("Input values must be a dictionary")

        if set(input_values) != set(self.inputs):
            raise ValueError("Input values must match the circuit inputs exactly")

        if any(
            type(value) is not int or value not in (0, 1)
            for value in input_values.values()
        ):
            raise ValueError("All input values must be integer 0 or 1")

        signals = dict(input_values)

        for gate in self.gates:
            gate_type = gate["type"].upper()
            gate_inputs = [signals[name] for name in gate["inputs"]]
            gate_output = gate["output"]

            if gate_type == "AND":
                result = gate_inputs[0] & gate_inputs[1]
            elif gate_type == "OR":
                result = gate_inputs[0] | gate_inputs[1]
            else:
                result = 1 - gate_inputs[0]

            signals[gate_output] = result

        return signals[self.output]


def load_circuit_from_json(file_path):
    """Load and validate a circuit definition from a JSON file."""
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Circuit JSON file not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in circuit file '{path}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Circuit JSON must contain an object")

    required_keys = {"inputs", "gates", "output"}

    if set(data) != required_keys:
        raise ValueError(
            "Circuit JSON must contain exactly these keys: "
            "inputs, gates, output"
        )

    return ConfigurableCircuit(
        inputs=data["inputs"],
        gates=data["gates"],
        output=data["output"],
    )


def example_circuit():
    """Return the original circuit using the configurable model."""
    return ConfigurableCircuit(
        inputs=["A", "B", "C"],
        gates=[
            {"type": "AND", "inputs": ["A", "B"], "output": "n1"},
            {"type": "OR", "inputs": ["n1", "C"], "output": "Y"},
        ],
        output="Y",
    )


if __name__ == "__main__":
    circuit_path = (
        Path(__file__).resolve().parent.parent
        / "circuits"
        / "example_circuit.json"
    )

    circuit = load_circuit_from_json(circuit_path)

    print("Configurable Circuit Simulator")
    print("Circuit loaded from:", circuit_path.name)
    print("Circuit: Y = (A AND B) OR C")
    print("-" * 35)
    print("A B C | Y")

    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                y = circuit.evaluate({"A": a, "B": b, "C": c})
                print(f"{a} {b} {c} | {y}")
