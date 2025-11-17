"""
HYHB Quantum Cellular Automata (QCA) - Rigetti Implementation

Generates letter patterns (H, Y, H, B) using quantum circuits that mimic
cellular automata behavior. Uses 5-qubit circuits with neighbor entanglement
and quantum measurement statistics to create organic-looking letter patterns.

BACKENDS:
  - rigetti.sim.qvm: Free quantum simulator (default)
  - rigetti.qpu.ankaa-3: Real 84-qubit quantum computer (~$0.04/job)

COST ESTIMATES:
  - Simulator: $0.00 (unlimited free usage)
  - QPU: ~$0.16 total for HYHB (4 letters × $0.04)

USAGE:
  python quantum-ca/qca.py                    # Free simulator (default)

  # To use real quantum hardware, edit main() and uncomment QPU line

REQUIREMENTS:
  pip install azure-quantum qiskit 'azure-quantum[qiskit]' pillow numpy

OUTPUT:
  Animated GIF with 4 frames showing quantum-perturbed letter patterns
  Location: out/HYHB_qca_simulator.gif
"""

from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit
import numpy as np
from collections import Counter
from PIL import Image
import os

# ================================
# 1. Connect to Azure Quantum
# ================================

workspace = Workspace(
    resource_id="/subscriptions/668927d0-86e8-499a-a9b2-771c02e9dd82/resourceGroups/quantum-conway-rg/providers/Microsoft.Quantum/workspaces/conway-quantum-ws",
    location="eastus"
)

provider = AzureQuantumProvider(workspace)

# Backend selection: use Rigetti simulator (free) or QPU (Ankaa-3, ~$0.04/job)
# Simulator: rigetti.sim.qvm (free, unlimited)
# QPU: rigetti.qpu.ankaa-3 (~$0.02 per 10ms execution time)
backend = provider.get_backend("rigetti.sim.qvm")
# backend = provider.get_backend("rigetti.qpu.ankaa-3")   # <- switch for real quantum hardware


# ================================
# 2. Letter templates (5x5 bitmaps)
# ================================

# 5x5 grids, top row first, 1 = filled pixel, 0 = empty
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

# For each letter, define a "column intensity" in [0,1] for qubits 0..4
# These control how strongly the QCA biases each column toward "ink".
LETTER_COLUMN_INTENSITIES = {
    "H": [0.9, 0.3, 0.9, 0.3, 0.9],
    "Y": [0.8, 0.6, 0.9, 0.6, 0.8],
    "B": [0.9, 0.7, 0.9, 0.7, 0.9],
}


# ================================
# 3. Build the 5-qubit QCA-ish circuit
# ================================

def build_qca_circuit_for_letter(letter: str) -> QuantumCircuit:
    """Construct a shallow 5-qubit circuit with:
       - global superposition
       - neighbor entangling (QCA-style)
       - letter-specific columns via small Ry biases
    """
    qc = QuantumCircuit(5, 5)
    qc.name = f"QCA_{letter}"

    # Step 1: Seed – create superposition on all qubits
    for q in range(5):
        qc.h(q)

    # Step 2: Simple 1D QCA evolution – CZ between neighbors
    for q in range(4):
        qc.cz(q, q+1)

    # Optionally, one more “time step” of H+CZ to make patterns richer
    for q in range(5):
        qc.h(q)
    for q in range(4):
        qc.cz(q, q+1)

    # Step 3: Letter-specific bias
    intensities = LETTER_COLUMN_INTENSITIES[letter]
    for q, alpha in enumerate(intensities):
        # Centered around 0.5; scale controls how strong the bias is
        theta = (alpha - 0.5) * 1.5 * np.pi  # radians
        qc.ry(theta, q)

    # Step 4: Measure
    qc.measure(range(5), range(5))
    return qc


# ================================
# 4. Run on IonQ and get column probabilities
# ================================

def run_qca_and_get_column_probs(letter: str, shots: int = 256):
    qc = build_qca_circuit_for_letter(letter)
    print(f"Submitting circuit for letter {letter} to backend {backend.name()} ...")

    job = backend.run(qc, shots=shots)
    result = job.result()

    counts = result.get_counts()
    # counts is a dict: {bitstring: shots}, bitstring like "01010"
    # We interpret bitstring as c4 c3 c2 c1 c0; we’ll reverse for q0..q4.
    col_counts = [0] * 5
    total = 0

    for bitstring, cnt in counts.items():
        total += cnt
        bits = bitstring[::-1]  # now bits[0] is q0, bits[4] is q4
        for i in range(5):
            if bits[i] == '1':
                col_counts[i] += cnt

    probs = [c / total for c in col_counts]
    return probs, counts


# ================================
# 5. Decode probs + template → 5x5 bitmap
# ================================

def make_bitmap_from_template_and_probs(letter: str, probs):
    """Take the clean 5x5 template for the letter and 'quantum-perturb' it.
       Higher prob on column i makes filled pixels more stable;
       lower prob makes them more likely to drop out, and empty pixels
       slightly more likely to turn on.
    """
    base = LETTER_BITMAPS[letter]
    bitmap = []

    for row in range(5):
        new_row = []
        for col in range(5):
            base_pixel = base[row][col]
            p_col = probs[col]   # 0..1

            if base_pixel == 1:
                # Filled pixels may randomly drop out if column prob is low
                keep_prob = 0.5 + 0.5 * p_col
                pixel = 1 if np.random.rand() < keep_prob else 0
            else:
                # Empty pixels may randomly turn on if column prob is high
                on_prob = max(0.0, p_col - 0.6)  # only strong columns leak ink
                pixel = 1 if np.random.rand() < on_prob else 0

            new_row.append(pixel)
        bitmap.append(new_row)

    return bitmap


# ================================
# 6. Render a 5x5 bitmap to an image
# ================================

def bitmap_to_image(bitmap, scale=40, on_color=0, off_color=255):
    """Convert 5x5 bitmap into a PIL image (5*scale x 5*scale)."""
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


# ================================
# 7. Put it all together for HYHB
# ================================

def generate_hyhb_gif(output_path="HYHB_qca.gif", backend_type="simulator"):
    """Generate HYHB animated GIF using quantum circuits.

    Args:
        output_path: Path to save the output GIF
        backend_type: "simulator" (free) or "qpu" (Ankaa-3, ~$0.16 total)
    """
    letters = ["H", "Y", "H", "B"]
    frames = []

    # Select backend and display cost estimate
    global backend
    if backend_type == "qpu":
        backend = provider.get_backend("rigetti.qpu.ankaa-3")
        estimated_cost = len(letters) * 0.04  # ~$0.04 per job
        print(f"\n{'='*60}")
        print(f"WARNING: Using Rigetti QPU - Estimated cost: ${estimated_cost:.2f}")
        print(f"{'='*60}\n")
    else:
        backend = provider.get_backend("rigetti.sim.qvm")
        print(f"\n{'='*60}")
        print(f"Using Rigetti Simulator - Cost: $0.00 (FREE)")
        print(f"{'='*60}\n")

    for letter in letters:

        probs, counts = run_qca_and_get_column_probs(letter, shots=256)
        print(f"Letter {letter} column probabilities: {probs}")
        print(f"Raw counts: {counts}")

        bitmap = make_bitmap_from_template_and_probs(letter, probs)
        img = bitmap_to_image(bitmap, scale=40)
        frames.append(img)

    # Save as animated GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=800,   # ms per frame
        loop=0
    )
    print(f"Saved GIF to {output_path}")


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)

    # Generate with free simulator (default)
    generate_hyhb_gif(output_path="out/HYHB_qca_simulator.gif", backend_type="simulator")

    # To use real quantum hardware (costs ~$0.16), uncomment below:
    # generate_hyhb_gif(output_path="out/HYHB_qca_qpu.gif", backend_type="qpu")