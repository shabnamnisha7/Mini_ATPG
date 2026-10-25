
from configurable_circuit import example_circuit


def evaluate_with_fault(circuit, input_values, fault_signal, stuck_value):
    """
    Evaluate a combinational circuit with one stuck-at fault.

    The fault is applied to a primary input or gate output.
    Downstream gates use the faulty signal value.
    """

    # Validate the stuck-at value. Booleans are deliberately rejected.
    if type(stuck_value) is not int or stuck_value not in (0, 1):
        raise ValueError("stuck_value must be integer 0 or 1")

    # Validate the fault signal.
    if not isinstance(fault_signal, str) or not fault_signal:
        raise ValueError("fault_signal must be a non-empty string")

    gate_outputs = {gate["output"] for gate in circuit.gates}
    valid_signals = set(circuit.inputs) | gate_outputs

    if fault_signal not in valid_signals:
        raise ValueError(f"Unknown fault signal: {fault_signal}")

    # Validate inputs before simulating the faulty circuit.
    if not isinstance(input_values, dict):
        raise ValueError("Input values must be a dictionary")

    if set(input_values) != set(circuit.inputs):
        raise ValueError("Input values must match the circuit inputs exactly")

    if any(
        type(value) is not int or value not in (0, 1)
        for value in input_values.values()
    ):
        raise ValueError("All input values must be integer 0 or 1")

    signals = dict(input_values)

    # Apply a fault to a primary input before evaluating the gates.
    if fault_signal in circuit.inputs:
        signals[fault_signal] = stuck_value

    for gate in circuit.gates:
        gate_type = gate["type"].upper()
        gate_inputs = [signals[name] for name in gate["inputs"]]
        output = gate["output"]

        if gate_type == "AND":
            result = gate_inputs[0] & gate_inputs[1]
        elif gate_type == "OR":
            result = gate_inputs[0] | gate_inputs[1]
        elif gate_type == "NOT":
            result = 1 - gate_inputs[0]
        else:
            raise ValueError(f"Unsupported gate type: {gate_type}")

        # Force a gate output to the faulty value when applicable.
        if output == fault_signal:
            result = stuck_value

        signals[output] = result

    return signals[circuit.output]


def detect_fault(circuit, input_values, fault_signal, stuck_value):
    """Return True if a single stuck-at fault changes the circuit output."""

    good_output = circuit.evaluate(input_values)

    faulty_output = evaluate_with_fault(
        circuit,
        input_values,
        fault_signal,
        stuck_value,
    )

    return good_output != faulty_output


if __name__ == "__main__":
    circuit = example_circuit()
    vector = {"A": 1, "B": 1, "C": 0}

    signal = "n1"
    stuck_value = 0

    good_output = circuit.evaluate(vector)
    faulty_output = evaluate_with_fault(
        circuit, vector, signal, stuck_value
    )

    print("Configurable Fault Simulator")
    print(f"Input vector: {vector}")
    print(f"Fault: {signal} stuck-at-{stuck_value}")
    print(f"Healthy output: {good_output}")
    print(f"Faulty output: {faulty_output}")
    print(f"Fault detected: {good_output != faulty_output}")
