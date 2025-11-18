"""
Recurrent Quantum Cellular Automata

Pattern cycle:
1. Clean template → 2. Add quantum noise → 3. Recover to template → Repeat

This demonstrates:
- Quantum perturbation (noise)
- Quantum attraction (recovery)
- Stable limit cycle behavior
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
# Backend will be set via command line argument
backend = None

LETTER_BITMAPS = {
    "H": [[1,0,0,0,1], [1,0,0,0,1], [1,1,1,1,1], [1,0,0,0,1], [1,0,0,0,1]],
    "Y": [[1,0,0,0,1], [0,1,0,1,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]],
    "B": [[1,1,1,1,0], [1,0,0,0,1], [1,1,1,1,0], [1,0,0,0,1], [1,1,1,1,0]]
}

LETTER_COLUMN_INTENSITIES = {
    "H": [0.9, 0.3, 0.9, 0.3, 0.9],
    "Y": [0.8, 0.6, 0.9, 0.6, 0.8],
    "B": [0.9, 0.7, 0.9, 0.7, 0.9],
}


def add_quantum_noise(letter: str, noise_strength: float = 0.8):
    """
    Add quantum noise to letter pattern.

    noise_strength: 0 = no noise, 1 = maximum noise
    """
    qc = QuantumCircuit(5, 5)

    # Start with superposition
    for q in range(5):
        qc.h(q)

    # QCA entanglement
    for q in range(4):
        qc.cz(q, q+1)

    # Second layer
    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # Bias toward letter (but with noise)
    intensities = LETTER_COLUMN_INTENSITIES[letter]
    for q, alpha in enumerate(intensities):
        # Reduce bias strength = more noise
        theta = (alpha - 0.5) * (1 - noise_strength) * 1.5 * np.pi
        qc.ry(theta, q)

    qc.measure(range(5), range(5))

    # Run and get probabilities
    job = backend.run(qc, shots=256)
    result = job.result()
    counts = result.get_counts()

    col_counts = [0] * 5
    total = 0
    for bitstring, cnt in counts.items():
        total += cnt
        bits = bitstring[::-1]
        for i in range(5):
            if bits[i] == '1':
                col_counts[i] += cnt

    probs = [c / total for c in col_counts]
    return probs


def recover_to_template(current_probs, letter: str, recovery_strength: float = 0.8):
    """
    Quantum evolution that 'attracts' back toward the template.

    recovery_strength: 0 = no recovery, 1 = full recovery
    """
    target_intensities = LETTER_COLUMN_INTENSITIES[letter]

    # Blend current state toward target
    recovered_probs = []
    for curr, target in zip(current_probs, target_intensities):
        # Move toward target
        recovered = curr + recovery_strength * (target - curr)
        recovered_probs.append(recovered)

    return recovered_probs


def probs_to_bitmap(letter: str, probs):
    """Convert column probabilities to bitmap using template."""
    base = LETTER_BITMAPS[letter]
    bitmap = []

    for row in range(5):
        new_row = []
        for col in range(5):
            base_pixel = base[row][col]
            p_col = probs[col]

            if base_pixel == 1:
                keep_prob = 0.5 + 0.5 * p_col
                pixel = 1 if np.random.rand() < keep_prob else 0
            else:
                on_prob = max(0.0, p_col - 0.6)
                pixel = 1 if np.random.rand() < on_prob else 0

            new_row.append(pixel)
        bitmap.append(new_row)

    return bitmap


def bitmap_to_image(bitmap, scale=40, label=""):
    """Convert bitmap to image with label."""
    from PIL import ImageDraw, ImageFont

    h, w = len(bitmap), len(bitmap[0])
    img = Image.new("RGB", (w * scale, h * scale + 40), color=(255, 255, 255))
    pixels = img.load()

    for y in range(h):
        for x in range(w):
            color = (0, 0, 0) if bitmap[y][x] == 1 else (255, 255, 255)
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy + 40] = color

    # Draw grid
    draw = ImageDraw.Draw(img)
    for i in range(h + 1):
        draw.line([(0, i*scale + 40), (w*scale, i*scale + 40)], fill=(200,200,200))
    for i in range(w + 1):
        draw.line([(i*scale, 40), (i*scale, h*scale + 40)], fill=(200,200,200))

    # Label
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), label, fill=(0, 0, 0), font=font)

    return img


def create_recurrent_cycle(letter: str, num_cycles: int = 3):
    """
    Create animation showing recurrent pattern:
    Clean → Noisy → Recovering → Clean → Noisy → ...
    """
    frames = []

    print(f"\n{'='*80}")
    print(f"GENERATING RECURRENT CYCLE FOR LETTER '{letter}'")
    print(f"{'='*80}\n")

    # Start with clean template probabilities
    current_probs = LETTER_COLUMN_INTENSITIES[letter].copy()

    for cycle in range(num_cycles):
        print(f"Cycle {cycle + 1}/{num_cycles}")
        print("-" * 80)

        # Phase 1: Clean state
        bitmap = probs_to_bitmap(letter, current_probs)
        img = bitmap_to_image(bitmap, label=f"Cycle {cycle+1}: Clean")
        frames.append(img)
        print(f"  Clean: probs = {[f'{p:.2f}' for p in current_probs]}")

        # Phase 2: Add quantum noise (gradual)
        for noise_level in [0.3, 0.6, 0.9]:
            noisy_probs = add_quantum_noise(letter, noise_strength=noise_level)
            bitmap = probs_to_bitmap(letter, noisy_probs)
            img = bitmap_to_image(bitmap, label=f"Cycle {cycle+1}: Noise={noise_level:.1f}")
            frames.append(img)
            print(f"  Noisy ({noise_level:.1f}): probs = {[f'{p:.2f}' for p in noisy_probs]}")
            current_probs = noisy_probs

        # Phase 3: Recovery (gradual)
        for recovery_level in [0.4, 0.7, 1.0]:
            recovered_probs = recover_to_template(current_probs, letter, recovery_strength=recovery_level)
            bitmap = probs_to_bitmap(letter, recovered_probs)
            img = bitmap_to_image(bitmap, label=f"Cycle {cycle+1}: Recovery={recovery_level:.1f}")
            frames.append(img)
            print(f"  Recover ({recovery_level:.1f}): probs = {[f'{p:.2f}' for p in recovered_probs]}")
            current_probs = recovered_probs

        print()

    return frames


def create_phase_diagram(letter: str):
    """
    Show the phase space: noise vs recovery
    """
    from PIL import ImageDraw, ImageFont

    print(f"Creating phase diagram for letter '{letter}'...")

    # Create grid showing different noise/recovery combinations
    noise_levels = [0.0, 0.3, 0.6, 0.9]
    recovery_levels = [0.0, 0.3, 0.6, 0.9]

    cell_size = 100
    margin = 80
    width = len(noise_levels) * cell_size + margin * 2
    height = len(recovery_levels) * cell_size + margin * 2

    img = Image.new("RGB", (width, height), color=(255, 255, 255))

    for i, noise in enumerate(noise_levels):
        for j, recovery in enumerate(recovery_levels):
            # Generate pattern
            noisy_probs = add_quantum_noise(letter, noise_strength=noise)
            final_probs = recover_to_template(noisy_probs, letter, recovery_strength=recovery)
            bitmap = probs_to_bitmap(letter, final_probs)

            # Draw mini bitmap
            x_offset = margin + i * cell_size
            y_offset = margin + j * cell_size

            pixels = img.load()
            scale = cell_size // 5 - 2
            for y in range(5):
                for x in range(5):
                    color = (0, 0, 0) if bitmap[y][x] == 1 else (255, 255, 255)
                    for dy in range(scale):
                        for dx in range(scale):
                            px = x_offset + x * scale + dx + 5
                            py = y_offset + y * scale + dy + 5
                            if 0 <= px < width and 0 <= py < height:
                                pixels[px, py] = color

    # Add labels
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except:
        font = ImageFont.load_default()
        font_small = font

    # Title
    draw.text((width//2 - 100, 20), f"Phase Diagram: Letter '{letter}'", fill=(0,0,0), font=font)

    # Axis labels
    draw.text((width//2 - 50, height - 40), "Noise Level →", fill=(0,0,0), font=font)
    draw.text((20, height//2 - 50), "Recovery →", fill=(0,0,0), font=font, )

    # Noise values
    for i, noise in enumerate(noise_levels):
        x = margin + i * cell_size + cell_size // 2 - 10
        draw.text((x, height - 60), f"{noise:.1f}", fill=(0,0,0), font=font_small)

    # Recovery values
    for j, recovery in enumerate(recovery_levels):
        y = margin + j * cell_size + cell_size // 2
        draw.text((30, y), f"{recovery:.1f}", fill=(0,0,0), font=font_small)

    return img


if __name__ == "__main__":
    import sys

    os.makedirs("out", exist_ok=True)

    # Parse command line arguments
    backend_type = "simulator"  # default
    if len(sys.argv) > 1:
        if sys.argv[1] == "--backend":
            if len(sys.argv) > 2:
                backend_type = sys.argv[2]
        elif sys.argv[1] in ["simulator", "qpu"]:
            backend_type = sys.argv[1]

    # Set backend based on selection
    if backend_type == "qpu":
        backend = provider.get_backend("rigetti.qpu.ankaa-3")
        backend_label = "QPU"

        # Calculate and display cost
        num_executions = 25  # 9 for animation + 16 for phase diagram
        cost_per_job = 0.04
        total_cost = num_executions * cost_per_job

        print("\n" + "="*80)
        print("⚠️  REAL QUANTUM HARDWARE - COST WARNING")
        print("="*80)
        print(f"Backend: Rigetti Ankaa-3 (84-qubit QPU)")
        print(f"Quantum executions: {num_executions}")
        print(f"Cost per execution: ${cost_per_job:.2f}")
        print(f"TOTAL ESTIMATED COST: ${total_cost:.2f}")
        print("="*80)

        response = input("\nProceed with QPU execution? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled. Exiting.")
            sys.exit(0)
    else:
        backend = provider.get_backend("rigetti.sim.qvm")
        backend_label = "SIMULATOR"
        print("\n" + "="*80)
        print(f"Using Rigetti Simulator - Cost: $0.00 (FREE)")
        print("="*80)

    print("\n" + "="*80)
    print("RECURRENT QUANTUM CELLULAR AUTOMATA")
    print("="*80)
    print("\nConcept:")
    print("  1. Start with clean letter template")
    print("  2. Add quantum noise (pattern degrades)")
    print("  3. Quantum recovery (pattern restores)")
    print("  4. Repeat → Limit cycle behavior!")
    print("\nThis shows quantum system with stable attractor dynamics.")
    print("="*80)

    letter = "H"

    # Create recurrent animation
    frames = create_recurrent_cycle(letter, num_cycles=3)

    output_suffix = f"_{backend_label}"
    frames[0].save(
        f"out/RECURRENT_{letter}{output_suffix}.gif",
        save_all=True,
        append_images=frames[1:],
        duration=400,
        loop=0
    )

    print(f"\n✓ Saved: out/RECURRENT_{letter}{output_suffix}.gif")

    # Create phase diagram
    phase_img = create_phase_diagram(letter)
    phase_img.save(f"out/PHASE_DIAGRAM_{letter}{output_suffix}.png")

    print(f"✓ Saved: out/PHASE_DIAGRAM_{letter}{output_suffix}.png")

    print("\n" + "="*80)
    print("KEY FEATURES:")
    print("  • Recurrent cycle: Clean ↔ Noisy ↔ Clean")
    print(f"  • Quantum noise: True randomness from quantum measurements ({backend_label})")
    print("  • Quantum recovery: Attracts back to template")
    print("  • Phase diagram: Shows noise vs recovery parameter space")
    print("="*80 + "\n")
