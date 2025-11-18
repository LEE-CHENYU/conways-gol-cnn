"""
Compare QCA with and without letter-specific targeting
"""

from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit
import numpy as np
from collections import Counter
from PIL import Image
import os

# Connect to Azure Quantum
workspace = Workspace(
    resource_id="/subscriptions/668927d0-86e8-499a-a9b2-771c02e9dd82/resourceGroups/quantum-conway-rg/providers/Microsoft.Quantum/workspaces/conway-quantum-ws",
    location="eastus"
)

provider = AzureQuantumProvider(workspace)
backend = provider.get_backend("rigetti.sim.qvm")

LETTER_BITMAPS = {
    "H": [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,1,1,1,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    "Y": [
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    "B": [
        [1,1,1,1,0],
        [1,0,0,0,1],
        [1,1,1,1,0],
        [1,0,0,0,1],
        [1,1,1,1,0],
    ]
}

LETTER_COLUMN_INTENSITIES = {
    "H": [0.9, 0.3, 0.9, 0.3, 0.9],
    "Y": [0.8, 0.6, 0.9, 0.6, 0.8],
    "B": [0.9, 0.7, 0.9, 0.7, 0.9],
}


def build_qca_circuit_NO_TARGET(letter: str) -> QuantumCircuit:
    """Pure QCA without letter-specific biasing"""
    qc = QuantumCircuit(5, 5)
    qc.name = f"QCA_{letter}_NO_TARGET"

    # Step 1: Seed – create superposition on all qubits
    for q in range(5):
        qc.h(q)

    # Step 2: Simple 1D QCA evolution – CZ between neighbors
    for q in range(4):
        qc.cz(q, q+1)

    # Second time step
    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # Step 3: NO LETTER-SPECIFIC BIAS - SKIPPED!
    # (This is the key difference)

    # Step 4: Measure
    qc.measure(range(5), range(5))
    return qc


def build_qca_circuit_WITH_TARGET(letter: str) -> QuantumCircuit:
    """QCA with letter-specific biasing (original version)"""
    qc = QuantumCircuit(5, 5)
    qc.name = f"QCA_{letter}_WITH_TARGET"

    # Step 1: Seed
    for q in range(5):
        qc.h(q)

    # Step 2: QCA evolution
    for q in range(4):
        qc.cz(q, q+1)

    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # Step 3: Letter-specific bias
    intensities = LETTER_COLUMN_INTENSITIES[letter]
    for q, alpha in enumerate(intensities):
        theta = (alpha - 0.5) * 1.5 * np.pi
        qc.ry(theta, q)

    # Step 4: Measure
    qc.measure(range(5), range(5))
    return qc


def run_qca_and_get_column_probs(qc: QuantumCircuit, shots: int = 256):
    job = backend.run(qc, shots=shots)
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
    return probs, counts


def make_bitmap_from_template_and_probs(letter: str, probs):
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


def bitmap_to_image(bitmap, scale=40, on_color=0, off_color=255):
    h = len(bitmap)
    w = len(bitmap[0])
    img = Image.new("L", (w * scale, h * scale), color=off_color)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            val = on_color if bitmap[y][x] == 1 else off_color
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy] = val
    return img


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    letters = ["H", "Y", "H", "B"]

    print("\n" + "="*70)
    print("COMPARISON: QCA WITH vs WITHOUT Letter-Specific Targeting")
    print("="*70 + "\n")

    # Generate WITHOUT target
    print("🔴 PART 1: Pure QCA (NO letter-specific biasing)")
    print("-" * 70)
    frames_no_target = []
    for letter in letters:
        qc = build_qca_circuit_NO_TARGET(letter)
        print(f"Running pure QCA for letter {letter}...")
        probs, counts = run_qca_and_get_column_probs(qc)
        print(f"  Column probabilities: {[f'{p:.3f}' for p in probs]}")

        bitmap = make_bitmap_from_template_and_probs(letter, probs)
        img = bitmap_to_image(bitmap, scale=40)
        frames_no_target.append(img)

    frames_no_target[0].save(
        "out/HYHB_qca_NO_TARGET.gif",
        save_all=True,
        append_images=frames_no_target[1:],
        duration=800,
        loop=0
    )
    print("✓ Saved: out/HYHB_qca_NO_TARGET.gif\n")

    # Generate WITH target
    print("🟢 PART 2: QCA WITH letter-specific biasing (original)")
    print("-" * 70)
    frames_with_target = []
    for letter in letters:
        qc = build_qca_circuit_WITH_TARGET(letter)
        print(f"Running targeted QCA for letter {letter}...")
        probs, counts = run_qca_and_get_column_probs(qc)
        print(f"  Column probabilities: {[f'{p:.3f}' for p in probs]}")

        bitmap = make_bitmap_from_template_and_probs(letter, probs)
        img = bitmap_to_image(bitmap, scale=40)
        frames_with_target.append(img)

    frames_with_target[0].save(
        "out/HYHB_qca_WITH_TARGET.gif",
        save_all=True,
        append_images=frames_with_target[1:],
        duration=800,
        loop=0
    )
    print("✓ Saved: out/HYHB_qca_WITH_TARGET.gif\n")

    print("="*70)
    print("ANALYSIS:")
    print("  WITHOUT targeting: Column probabilities will be ~0.5 (uniform)")
    print("                    Letters will be mostly random quantum noise")
    print("  WITH targeting:    Column probabilities biased toward letter shape")
    print("                    Letters retain recognizable structure")
    print("="*70 + "\n")
