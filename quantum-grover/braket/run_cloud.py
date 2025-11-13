"""
Run Grover's Algorithm on AWS Braket Cloud Simulators

This script executes on AWS Braket cloud simulators (SV1, TN1, or DM1).
Requires AWS credentials and S3 bucket. Has 1 hour/month free tier.

Prerequisites:
1. AWS account with Braket access
2. AWS credentials configured (aws configure)
3. S3 bucket with name starting with "amazon-braket-"
"""

from braket.aws import AwsDevice
from braket.circuits import Circuit
import boto3
import time
import os

# Define the bitmap patterns we're searching for
H_CONST = 0b101101111101101  # 23533
B_CONST = 0b110101110101110  # 27566
Y_CONST = 0b101010010010010  # 21650

NUM_PIXELS = 15

# AWS Configuration
DEFAULT_S3_BUCKET = "amazon-braket-your-bucket-name"  # CHANGE THIS!
DEFAULT_S3_FOLDER = "grover-results"
DEFAULT_REGION = "us-east-1"


def check_aws_credentials():
    """
    Check if AWS credentials are configured.
    """
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials configured")
        print(f"  Account: {identity['Account']}")
        print(f"  User ARN: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"✗ AWS credentials not configured: {e}")
        print("\nRun: aws configure")
        print("Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        return False


def check_s3_bucket(bucket_name):
    """
    Check if S3 bucket exists and is accessible.
    """
    try:
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ S3 bucket '{bucket_name}' is accessible")
        return True
    except Exception as e:
        print(f"✗ S3 bucket '{bucket_name}' not accessible: {e}")
        print(f"\nCreate bucket with:")
        print(f"  aws s3 mb s3://{bucket_name} --region {DEFAULT_REGION}")
        return False


def create_grover_circuit():
    """
    Create a simplified Grover's algorithm circuit for demonstration.
    """
    circuit = Circuit()

    # Initialize all qubits in superposition
    print("Building circuit: Initializing superposition...")
    for i in range(NUM_PIXELS):
        circuit.h(i)

    print(f"Circuit has {NUM_PIXELS} qubits in superposition")
    print("Note: This is a simplified demonstration circuit")

    # Add a barrier
    circuit.barrier(range(NUM_PIXELS))

    # Measure all qubits
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

        # Create circuit from QASM
        circuit = Circuit.from_ir(qasm_string, inputs={"format": "OPENQASM"})
        return circuit
    except Exception as e:
        print(f"Error loading QASM: {e}")
        return None


def list_available_devices():
    """
    List available AWS Braket devices.
    """
    print("\n" + "="*60)
    print("AVAILABLE AWS BRAKET DEVICES")
    print("="*60)

    try:
        # Simulators
        simulators = [
            ("SV1", "arn:aws:braket:::device/quantum-simulator/amazon/sv1", "State vector simulator (up to 34 qubits)"),
            ("TN1", "arn:aws:braket:::device/quantum-simulator/amazon/tn1", "Tensor network simulator (up to 50 qubits)"),
            ("DM1", "arn:aws:braket:::device/quantum-simulator/amazon/dm1", "Density matrix simulator (up to 17 qubits)"),
        ]

        print("\nCloud Simulators (FREE tier: 1 hour/month):")
        for name, arn, description in simulators:
            print(f"  {name}: {description}")
            print(f"       ARN: {arn}")

        print("\nQuantum Hardware (Expensive - not recommended for testing):")
        print("  - IonQ Forte")
        print("  - Rigetti Ankaa-3")
        print("  - IQM Garnet")

    except Exception as e:
        print(f"Error listing devices: {e}")


def run_cloud_simulation(circuit, device_arn, s3_location, shots=1000):
    """
    Run the circuit on AWS Braket cloud simulator.

    Args:
        circuit: Braket Circuit object
        device_arn: ARN of the AWS Braket device
        s3_location: Tuple of (bucket, folder) for results
        shots: Number of measurement shots
    """
    bucket, folder = s3_location

    # Create AWS device
    device = AwsDevice(device_arn)

    print(f"\n{'='*60}")
    print(f"Running on AWS Braket: {device.name}")
    print(f"{'='*60}")
    print(f"Device ARN: {device_arn}")
    print(f"Shots: {shots}")
    print(f"Results: s3://{bucket}/{folder}/")
    print(f"{'='*60}\n")

    # Execute the circuit
    print("Submitting task to AWS Braket...")
    start_time = time.time()

    task = device.run(
        circuit,
        s3_location=(bucket, folder),
        shots=shots
    )

    print(f"Task ID: {task.id}")
    print(f"Task status: {task.state()}")

    # Wait for completion
    print("\nWaiting for results...")
    print("(This may take 30-60 seconds for cloud simulators)")

    result = task.result()
    elapsed_time = time.time() - start_time

    print(f"\n✓ Execution completed in {elapsed_time:.2f} seconds")
    print(f"Final status: {task.state()}")

    return result


def analyze_results(result):
    """
    Analyze measurement results.
    """
    print(f"\n{'='*60}")
    print("RESULTS ANALYSIS")
    print(f"{'='*60}")

    measurement_counts = result.measurement_counts
    total_shots = sum(measurement_counts.values())

    print(f"\nTotal measurements: {total_shots}")
    print(f"Unique states observed: {len(measurement_counts)}")

    # Sort by count
    sorted_counts = sorted(measurement_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 10 most frequent states:")
    print(f"{'Bitstring':<20} {'Decimal':<10} {'Count':<8} {'Probability':<12} {'Pattern'}")
    print("-" * 70)

    found_patterns = []

    for i, (bitstring, count) in enumerate(sorted_counts[:10]):
        decimal_value = int(bitstring, 2)
        probability = count / total_shots

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

    print(f"\n{'='*60}")
    print("TARGET PATTERN DETECTION")
    print(f"{'='*60}")

    if found_patterns:
        print("\n✓ Found target patterns:")
        for pattern_name, count, prob in found_patterns:
            print(f"  - Pattern '{pattern_name}': {count} times ({prob*100:.2f}%)")
    else:
        print("\n✗ No target patterns (H, B, Y) found")
        print("\nThis is expected with the simplified circuit.")

    return found_patterns


def main():
    """
    Main execution function.
    """
    print("="*60)
    print("GROVER'S ALGORITHM - AWS BRAKET CLOUD")
    print("="*60)

    # Check prerequisites
    print("\nChecking prerequisites...")
    if not check_aws_credentials():
        print("\n✗ Setup required. See aws_setup_instructions.md")
        return

    # Get S3 bucket from environment or use default
    s3_bucket = os.environ.get('BRAKET_S3_BUCKET', DEFAULT_S3_BUCKET)

    if s3_bucket == DEFAULT_S3_BUCKET:
        print(f"\n⚠ Using default S3 bucket name: {s3_bucket}")
        print("   Set BRAKET_S3_BUCKET environment variable or edit this script")

    if not check_s3_bucket(s3_bucket):
        print("\n✗ S3 bucket not configured. See aws_setup_instructions.md")
        return

    # List available devices
    list_available_devices()

    # Choose device (SV1 is recommended for general use)
    device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"

    print("\n" + "="*60)
    print(f"Using device: SV1 (State Vector Simulator)")
    print("="*60)

    # Load or create circuit
    qasm_file = "grover_hby_search.qasm"
    circuit = load_qasm_circuit(qasm_file)

    if circuit is None:
        print("\nFalling back to programmatic circuit creation...")
        circuit = create_grover_circuit()

    print(f"\nCircuit depth: {circuit.depth}")
    print(f"Circuit instructions: {len(circuit.instructions)}")

    # Run on cloud
    try:
        result = run_cloud_simulation(
            circuit,
            device_arn,
            s3_location=(s3_bucket, DEFAULT_S3_FOLDER),
            shots=1000
        )

        # Analyze results
        analyze_results(result)

        print("\n" + "="*60)
        print("CLOUD SIMULATION COMPLETE")
        print("="*60)
        print("\nCost estimate:")
        print("  - With free tier: FREE (first 1 hour/month)")
        print("  - Without free tier: ~$0.08-0.38 per run")
        print("\nResults saved to:")
        print(f"  s3://{s3_bucket}/{DEFAULT_S3_FOLDER}/")

    except Exception as e:
        print(f"\n✗ Error running cloud simulation: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials: aws sts get-caller-identity")
        print("2. Verify S3 bucket exists and starts with 'amazon-braket-'")
        print("3. Ensure region is correct (us-east-1 or us-west-1)")
        print("4. Check IAM permissions for Braket and S3")


if __name__ == "__main__":
    main()
