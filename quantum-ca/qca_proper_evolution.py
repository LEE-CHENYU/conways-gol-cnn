"""
Proper Quantum Cellular Automata Evolution

The KEY INSIGHT: We need to encode row-by-row evolution, not just column probabilities!

APPROACH: Use quantum circuit as a CA rule that evolves row-by-row
- Start with random seed row
- Apply quantum CA rule to generate next row
- Repeat 5 times to get 5x5 grid
- Optimize the CA rule parameters to produce target letter

This is TRUE cellular automata evolution!
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

# Target patterns
TARGETS = {
    "H": [[1,0,0,0,1], [1,0,0,0,1], [1,1,1,1,1], [1,0,0,0,1], [1,0,0,0,1]],
    "I": [[1,1,1,1,1], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [1,1,1,1,1]],
}


def quantum_ca_rule(prev_row, params):
    """
    Apply quantum CA rule to get next row.

    Args:
        prev_row: list of 5 bits [0,1,0,1,0]
        params: 10 rotation parameters for the quantum circuit

    Returns:
        next_row: list of 5 bits
    """
    qc = QuantumCircuit(5, 5)

    # Initialize qubits based on previous row
    for i, bit in enumerate(prev_row):
        if bit == 1:
            qc.x(i)

    # Apply parameterized quantum CA evolution
    # Layer 1: Local rotations (5 params)
    for i in range(5):
        qc.ry(params[i], i)

    # Layer 2: Neighbor interactions
    for i in range(4):
        qc.cz(i, i+1)

    # Layer 3: More rotations (5 params)
    for i in range(5):
        qc.rx(params[5 + i], i)

    # Wrap-around interaction (periodic boundary)
    qc.cz(4, 0)

    qc.measure(range(5), range(5))

    # Run circuit
    job = backend.run(qc, shots=100)
    result = job.result()
    counts = result.get_counts()

    # Get most common outcome
    most_common = max(counts.items(), key=lambda x: x[1])[0]
    next_row = [int(bit) for bit in most_common[::-1]]

    return next_row


def evolve_ca_from_seed(seed_row, params, num_rows=5):
    """
    Evolve cellular automata for num_rows steps.

    Args:
        seed_row: initial 5-bit row
        params: CA rule parameters
        num_rows: number of rows to generate

    Returns:
        grid: num_rows × 5 bitmap
    """
    grid = [seed_row]

    for _ in range(num_rows - 1):
        next_row = quantum_ca_rule(grid[-1], params)
        grid.append(next_row)

    return grid


def optimize_ca_rule(target_letter, iterations=20):
    """
    Optimize CA rule parameters to produce target letter.

    Strategy:
    1. Try different seed rows
    2. Optimize CA rule parameters
    3. Evaluate fitness against target
    """
    target = TARGETS[target_letter]

    # Try multiple seed rows and parameter sets
    best_fitness = 0
    best_grid = None
    best_params = None
    best_seed = None

    print(f"\nOptimizing CA rule for letter '{target_letter}'...\n")

    for iteration in range(iterations):
        # Random seed row and parameters
        seed_row = [np.random.randint(2) for _ in range(5)]
        params = np.random.uniform(-np.pi, np.pi, 10)

        # Evolve CA
        grid = evolve_ca_from_seed(seed_row, params, num_rows=5)

        # Calculate fitness
        matches = sum(
            1 for r in range(5) for c in range(5)
            if grid[r][c] == target[r][c]
        )
        fitness = matches / 25.0

        if fitness > best_fitness:
            best_fitness = fitness
            best_grid = grid
            best_params = params
            best_seed = seed_row
            print(f"Iteration {iteration+1}: NEW BEST fitness = {fitness:.2f}")
            print(f"  Seed: {seed_row}")
            print(f"  Grid:")
            for row in grid:
                print(f"    {row}")

        # Early stopping
        if best_fitness >= 0.95:
            print(f"\nExcellent match found! Stopping early.")
            break

    return best_grid, best_params, best_seed, best_fitness


def fitness_score(grid, target):
    """Calculate fitness between grid and target."""
    matches = sum(
        1 for r in range(5) for c in range(5)
        if grid[r][c] == target[r][c]
    )
    return matches / 25.0


def refine_ca_rule(seed_row, params, target_letter, iterations=10):
    """
    Given a good starting point, refine parameters.
    """
    target = TARGETS[target_letter]
    best_params = params.copy()
    best_fitness = 0

    print(f"\nRefining CA rule...")

    for i in range(iterations):
        # Mutate parameters
        noise = np.random.normal(0, 0.3, 10)
        new_params = best_params + noise
        new_params = np.clip(new_params, -np.pi, np.pi)

        # Evolve
        grid = evolve_ca_from_seed(seed_row, new_params, num_rows=5)
        fitness = fitness_score(grid, target)

        if fitness > best_fitness:
            best_fitness = fitness
            best_params = new_params
            print(f"  Iteration {i+1}: fitness = {fitness:.2f}")
            for row in grid:
                print(f"    {row}")

    final_grid = evolve_ca_from_seed(seed_row, best_params, num_rows=5)
    return final_grid, best_params, best_fitness


def bitmap_to_image(bitmap, scale=50, label=""):
    """Convert bitmap to image."""
    from PIL import ImageDraw, ImageFont

    h, w = len(bitmap), len(bitmap[0])
    img = Image.new("RGB", (w * scale, h * scale + 40), color=(255, 255, 255))
    pixels = img.load()

    # Draw grid
    for y in range(h):
        for x in range(w):
            color = (0, 0, 0) if bitmap[y][x] == 1 else (255, 255, 255)
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy + 40] = color

    # Draw grid lines
    draw = ImageDraw.Draw(img)
    for i in range(h + 1):
        draw.line([(0, i*scale + 40), (w*scale, i*scale + 40)], fill=(200, 200, 200), width=1)
    for i in range(w + 1):
        draw.line([(i*scale, 40), (i*scale, h*scale + 40)], fill=(200, 200, 200), width=1)

    # Add label
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), label, fill=(0, 0, 0), font=font)

    return img


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)

    print("="*80)
    print("PROPER QUANTUM CELLULAR AUTOMATA EVOLUTION")
    print("="*80)
    print("\nKey difference from previous approach:")
    print("  - Previous: 5 qubits → 5 column probs → same pattern in every row")
    print("  - This: Quantum CA rule evolves row-by-row from seed")
    print("  - Each row can be different!")
    print("="*80)

    letter = "I"  # Simpler target for demo

    # Step 1: Find good CA rule
    grid, params, seed, fitness = optimize_ca_rule(letter, iterations=30)

    print(f"\n{'='*80}")
    print(f"INITIAL OPTIMIZATION COMPLETE")
    print(f"Best fitness: {fitness:.2f}")
    print(f"Best seed: {seed}")
    print(f"{'='*80}")

    # Step 2: Refine
    if fitness < 0.9:
        grid, params, fitness = refine_ca_rule(seed, params, letter, iterations=15)

        print(f"\n{'='*80}")
        print(f"REFINEMENT COMPLETE")
        print(f"Final fitness: {fitness:.2f}")
        print(f"{'='*80}")

    # Create comparison
    target = TARGETS[letter]

    img_target = bitmap_to_image(target, label=f"TARGET: {letter}")
    img_evolved = bitmap_to_image(grid, label=f"EVOLVED (fitness={fitness:.2f})")

    # Save
    img_target.save("out/CA_TARGET.png")
    img_evolved.save("out/CA_EVOLVED.png")

    # Create animation showing evolution
    frames = [img_target]
    current_row = seed
    partial_grid = [current_row]

    for step in range(5):
        # Show current state
        display_grid = partial_grid + [[0]*5] * (5 - len(partial_grid))
        img = bitmap_to_image(display_grid, label=f"CA Evolution Step {step+1}/5")
        frames.append(img)

        if step < 4:
            # Evolve next row
            next_row = quantum_ca_rule(current_row, params)
            partial_grid.append(next_row)
            current_row = next_row

    frames.append(img_evolved)

    frames[0].save(
        "out/CA_EVOLUTION.gif",
        save_all=True,
        append_images=frames[1:],
        duration=1000,
        loop=0
    )

    print(f"\n✓ Saved: out/CA_EVOLUTION.gif")
    print(f"✓ Saved: out/CA_TARGET.png")
    print(f"✓ Saved: out/CA_EVOLVED.png")

    print("\n" + "="*80)
    print("This demonstrates TRUE CA evolution:")
    print("  • Each row evolved from previous row")
    print("  • Quantum circuit defines CA rule")
    print("  • Optimization finds CA rule that produces target pattern")
    print("="*80 + "\n")
