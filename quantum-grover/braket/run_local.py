"""
Run Grover's Algorithm on AWS Braket Local Simulator (FREE)

This script executes the Grover search algorithm for H, B, Y bitmap patterns
using AWS Braket's local simulator, which runs entirely on your machine at no cost.
"""

from braket.devices import LocalSimulator
from braket.circuits import Circuit
import time

# Define the bitmap patterns we're searching for
H_CONST = 0b101101111101101  # 23533
B_CONST = 0b110101110101110  # 27566
Y_CONST = 0b101010010010010  # 21650

NUM_PIXELS = 15

def create_grover_circuit():
    """
    Create a simplified Grover's algorithm circuit for demonstration.

    Note: This is a basic version. The full implementation would require
    the complete oracle for checking H/B/Y patterns, which needs ~100-1000 gates.
    """
    circuit = Circuit()

    # Step 1: Initialize all qubits in superposition
    print("Building circuit: Initializing superposition...")
    for i in range(NUM_PIXELS):
        circuit.h(i)

    # Step 2: Simplified Grover iteration
    # In a full implementation, you would have:
    # - Oracle: Mark states matching H_CONST, B_CONST, Y_CONST
    # - Diffuser: Reflect about uniform superposition
    # Repeated 20 times

    print(f"Circuit has {NUM_PIXELS} qubits in superposition")
    print("Note: This is a simplified demonstration circuit")

    # Add a barrier for visualization
    circuit.barrier(range(NUM_PIXELS))

    # Step 3: Measure all qubits
    for i in range(NUM_PIXELS):
        circuit.measure(i)

    return circuit


def load_qasm_circuit(qasm_file_path):
    """
    Load a circuit from a QASM file.
    """
    try:
        with open(qasm_file_path, 'r') as f:
            qasm_string = f.read()

        print(f"Loaded QASM from {qasm_file_path}")
        print(f"QASM length: {len(qasm_string)} characters")

        # Create circuit from QASM
        circuit = Circuit.from_ir(qasm_string, inputs={"format": "OPENQASM"})
        return circuit
    except Exception as e:
        print(f"Error loading QASM: {e}")
        return None


def run_simulation(circuit, shots=1000):
    """
    Run the circuit on AWS Braket Local Simulator.

    Args:
        circuit: Braket Circuit object
        shots: Number of measurement shots (default 1000)
    """
    # Create local simulator device (completely FREE)
    device = LocalSimulator()

    print(f"\n{'='*60}")
    print("Running on AWS Braket Local Simulator (FREE)")
    print(f"Shots: {shots}")
    print(f"{'='*60}\n")

    # Execute the circuit
    start_time = time.time()
    task = device.run(circuit, shots=shots)

    # Get results
    result = task.result()
    elapsed_time = time.time() - start_time

    print(f"Execution completed in {elapsed_time:.2f} seconds")

    return result


def analyze_results(result):
    """
    Analyze measurement results to check if H, B, or Y patterns were found.
    """
    print(f"\n{'='*60}")
    print("RESULTS ANALYSIS")
    print(f"{'='*60}")

    measurement_counts = result.measurement_counts
    total_shots = sum(measurement_counts.values())

    print(f"\nTotal measurements: {total_shots}")
    print(f"Unique states observed: {len(measurement_counts)}")

    # Sort by count (most frequent first)
    sorted_counts = sorted(measurement_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 10 most frequent states:")
    print(f"{'Bitstring':<20} {'Decimal':<10} {'Count':<8} {'Probability':<12} {'Pattern'}")
    print("-" * 70)

    found_patterns = []

    for i, (bitstring, count) in enumerate(sorted_counts[:10]):
        # Convert bitstring to decimal
        decimal_value = int(bitstring, 2)
        probability = count / total_shots

        # Check if this matches H, B, or Y
        pattern = ""
        if decimal_value == H_CONST:
            pattern = "H (Target!)"
            found_patterns.append(('H', count, probability))
        elif decimal_value == B_CONST:
            pattern = "B (Target!)"
            found_patterns.append(('B', count, probability))
        elif decimal_value == Y_CONST:
            pattern = "Y (Target!)"
            found_patterns.append(('Y', count, probability))

        print(f"{bitstring:<20} {decimal_value:<10} {count:<8} {probability:<12.4f} {pattern}")

    # Summary of target patterns
    print(f"\n{'='*60}")
    print("TARGET PATTERN DETECTION")
    print(f"{'='*60}")

    if found_patterns:
        print("\n✓ Found target patterns:")
        for pattern_name, count, prob in found_patterns:
            print(f"  - Pattern '{pattern_name}': {count} times ({prob*100:.2f}%)")
    else:
        print("\n✗ No target patterns (H, B, Y) found in top results")
        print("\nThis is expected with the simplified circuit.")
        print("For actual pattern detection, you need the full Grover oracle implementation.")

    print(f"\n{'='*60}")

    # Show expected vs actual
    print("\nEXPECTED TARGET VALUES:")
    print(f"  H: {H_CONST} = {bin(H_CONST)}")
    print(f"  B: {B_CONST} = {bin(B_CONST)}")
    print(f"  Y: {Y_CONST} = {bin(Y_CONST)}")

    return found_patterns


def main():
    """
    Main execution function.
    """
    print("="*60)
    print("GROVER'S ALGORITHM - AWS BRAKET LOCAL SIMULATOR")
    print("="*60)
    print("\nSearching for bitmap patterns: H, B, Y")
    print("Using 15 qubits (3×5 pixel grid)")
    print("\n")

    # Try to load the QASM file first
    qasm_file = "grover_hby_search.qasm"
    circuit = load_qasm_circuit(qasm_file)

    if circuit is None:
        print("\nFalling back to programmatic circuit creation...")
        circuit = create_grover_circuit()

    print(f"\nCircuit depth: {circuit.depth}")
    print(f"Circuit instructions: {len(circuit.instructions)}")

    # Run simulation with 1000 shots
    result = run_simulation(circuit, shots=1000)

    # Analyze results
    analyze_results(result)

    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. To run on AWS cloud (with free tier): Use run_on_braket_cloud.py")
    print("2. For full Grover implementation: Need complete QASM from Classiq")
    print("3. Check aws_setup_instructions.md for cloud setup")


if __name__ == "__main__":
    main()
