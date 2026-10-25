
from circuit import evaluate_circuit


def evaluate_with_fault(a, b, c, fault_signal, stuck_value):
    """
    Evaluate the circuit with a stuck-at-0 or stuck-at-1 fault.

    Supported fault sites: A, B, C, n1, Y
    """
    if stuck_value not in (0, 1):
        raise ValueError("stuck_value must be 0 or 1")

    if fault_signal not in ("A", "B", "C", "n1", "Y"):
        raise ValueError("Unknown fault signal")

    # Apply faults on primary inputs before evaluating the circuit.
    if fault_signal == "A":
        a = stuck_value
    elif fault_signal == "B":
        b = stuck_value
    elif fault_signal == "C":
        c = stuck_value

    # Calculate the intermediate signal.
    n1 = a & b

    # Apply a fault on the intermediate signal.
    if fault_signal == "n1":
        n1 = stuck_value

    # Calculate the output.
    y = n1 | c

    # Apply a fault on the output itself.
    if fault_signal == "Y":
        y = stuck_value

    return y


def detect_fault(a, b, c, fault_signal, stuck_value):
    """Return True when the faulty and healthy outputs differ."""
    good_output = evaluate_circuit(a, b, c)["Y"]
    faulty_output = evaluate_with_fault(
        a, b, c, fault_signal, stuck_value
    )

    return good_output != faulty_output


if __name__ == "__main__":
    test_vector = (1, 1, 0)
    fault_signal = "n1"
    stuck_value = 0

    detected = detect_fault(
        *test_vector, fault_signal, stuck_value
    )

    print("Mini-ATPG: Fault Simulator")
    print(f"Test vector: A={test_vector[0]}, "
          f"B={test_vector[1]}, C={test_vector[2]}")
    print(f"Injected fault: {fault_signal} stuck-at-{stuck_value}")
    print(f"Fault detected: {detected}")
