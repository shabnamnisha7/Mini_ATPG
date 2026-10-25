
"""
Mini-ATPG fault diagnosis engine.

Identifies modeled single stuck-at faults consistent with
supplied input vectors and observed circuit outputs.

Supports:
- The original fixed A, B, C example circuit.
- ConfigurableCircuit instances with AND, OR, and NOT gates.

Candidates are modeled hypotheses, not proof of physical defects.
"""

try:
    from .circuit import evaluate_circuit
    from .fault_simulator import evaluate_with_fault as evaluate_fixed_fault
    from .configurable_circuit import (
        example_circuit,
        load_circuit_from_json,
    )
    from .configurable_fault_simulator import (
        evaluate_with_fault as evaluate_configurable_fault,
    )
except ImportError:
    from circuit import evaluate_circuit
    from fault_simulator import evaluate_with_fault as evaluate_fixed_fault
    from configurable_circuit import (
        example_circuit,
        load_circuit_from_json,
    )
    from configurable_fault_simulator import (
        evaluate_with_fault as evaluate_configurable_fault,
    )


STUCK_VALUES = (0, 1)
FIXED_INPUTS = ("A", "B", "C")
FIXED_FAULT_SIGNALS = ("A", "B", "C", "n1", "Y")


def _validate_binary(value, label):
    if type(value) is not int or value not in (0, 1):
        raise ValueError(f"{label} must be integer 0 or 1.")


def _validate_observations(observations, input_names):
    if not isinstance(observations, list) or not observations:
        raise ValueError("Provide at least one observation.")

    validated = []

    for index, observation in enumerate(observations):
        number = index + 1

        if not isinstance(observation, dict):
            raise ValueError(
                f"Observation {number} must be a dictionary."
            )

        required = set(input_names) | {"observed_Y"}

        missing = required - set(observation)
        if missing:
            name = sorted(missing)[0]
            raise ValueError(
                f"Observation {number} is missing {name}."
            )

        unexpected = set(observation) - required
        if unexpected:
            name = sorted(unexpected)[0]
            raise ValueError(
                f"Unexpected field '{name}' in observation {number}."
            )

        row = {}

        for name in input_names:
            _validate_binary(
                observation[name],
                f"{name} in observation {number}",
            )
            row[name] = observation[name]

        _validate_binary(
            observation["observed_Y"],
            f"observed_Y in observation {number}",
        )
        row["observed_Y"] = observation["observed_Y"]

        validated.append(row)

    return validated


def _diagnosis_message(candidates, healthy_matches):
    if not candidates and not healthy_matches:
        return "No modeled single stuck-at fault matches all observations."

    if healthy_matches:
        return "Healthy circuit is consistent with observations."

    return (
        "One or more modeled fault candidates match all observations."
    )



def _diagnose_fixed(observations):
    validated = _validate_observations(
        observations,
        FIXED_INPUTS,
    )

    healthy_matches = all(
        evaluate_circuit(
            row["A"],
            row["B"],
            row["C"],
        )["Y"] == row["observed_Y"]
        for row in validated
    )

    # If every observation matches the healthy circuit,
    # preserve the established API behavior: report no candidates.
    if healthy_matches:
        return {
            "healthy_circuit_matches": True,
            "observations_count": len(validated),
            "candidate_faults": [],
            "diagnosis": _diagnosis_message([], True),
        }

    candidates = []

    for signal in FIXED_FAULT_SIGNALS:
        for stuck_value in STUCK_VALUES:
            matches_all = all(
                evaluate_fixed_fault(
                    row["A"],
                    row["B"],
                    row["C"],
                    signal,
                    stuck_value,
                ) == row["observed_Y"]
                for row in validated
            )

            if matches_all:
                candidates.append({
                    "signal": signal,
                    "stuck_at": stuck_value,
                })

    return {
        "healthy_circuit_matches": False,
        "observations_count": len(validated),
        "candidate_faults": candidates,
        "diagnosis": _diagnosis_message(candidates, False),
    }

def _diagnose_configurable(observations, circuit):
    if not hasattr(circuit, "inputs") or not hasattr(circuit, "gates"):
        raise ValueError(
            "circuit must be a ConfigurableCircuit instance."
        )

    validated = _validate_observations(
        observations,
        circuit.inputs,
    )

    fault_signals = list(circuit.inputs)
    fault_signals.extend(
        gate["output"] for gate in circuit.gates
    )

    healthy_matches = all(
        circuit.evaluate({
            name: row[name] for name in circuit.inputs
        }) == row["observed_Y"]
        for row in validated
    )

    # Match the established behavior of the fixed-circuit mode.
    if healthy_matches:
        return {
            "healthy_circuit_matches": True,
            "observations_count": len(validated),
            "candidate_faults": [],
            "diagnosis": _diagnosis_message([], True),
        }

    candidates = []

    for signal in fault_signals:
        for stuck_value in STUCK_VALUES:
            matches_all = all(
                evaluate_configurable_fault(
                    circuit,
                    {
                        name: row[name] for name in circuit.inputs
                    },
                    signal,
                    stuck_value,
                ) == row["observed_Y"]
                for row in validated
            )

            if matches_all:
                candidates.append({
                    "signal": signal,
                    "stuck_at": stuck_value,
                })

    return {
        "healthy_circuit_matches": False,
        "observations_count": len(validated),
        "candidate_faults": candidates,
        "diagnosis": _diagnosis_message(candidates, False),
    }



def diagnose_faults(observations, circuit=None):
    """
    Diagnose modeled single stuck-at faults consistent with observations.

    Without `circuit`, uses the original A, B, C example.

    With `circuit`, uses a ConfigurableCircuit instance.

    Each observation contains the circuit's input names and `observed_Y`.

    Example for the original circuit:
        diagnose_faults([
            {"A": 1, "B": 1, "C": 0, "observed_Y": 0}
        ])

    Example for a configurable circuit:
        circuit = load_circuit_from_json("circuits/example_circuit.json")
        diagnose_faults([
            {"A": 1, "B": 1, "C": 0, "observed_Y": 0}
        ], circuit=circuit)
    """
    if circuit is None:
        return _diagnose_fixed(observations)

    return _diagnose_configurable(observations, circuit)


def main():
    print("Mini-ATPG: Configurable Fault Diagnosis")
    print("Enter the circuit's input values and observed output.")
    print("Enter q at the first input prompt to finish.")
    print()

    circuit_path = (
        __import__("pathlib").Path(__file__).resolve().parent.parent
        / "circuits"
        / "example_circuit.json"
    )
    circuit = load_circuit_from_json(circuit_path)

    print("Loaded circuit:", circuit_path.name)
    print("Inputs:", ", ".join(circuit.inputs))
    print("Output:", circuit.output)
    print()

    observations = []

    while True:
        row = {}
        first_name = circuit.inputs[0]
        first_value = input(
            f"{first_name} (0, 1, or q): "
        ).strip().lower()

        if first_value == "q":
            break

        try:
            if first_value not in ("0", "1"):
                raise ValueError(
                    f"{first_name} must be 0 or 1."
                )

            row[first_name] = int(first_value)

            for name in circuit.inputs[1:]:
                value = input(f"{name} (0 or 1): ").strip()
                if value not in ("0", "1"):
                    raise ValueError(f"{name} must be 0 or 1.")
                row[name] = int(value)

            observed = input("Observed output (0 or 1): ").strip()
            if observed not in ("0", "1"):
                raise ValueError("Observed output must be 0 or 1.")

            row["observed_Y"] = int(observed)

            # Validate before storing the observation.
            _validate_observations([row], circuit.inputs)
            observations.append(row)

        except ValueError as error:
            print(f"Invalid entry: {error}")
            print()
            continue

        print()

    if not observations:
        print("No observations entered.")
        return

    result = diagnose_faults(observations, circuit=circuit)

    print("\nDiagnosis report")
    print("-" * 40)
    print(f"Observations: {result['observations_count']}")
    print(
        "Healthy circuit matches:",
        result["healthy_circuit_matches"],
    )
    print(result["diagnosis"])

    if result["candidate_faults"]:
        print("\nCandidate fault locations:")
        for fault in result["candidate_faults"]:
            print(
                f"  Signal {fault['signal']} "
                f"stuck-at-{fault['stuck_at']}"
            )
    else:
        print("\nNo candidate from the modeled fault set was found.")

    print(
        "\nNote: these are hypotheses under the single stuck-at fault "
        "model, not proof of a physical defect."
    )


if __name__ == "__main__":
    main()
