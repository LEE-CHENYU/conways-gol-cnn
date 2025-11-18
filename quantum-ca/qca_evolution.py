"""
Quantum Cellular Automata - TRUE Evolution Approach
Instead of using templates, evolve random states toward letter patterns
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

# Target patterns (what we want to evolve toward)
LETTER_BITMAPS = {
    "H": [[1,0,0,0,1], [1,0,0,0,1], [1,1,1,1,1], [1,0,0,0,1], [1,0,0,0,1]],
    "Y": [[1,0,0,0,1], [0,1,0,1,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]],
    "B": [[1,1,1,1,0], [1,0,0,0,1], [1,1,1,1,0], [1,0,0,0,1], [1,1,1,1,0]]
}


def fitness_function(bitmap, target_letter):
    """
    Measure how close a quantum-generated bitmap is to the target letter.
    Returns a score between 0 (no match) and 1 (perfect match).
    """
    target = LETTER_BITMAPS[target_letter]
    matches = 0
    total = 25

    for row in range(5):
        for col in range(5):
            if bitmap[row][col] == target[row][col]:
                matches += 1

    return matches / total


def build_parameterized_qca_circuit(params):
    """
    Build a quantum circuit with trainable parameters.
    Params: 15 rotation angles (3 per qubit: Rx, Ry, Rz)

    This represents a "genome" that can be optimized.
    """
    qc = QuantumCircuit(5, 5)

    # Layer 1: Initial rotations (parameterized)
    for q in range(5):
        qc.rx(params[q*3], q)
        qc.ry(params[q*3 + 1], q)
        qc.rz(params[q*3 + 2], q)

    # Layer 2: QCA neighbor entanglement
    for q in range(4):
        qc.cz(q, q+1)

    # Layer 3: Second set of rotations (parameterized)
    # (We only have 15 params, so reuse with negative sign)
    for q in range(5):
        qc.rx(-params[q*3] * 0.5, q)
        qc.ry(-params[q*3 + 1] * 0.5, q)

    # Layer 4: More entanglement
    for q in range(4):
        qc.cz(q, q+1)

    qc.measure(range(5), range(5))
    return qc


def run_circuit_and_get_bitmap(params, shots=256):
    """Run circuit with given parameters and decode into bitmap."""
    qc = build_parameterized_qca_circuit(params)
    job = backend.run(qc, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # Get column probabilities
    col_counts = [0] * 5
    total = 0
    for bitstring, cnt in counts.items():
        total += cnt
        bits = bitstring[::-1]
        for i in range(5):
            if bits[i] == '1':
                col_counts[i] += cnt

    probs = [c / total for c in col_counts]

    # Convert to bitmap using probabilities as pixel intensity
    bitmap = []
    for row in range(5):
        new_row = []
        for col in range(5):
            # Simple thresholding: >0.5 = pixel on
            pixel = 1 if probs[col] > 0.5 else 0
            new_row.append(pixel)
        bitmap.append(new_row)

    return bitmap, probs


def optimize_toward_letter(target_letter, generations=50, population_size=20):
    """
    Genetic algorithm to evolve quantum circuit parameters toward target letter.

    Algorithm:
    1. Start with random population of parameter sets
    2. Evaluate fitness of each
    3. Select best performers
    4. Mutate/crossover to create new generation
    5. Repeat
    """
    print(f"\n{'='*80}")
    print(f"EVOLVING QUANTUM CIRCUIT TO PRODUCE LETTER '{target_letter}'")
    print(f"{'='*80}\n")

    # Initialize random population
    population = [np.random.uniform(-np.pi, np.pi, 15) for _ in range(population_size)]

    best_fitness_history = []
    best_params = None
    best_fitness = 0

    for gen in range(generations):
        # Evaluate fitness for each individual
        fitnesses = []
        for i, params in enumerate(population):
            bitmap, probs = run_circuit_and_get_bitmap(params, shots=100)
            fitness = fitness_function(bitmap, target_letter)
            fitnesses.append(fitness)

            if fitness > best_fitness:
                best_fitness = fitness
                best_params = params.copy()

        best_fitness_history.append(best_fitness)
        avg_fitness = np.mean(fitnesses)

        print(f"Generation {gen+1}/{generations}: Best={best_fitness:.3f}, Avg={avg_fitness:.3f}")

        # Early stopping if we found perfect match
        if best_fitness >= 0.95:
            print(f"✓ Found excellent match! Stopping early.")
            break

        # Selection: keep top 50%
        sorted_indices = np.argsort(fitnesses)[::-1]
        elite_size = population_size // 2
        elite = [population[i] for i in sorted_indices[:elite_size]]

        # Create new generation
        new_population = elite.copy()

        # Mutation + Crossover
        while len(new_population) < population_size:
            if np.random.rand() < 0.7:  # Crossover
                parent1, parent2 = np.random.choice(len(elite), 2, replace=False)
                child = (elite[parent1] + elite[parent2]) / 2
            else:  # Mutation
                parent = elite[np.random.randint(len(elite))]
                child = parent.copy()

            # Add mutation noise
            mutation = np.random.normal(0, 0.3, 15)
            child = child + mutation
            child = np.clip(child, -np.pi, np.pi)

            new_population.append(child)

        population = new_population

    return best_params, best_fitness, best_fitness_history


def bitmap_to_image(bitmap, scale=40):
    h, w = len(bitmap), len(bitmap[0])
    img = Image.new("L", (w * scale, h * scale), color=255)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            val = 0 if bitmap[y][x] == 1 else 255
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy] = val
    return img


def visualize_evolution(target_letter, best_params, num_samples=4):
    """Generate multiple samples showing evolved pattern."""
    print(f"\nGenerating {num_samples} samples of evolved '{target_letter}'...")

    frames = []
    for i in range(num_samples):
        bitmap, probs = run_circuit_and_get_bitmap(best_params, shots=256)
        print(f"  Sample {i+1}: probs={[f'{p:.3f}' for p in probs]}")
        img = bitmap_to_image(bitmap, scale=40)
        frames.append(img)

    return frames


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)

    print("\n" + "="*80)
    print("QUANTUM EVOLUTION APPROACH")
    print("="*80)
    print("\nInstead of using templates, we'll EVOLVE random quantum states")
    print("toward letter patterns using a genetic algorithm.\n")
    print("Process:")
    print("1. Start with random quantum circuit parameters (15D search space)")
    print("2. Run quantum circuit → get bitmap")
    print("3. Measure fitness vs target letter")
    print("4. Evolve parameters using genetic algorithm")
    print("5. Repeat until convergence")
    print("="*80)

    # Evolve toward 'H'
    letter = 'H'
    best_params, best_fitness, history = optimize_toward_letter(
        letter,
        generations=30,  # Reduced for demo
        population_size=15
    )

    print(f"\n{'='*80}")
    print(f"EVOLUTION COMPLETE!")
    print(f"Final fitness: {best_fitness:.3f}")
    print(f"Best parameters: {best_params}")
    print(f"{'='*80}\n")

    # Generate evolved letter
    frames = visualize_evolution(letter, best_params, num_samples=4)

    frames[0].save(
        f"out/EVOLVED_{letter}.gif",
        save_all=True,
        append_images=frames[1:],
        duration=800,
        loop=0
    )
    print(f"\n✓ Saved: out/EVOLVED_{letter}.gif")

    print("\n" + "="*80)
    print("KEY DIFFERENCE FROM TEMPLATE APPROACH:")
    print("  • Template: Start with letter → add quantum noise")
    print("  • Evolution: Start with random → optimize toward letter")
    print("  • This demonstrates TRUE quantum evolution!")
    print("="*80 + "\n")
