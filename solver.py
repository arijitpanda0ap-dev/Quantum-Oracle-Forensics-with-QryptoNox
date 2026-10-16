

from collections import Counter
import random

from qiskit import QuantumCircuit
from qiskit.circuit import Gate


# --------------------------------------------------
# ORACLE AND CIRCUIT HELPERS
# --------------------------------------------------

def add_oracle(qc, n, m):
    """Add the placeholder replaced by the challenge evaluator."""
    oracle = Gate("oracle", n + m, [])
    qc.append(oracle, list(range(n + m)))


def decode_counts(counts):
    """Convert Qiskit measurement strings into integers."""
    values = []
    for bits, count in counts.items():
        value = int(bits.replace(" ", ""), 2)
        values.extend([value] * count)
    return values


def make_basis_circuit(n, m, x):
    """Query one classical input x."""
    qc = QuantumCircuit(n + m, m)

    for bit in range(n):
        if (x >> bit) & 1:
            qc.x(bit)

    add_oracle(qc, n, m)

    for bit in range(m):
        qc.measure(n + bit, bit)

    return qc


def make_bv_circuit(n, m):
    """Bernstein-Vazirani-style circuit for a linear oracle."""
    qc = QuantumCircuit(n + m, n)

    qc.h(range(n))
    qc.x(n)
    qc.h(n)

    add_oracle(qc, n, m)

    qc.h(range(n))

    for bit in range(n):
        qc.measure(bit, bit)

    return qc


def make_simon_circuit(n, m):
    """Generate Simon-style samples from the input register."""
    qc = QuantumCircuit(n + m, n)

    qc.h(range(n))
    add_oracle(qc, n, m)
    qc.h(range(n))

    for bit in range(n):
        qc.measure(bit, bit)

    return qc


def make_grover_circuit(n, m, iterations):
    """Grover search using phase kickback."""
    qc = QuantumCircuit(n + m, n)

    # Prepare the input superposition and |-> output state.
    qc.h(range(n))
    qc.x(n)
    qc.h(n)

    for _ in range(iterations):
        add_oracle(qc, n, m)

        # Grover diffuser.
        qc.h(range(n))
        qc.x(range(n))
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)
        qc.x(range(n))
        qc.h(range(n))

    for bit in range(n):
        qc.measure(bit, bit)

    return qc


# --------------------------------------------------
# MAIN SOLVER
# --------------------------------------------------

def solve(n, m, budget, families, run):
    """
    Return (family, secret).

    Secret formats:
      constant: integer c
      linear: [a, b]
      grover: marked input t
      simon: integer s
      simon2: sorted list of three nonzero elements of H
      balanced, randfun, perm: None
    """

    remaining = budget
    allowed = set(families)

    def execute(qc, shots):
        """Track oracle-gate cost and never exceed the budget."""
        nonlocal remaining

        oracle_count = sum(
            item.operation.name == "oracle"
            for item in qc.data
        )

        if oracle_count == 0 or remaining < oracle_count:
            return {}

        shots = min(shots, remaining // oracle_count)

        if shots <= 0:
            return {}

        counts = run(qc, shots)
        remaining -= oracle_count * shots

        return counts

    def query_classically(x, shots=1):
        qc = make_basis_circuit(n, m, x)
        return decode_counts(execute(qc, shots))

    # --------------------------------------------------
    # ONE-BIT OUTPUT ORACLES
    # constant, balanced, linear, grover, randfun
    # --------------------------------------------------

    if m == 1:
        basis_inputs = [0] + [1 << i for i in range(n)]
        observed = {}
        total_ones = 0

        # Two shots per selected input reduce readout noise.
        for x in basis_inputs:
            values = query_classically(x, 2)
            if not values:
                continue

            observed[x] = Counter(values).most_common(1)[0][0]
            total_ones += sum(values)

        # Recover the candidate mask with a BV-style experiment.
        bv_counts = decode_counts(
            execute(make_bv_circuit(n, m), 5)
        )

        candidate_a = None
        if bv_counts:
            bv_frequency = Counter(bv_counts)
            candidate_a, frequency = bv_frequency.most_common(1)[0]

            # Confirm the candidate against the classical samples.
            b = observed.get(0, 0)
            mismatches = 0

            for x, y in observed.items():
                predicted = (bin(x & candidate_a).count("1") % 2) ^ b
                if predicted != y:
                    mismatches += 1

            if (
                candidate_a != 0
                and frequency >= 3
                and mismatches <= 1
                and "linear" in allowed
            ):
                return ("linear", [candidate_a, b])

        # Detect the constant-one oracle.
        if (
            "constant" in allowed
            and len(observed) == len(basis_inputs)
            and all(value == 1 for value in observed.values())
        ):
            return ("constant", 1)

        # Very few observed ones: investigate constant-zero vs Grover.
        if total_ones <= 3:
            if "grover" in allowed and remaining >= 15 * 2:
                # Five iterations, six shots: 30 oracle calls.
                grover_counts = decode_counts(
                    execute(make_grover_circuit(n, m, 5), 6)
                )

                if grover_counts:
                    candidate_t = Counter(grover_counts).most_common(1)[0][0]

                    # Validate the proposed marked input.
                    validation = query_classically(candidate_t, 3)

                    if sum(value == 1 for value in validation) >= 2:
                        return ("grover", candidate_t)

            # If search did not confirm a marked input, constant zero
            # is the fallback for this low-one-count branch.
            if "constant" in allowed:
                return ("constant", 0)

            return ("randfun", None)

        # Otherwise collect additional classical samples.
        # These distinguish a balanced function from a random function.
        rng = random.Random(2026)
        remaining_inputs = [
            x for x in range(2 ** n)
            if x not in basis_inputs
        ]
        rng.shuffle(remaining_inputs)

        extra_ones = 0
        extra_total = 0

        for x in remaining_inputs:
            if remaining <= 0:
                break

            values = query_classically(x, 1)
            if values:
                extra_ones += sum(values)
                extra_total += len(values)

        # Include the initial direct samples, not the BV measurements.
        total_samples = 18 + extra_total
        observed_ones = total_ones + extra_ones
        proportion = observed_ones / max(1, total_samples)

        # The ideal probabilities are 0.5 for balanced and 0.3 for randfun.
        if proportion >= 0.40 and "balanced" in allowed:
            return ("balanced", None)

        if "randfun" in allowed:
            return ("randfun", None)

        return ("balanced", None)

    # --------------------------------------------------
    # EIGHT-BIT OUTPUT ORACLES
    # simon, simon2, perm
    # --------------------------------------------------

    if m == 8:
        # Collect Simon-style samples. Each shot costs one query.
        counts = decode_counts(
            execute(make_simon_circuit(n, m), min(60, remaining))
        )

        if not counts:
            return ("perm", None)

        # For Simon families, s·z is usually zero.
        # Measurement noise weakens the correlation.
        scores = {}

        for mask in range(1, 2 ** n):
            matches = sum(
                (bin(z & mask).count("1") % 2) == 0
                for z in counts
            )
            scores[mask] = matches / len(counts)

        # Search for a 2D subspace: three nonzero masks
        # s1, s2, s1 XOR s2 with strong correlations.
        high = {
            mask for mask, score in scores.items()
            if score >= 0.74
        }

        for a in sorted(high):
            for b in sorted(high):
                if a >= b:
                    continue

                c = a ^ b

                if c in high and c != 0:
                    if (
                        scores[a] + scores[b] + scores[c]
                    ) / 3 >= 0.78:
                        return ("simon2", sorted([a, b, c]))

        # A single strong mask suggests the Simon family.
        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        best_mask, best_score = ranked[0]
        second_score = ranked[1][1]

        if (
            best_score >= 0.75
            and best_score - second_score >= 0.08
            and "simon" in allowed
        ):
            return ("simon", best_mask)

        return ("perm", None)

    return (None, None)

if __name__ == "__main__":
    print("Solver file loaded successfully.")
    print("Solve function available:", callable(solve))
    