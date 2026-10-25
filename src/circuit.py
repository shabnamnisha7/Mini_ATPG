
from itertools import product


def evaluate_circuit(a, b, c):
    """
    Evaluate the combinational circuit:

        n1 = A AND B
        Y  = n1 OR C

    Inputs and outputs are binary: 0 or 1.
    """
    n1 = a & b
    y = n1 | c

    return {
        "A": a,
        "B": b,
        "C": c,
        "n1": n1,
        "Y": y,
    }


def generate_truth_table():
    """Generate all possible input combinations."""
    rows = []

    for a, b, c in product([0, 1], repeat=3):
        result = evaluate_circuit(a, b, c)
        rows.append(result)

    return rows


if __name__ == "__main__":
    print("Mini-ATPG: Circuit Simulator")
    print("Circuit: Y = (A AND B) OR C")
    print("-" * 35)
    print("A B C | n1 Y")
    print("-" * 35)

    for row in generate_truth_table():
        print(
            f"{row['A']} {row['B']} {row['C']} | "
            f" {row['n1']} {row['Y']}"
        )
