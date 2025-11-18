"""
TRUE Comparison: QCA with pure quantum output vs template-based
"""

from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# Connect to Azure Quantum
workspace = Workspace(
    resource_id="/subscriptions/668927d0-86e8-499a-a9b2-771c02e9dd82/resourceGroups/quantum-conway-rg/providers/Microsoft.Quantum/workspaces/conway-quantum-ws",
    location="eastus"
)

provider = AzureQuantumProvider(workspace)
backend = provider.get_backend("rigetti.sim.qvm")

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


def build_pure_qca_circuit() -> QuantumCircuit:
    """Pure QCA - NO letter info at all"""
    qc = QuantumCircuit(5, 5)
    qc.name = "PURE_QCA"

    # Superposition
    for q in range(5):
        qc.h(q)

    # QCA neighbor entanglement
    for q in range(4):
        qc.cz(q, q+1)

    # Second time step
    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # NO BIASING, NO TEMPLATE

    qc.measure(range(5), range(5))
    return qc


def build_targeted_qca_circuit(letter: str) -> QuantumCircuit:
    """QCA with letter-specific quantum biasing"""
    qc = QuantumCircuit(5, 5)
    qc.name = f"TARGETED_QCA_{letter}"

    for q in range(5):
        qc.h(q)

    for q in range(4):
        qc.cz(q, q+1)

    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # Letter-specific biasing
    intensities = LETTER_COLUMN_INTENSITIES[letter]
    for q, alpha in enumerate(intensities):
        theta = (alpha - 0.5) * 1.5 * np.pi
        qc.ry(theta, q)

    qc.measure(range(5), range(5))
    return qc


def run_qca(qc: QuantumCircuit, shots: int = 256):
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


def pure_quantum_to_bitmap(probs):
    """
    Create bitmap DIRECTLY from quantum probabilities
    NO TEMPLATE - just use probability as pixel intensity
    """
    bitmap = []
    for row in range(5):
        new_row = []
        for col in range(5):
            # Directly sample from quantum probability
            pixel = 1 if np.random.rand() < probs[col] else 0
            new_row.append(pixel)
        bitmap.append(new_row)
    return bitmap


def template_based_bitmap(letter: str, probs):
    """
    Traditional method: START with letter template, add quantum noise
    """
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


def bitmap_to_image(bitmap, scale=40):
    h = len(bitmap)
    w = len(bitmap[0])
    img = Image.new("L", (w * scale, h * scale), color=255)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            val = 0 if bitmap[y][x] == 1 else 255
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x*scale + dx, y*scale + dy] = val
    return img


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    letters = ["H", "Y", "H", "B"]

    print("\n" + "="*80)
    print("TRUE COMPARISON: Pure Quantum Output vs Template+Quantum")
    print("="*80 + "\n")

    # Method 1: PURE quantum (no template, no biasing)
    print("🔵 METHOD 1: Pure Quantum (no template, no letter biasing)")
    print("-" * 80)
    frames_pure = []
    qc = build_pure_qca_circuit()

    for i, letter in enumerate(letters):
        print(f"Run {i+1}/4 (label would be '{letter}' but circuit doesn't know this)...")
        probs, counts = run_qca(qc)
        print(f"  Column probabilities: {[f'{p:.3f}' for p in probs]}")

        bitmap = pure_quantum_to_bitmap(probs)
        img = bitmap_to_image(bitmap, scale=40)
        frames_pure.append(img)

    frames_pure[0].save(
        "out/PURE_QUANTUM.gif",
        save_all=True,
        append_images=frames_pure[1:],
        duration=800,
        loop=0
    )
    print("✓ Saved: out/PURE_QUANTUM.gif\n")

    # Method 2: Template + Quantum biasing
    print("🟢 METHOD 2: Template + Quantum Biasing (original approach)")
    print("-" * 80)
    frames_template = []

    for letter in letters:
        qc = build_targeted_qca_circuit(letter)
        print(f"Running for letter {letter} with template + biasing...")
        probs, counts = run_qca(qc)
        print(f"  Column probabilities: {[f'{p:.3f}' for p in probs]}")

        bitmap = template_based_bitmap(letter, probs)
        img = bitmap_to_image(bitmap, scale=40)
        frames_template.append(img)

    frames_template[0].save(
        "out/TEMPLATE_QUANTUM.gif",
        save_all=True,
        append_images=frames_template[1:],
        duration=800,
        loop=0
    )
    print("✓ Saved: out/TEMPLATE_QUANTUM.gif\n")

    print("="*80)
    print("KEY INSIGHT:")
    print("  Method 1: Probabilities ~0.5 → Random noise (no recognizable pattern)")
    print("  Method 2: Template provides structure, quantum just adds variation")
    print()
    print("The 'quantum' aspect is mostly aesthetic noise on top of classical templates!")
    print("="*80 + "\n")
