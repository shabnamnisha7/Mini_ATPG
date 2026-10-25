
from itertools import product

try:
    from .circuit import evaluate_circuit
except ImportError:
    from circuit import evaluate_circuit


def find_inputs_for_output(desired_output):
    """
    Find every input combination that produces the desired output.

    Args:
        desired_output: Required binary output, either 0 or 1.

    Returns:
        A list of dictionaries containing valid inputs and circuit signals.
    """
    if desired_output not in (0, 1) or isinstance(desired_output, bool):
        raise ValueError("Desired output must be integer 0 or 1.")

    matching_inputs = []

    for a, b, c in product([0, 1], repeat=3):
        result = evaluate_circuit(a, b, c)

        if result["Y"] == desired_output:
            matching_inputs.append(result)

    return matching_inputs


def main():
    print("Mini-ATPG: Desired-Output Input Solver")
    print("Circuit: Y = (A AND B) OR C")
    print()

    try:
        desired_output = int(input("Enter desired output (0 or 1): "))
        solutions = find_inputs_for_output(desired_output)
    except ValueError as error:
        print(f"Invalid input: {error}")
        return

    if not solutions:
        print("No valid input combinations found.")
        return

    print(f"\nInput combinations producing Y = {desired_output}:")
    print("A B C | n1 Y")
    print("-" * 17)

    for row in solutions:
        print(
            f"{row['A']} {row['B']} {row['C']} | "
            f" {row['n1']} {row['Y']}"
        )

    print(f"\nTotal valid combinations: {len(solutions)}")


if __name__ == "__main__":
    main()
