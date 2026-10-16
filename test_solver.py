
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from solver import solve

# Test that the solver can create and pass a circuit to run()
def fake_run(circuit, shots):
    print("Circuit received:", isinstance(circuit, QuantumCircuit))
    print("Shots requested:", shots)
    print("Circuit qubits:", circuit.num_qubits)
    return {"000000000": shots}

try:
    result = solve(8, 1, 60, ["constant", "linear"], fake_run)
    print("Solver returned:", result)
    print("Result is a 2-item tuple:", isinstance(result, tuple) and len(result) == 2)
except Exception as error:
    print("TEST FAILED:", type(error).__name__, error)
