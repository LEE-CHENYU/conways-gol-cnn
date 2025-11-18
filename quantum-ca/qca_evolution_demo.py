"""
Quick demo: How to evolve random quantum states toward letter patterns

Three approaches explained:
1. Template-based (current approach) - FAKE evolution
2. Optimization-based (genetic/gradient) - REAL evolution
3. Amplitude encoding - Direct quantum encoding
"""

from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit
import numpy as np
from PIL import Image
import os

workspace = Workspace(
    resource_id="/subscriptions/668927d0-86e8-499a-a9b2-771c02e9dd82/resourceGroups/quantum-conway-rg/providers/Microsoft.Quantum/workspaces/conway-quantum-ws",
    location="eastus"
)

provider = AzureQuantumProvider(workspace)
backend = provider.get_backend("rigetti.sim.qvm")

# Target letter 'H'
TARGET = [[1,0,0,0,1], [1,0,0,0,1], [1,1,1,1,1], [1,0,0,0,1], [1,0,0,0,1]]


def bitmap_to_image(bitmap, scale=40, label=""):
    """Convert bitmap to image with optional label."""
    h, w = len(bitmap), len(bitmap[0])
    img = Image.new("RGB", (w * scale, h * scale + 30), color=(255, 255, 255))
    pixels = img.load()

    # Draw bitmap
    for y in range(h):
        for x in range(w):
            val = (0, 0, 0) if bitmap[y][x] == 1 else (255, 255, 255)
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy + 30] = val

    # Add label at top
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()
    draw.text((10, 5), label, fill=(0, 0, 0), font=font)

    return img


def fitness_score(bitmap):
    """How well does bitmap match target H?"""
    matches = sum(
        1 for r in range(5) for c in range(5)
        if bitmap[r][c] == TARGET[r][c]
    )
    return matches / 25.0


# =============================================================================
# APPROACH 1: Random quantum state (no optimization)
# =============================================================================

def random_quantum_bitmap():
    """Pure random quantum measurement."""
    qc = QuantumCircuit(5, 5)

    # Just random superposition - no structure
    for q in range(5):
        qc.h(q)

    # Some entanglement
    for q in range(4):
        qc.cz(q, q+1)

    qc.measure(range(5), range(5))

    job = backend.run(qc, shots=256)
    result = job.result()
    counts = result.get_counts()

    # Convert to bitmap using column probabilities
    col_probs = [0] * 5
    total = sum(counts.values())

    for bitstring, count in counts.items():
        bits = bitstring[::-1]
        for i in range(5):
            if bits[i] == '1':
                col_probs[i] += count / total

    # Each row uses column probability
    bitmap = []
    for row in range(5):
        bitmap.append([1 if col_probs[c] > 0.5 else 0 for c in range(5)])

    return bitmap, col_probs


# =============================================================================
# APPROACH 2: Optimized quantum state (simple hill climbing)
# =============================================================================

def optimized_quantum_bitmap(iterations=10):
    """Use optimization to find parameters that produce H."""

    # Parameter space: rotation angles for each qubit
    best_params = np.random.uniform(-np.pi, np.pi, 15)
    best_fitness = 0

    print(f"\nOptimizing quantum circuit parameters...")

    for i in range(iterations):
        # Try current parameters
        qc = QuantumCircuit(5, 5)

        # Apply parameterized rotations
        for q in range(5):
            qc.rx(best_params[q*3], q)
            qc.ry(best_params[q*3 + 1], q)
            qc.rz(best_params[q*3 + 2], q)

        # QCA evolution
        for q in range(4):
            qc.cz(q, q+1)

        qc.measure(range(5), range(5))

        # Run and evaluate
        job = backend.run(qc, shots=256)
        result = job.result()
        counts = result.get_counts()

        col_probs = [0] * 5
        total = sum(counts.values())

        for bitstring, count in counts.items():
            bits = bitstring[::-1]
            for idx in range(5):
                if bits[idx] == '1':
                    col_probs[idx] += count / total

        bitmap = []
        for row in range(5):
            bitmap.append([1 if col_probs[c] > 0.5 else 0 for c in range(5)])

        fitness = fitness_score(bitmap)
        print(f"  Iteration {i+1}: fitness={fitness:.2f}, probs={[f'{p:.2f}' for p in col_probs]}")

        if fitness > best_fitness:
            best_fitness = fitness
        else:
            # Hill climbing: try mutation
            mutation = np.random.normal(0, 0.5, 15)
            best_params = best_params + mutation
            best_params = np.clip(best_params, -np.pi, np.pi)

    # Return best result
    qc = QuantumCircuit(5, 5)
    for q in range(5):
        qc.rx(best_params[q*3], q)
        qc.ry(best_params[q*3 + 1], q)
        qc.rz(best_params[q*3 + 2], q)
    for q in range(4):
        qc.cz(q, q+1)
    qc.measure(range(5), range(5))

    job = backend.run(qc, shots=256)
    result = job.result()
    counts = result.get_counts()

    col_probs = [0] * 5
    total = sum(counts.values())
    for bitstring, count in counts.items():
        bits = bitstring[::-1]
        for idx in range(5):
            if bits[idx] == '1':
                col_probs[idx] += count / total

    bitmap = [[1 if col_probs[c] > 0.5 else 0 for c in range(5)] for _ in range(5)]
    return bitmap, col_probs, best_fitness


# =============================================================================
# APPROACH 3: Amplitude encoding (direct quantum state preparation)
# =============================================================================

def amplitude_encoded_bitmap():
    """
    Encode the target pattern DIRECTLY in quantum amplitudes.
    This is the 'correct' quantum way but requires more qubits.

    For 5x5 bitmap, we'd need 25 qubits (one per pixel).
    Let's do a simplified 5-column version.
    """
    qc = QuantumCircuit(5, 5)

    # Target column pattern for 'H': [1, 0, 1, 0, 1]
    # We want higher probability for columns 0, 2, 4

    # Method: Use targeted rotations to bias toward desired pattern
    target_cols = [0.9, 0.2, 0.9, 0.2, 0.9]  # H's vertical bars

    for q, target in enumerate(target_cols):
        # Ry rotation to set probability
        # P(|1>) = sin²(θ/2)
        # For P = target, θ = 2*arcsin(√target)
        theta = 2 * np.arcsin(np.sqrt(target))
        qc.ry(theta, q)

    # Add some QCA dynamics for variation
    for q in range(4):
        qc.cz(q, q+1)

    # Small perturbation
    for q in range(5):
        qc.ry(0.2, q)

    qc.measure(range(5), range(5))

    job = backend.run(qc, shots=256)
    result = job.result()
    counts = result.get_counts()

    col_probs = [0] * 5
    total = sum(counts.values())
    for bitstring, count in counts.items():
        bits = bitstring[::-1]
        for idx in range(5):
            if bits[idx] == '1':
                col_probs[idx] += count / total

    bitmap = [[1 if col_probs[c] > 0.5 else 0 for c in range(5)] for _ in range(5)]
    return bitmap, col_probs


# =============================================================================
# Main demonstration
# =============================================================================

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)

    print("\n" + "="*80)
    print("QUANTUM EVOLUTION: THREE APPROACHES")
    print("="*80)
    print("\nTarget: Letter 'H'")
    print("Goal: Start from random → evolve toward H\n")

    frames = []

    # Show target
    target_img = bitmap_to_image(TARGET, label="TARGET: Letter H")
    frames.append(target_img)

    # Approach 1: Random (no evolution)
    print("\n" + "-"*80)
    print("APPROACH 1: Random Quantum State (No Optimization)")
    print("-"*80)
    bitmap1, probs1 = random_quantum_bitmap()
    fitness1 = fitness_score(bitmap1)
    print(f"Column probabilities: {[f'{p:.2f}' for p in probs1]}")
    print(f"Fitness vs H: {fitness1:.2f}")
    img1 = bitmap_to_image(bitmap1, label=f"Random (fitness={fitness1:.2f})")
    frames.append(img1)

    # Approach 2: Optimized
    print("\n" + "-"*80)
    print("APPROACH 2: Optimized Quantum State (Hill Climbing)")
    print("-"*80)
    bitmap2, probs2, fitness2 = optimized_quantum_bitmap(iterations=10)
    print(f"Final column probabilities: {[f'{p:.2f}' for p in probs2]}")
    print(f"Final fitness: {fitness2:.2f}")
    img2 = bitmap_to_image(bitmap2, label=f"Optimized (fitness={fitness2:.2f})")
    frames.append(img2)

    # Approach 3: Amplitude encoding
    print("\n" + "-"*80)
    print("APPROACH 3: Amplitude Encoding (Direct Preparation)")
    print("-"*80)
    bitmap3, probs3 = amplitude_encoded_bitmap()
    fitness3 = fitness_score(bitmap3)
    print(f"Column probabilities: {[f'{p:.2f}' for p in probs3]}")
    print(f"Fitness vs H: {fitness3:.2f}")
    img3 = bitmap_to_image(bitmap3, label=f"Amplitude Encoded (fitness={fitness3:.2f})")
    frames.append(img3)

    # Save comparison
    frames[0].save(
        "out/EVOLUTION_COMPARISON.gif",
        save_all=True,
        append_images=frames[1:],
        duration=1500,
        loop=0
    )

    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"Approach 1 (Random):             Fitness = {fitness1:.2f}")
    print(f"Approach 2 (Optimized):          Fitness = {fitness2:.2f}")
    print(f"Approach 3 (Amplitude Encoded):  Fitness = {fitness3:.2f}")
    print("\nSaved: out/EVOLUTION_COMPARISON.gif")
    print("="*80 + "\n")
