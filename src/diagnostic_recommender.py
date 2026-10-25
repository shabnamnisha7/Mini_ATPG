
"""
Recommend input vectors that distinguish candidate stuck-at faults.

Supports both the original fixed circuit and ConfigurableCircuit objects.
Recommendations are ranked by the number of candidate-fault pairs
that predict different outputs.
"""

from itertools import product

try:
    from .circuit import evaluate_circuit
    from .fault_simulator import evaluate_with_fault as evaluate_fixed_fault
    from .configurable_fault_simulator import (
        evaluate_with_fault as evaluate_configurable_fault,
    )
except ImportError:
    from circuit import evaluate_circuit
    from fault_simulator import evaluate_with_fault as evaluate_fixed_fault
    from configurable_fault_simulator import (
        evaluate_with_fault as evaluate_configurable_fault,
    )


FIXED_INPUTS = ("A", "B", "C")
FIXED_FAULT_SIGNALS = ("A", "B", "C", "n1", "Y")


def recommend_diagnostic_tests(candidate_faults, circuit=None):
    """
    Rank input vectors by how many candidate-fault pairs they distinguish.

    Without `circuit`, use the original A, B, C circuit.
    With `circuit`, use a ConfigurableCircuit instance.

    Each candidate fault has:
        {"signal": signal_name, "stuck_at": 0_or_1}

    Returns ranked recommendations. This is a greedy ranking, not
    a guarantee of the globally smallest diagnostic test sequence.
    """
    if not isinstance(candidate_faults, list) or len(candidate_faults) < 2:
        raise ValueError("Provide at least two candidate faults.")

    if circuit is None:
        input_names = FIXED_INPUTS
        valid_signals = FIXED_FAULT_SIGNALS
    else:
        if not hasattr(circuit, "inputs") or not hasattr(circuit, "gates"):
            raise ValueError(
                "circuit must be a ConfigurableCircuit instance."
            )

        input_names = tuple(circuit.inputs)
        valid_signals = set(input_names)
        valid_signals.update(
            gate["output"] for gate in circuit.gates
        )

    validated_faults = []

    for fault in candidate_faults:
        if not isinstance(fault, dict):
            raise ValueError("Each candidate fault must be a dictionary.")

        signal = fault.get("signal")
        stuck_at = fault.get("stuck_at")

        if signal not in valid_signals:
            raise ValueError(f"Unknown fault signal: {signal}")

        if type(stuck_at) is not int or stuck_at not in (0, 1):
            raise ValueError("stuck_at must be integer 0 or 1.")

        validated_faults.append({
            "signal": signal,
            "stuck_at": stuck_at,
        })

    recommendations = []

    for values in product((0, 1), repeat=len(input_names)):
        inputs = dict(zip(input_names, values))
        predictions = []

        for fault in validated_faults:
            if circuit is None:
                predicted = evaluate_fixed_fault(
                    inputs["A"],
                    inputs["B"],
                    inputs["C"],
                    fault["signal"],
                    fault["stuck_at"],
                )
            else:
                predicted = evaluate_configurable_fault(
                    circuit,
                    inputs,
                    fault["signal"],
                    fault["stuck_at"],
                )

            predictions.append(predicted)

        distinguished_pairs = []

        for i in range(len(validated_faults)):
            for j in range(i + 1, len(validated_faults)):
                if predictions[i] != predictions[j]:
                    distinguished_pairs.append((i, j))

        if distinguished_pairs:
            if circuit is None:
                healthy_output = evaluate_circuit(
                    inputs["A"],
                    inputs["B"],
                    inputs["C"],
                )["Y"]
            else:
                healthy_output = circuit.evaluate(inputs)

            recommendations.append({
                "inputs": inputs,
                "healthy_expected_output": healthy_output,
                "fault_predictions": [
                    {
                        "fault": validated_faults[index],
                        "predicted_output": predictions[index],
                    }
                    for index in range(len(validated_faults))
                ],
                "distinguished_pairs": distinguished_pairs,
                "distinguished_pair_count": len(distinguished_pairs),
            })

    recommendations.sort(
        key=lambda item: item["distinguished_pair_count"],
        reverse=True,
    )

    return recommendations


def main():
    candidates = [
        {"signal": "C", "stuck_at": 0},
        {"signal": "Y", "stuck_at": 0},
    ]

    recommendations = recommend_diagnostic_tests(candidates)

    print("Mini-ATPG: Diagnostic Test Recommender")
    print("Candidate faults:")

    for fault in candidates:
        print(f"  {fault['signal']} stuck-at-{fault['stuck_at']}")

    print("\nRecommended test vectors:")

    if not recommendations:
        print("No vector distinguishes the supplied candidates.")
        return

    for item in recommendations:
        inputs = item["inputs"]
        input_text = " ".join(
            f"{name}={value}" for name, value in inputs.items()
        )

        print(
            f"{input_text} | "
            f"healthy output={item['healthy_expected_output']} | "
            f"distinguished pairs="
            f"{item['distinguished_pair_count']}"
        )

        for prediction in item["fault_predictions"]:
            fault = prediction["fault"]
            print(
                f"    {fault['signal']} stuck-at-{fault['stuck_at']}"
                f" predicts output={prediction['predicted_output']}"
            )


if __name__ == "__main__":
    main()
