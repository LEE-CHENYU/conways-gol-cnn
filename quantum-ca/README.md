# Quantum Cellular Automata (QCA) - HYHB Letter Generator

A quantum computing experiment that generates artistic letter patterns using quantum circuits inspired by cellular automata principles.

## Overview

This project uses **Rigetti's quantum computers** via **Azure Quantum** to create quantum-perturbed versions of the letters H, Y, H, B. The quantum circuits simulate cellular automata-like neighbor interactions through controlled-phase gates and quantum superposition.

## Features

- **5-qubit quantum circuits** with neighbor entanglement
- **Two execution modes**: Free simulator or real quantum hardware
- **Automatic cost tracking** with warnings before QPU usage
- **Visual output**: Animated GIF showing quantum noise effects

## Setup

### 1. Azure Quantum Workspace (Already Configured)

The workspace is already set up:
- **Resource Group**: `quantum-conway-rg`
- **Workspace**: `conway-quantum-ws`
- **Location**: `eastus`
- **Provider**: Rigetti (free simulator + QPU access)

### 2. Install Dependencies

```bash
pip install azure-quantum qiskit 'azure-quantum[qiskit]' pillow numpy
```

### 3. Azure Authentication

```bash
az login
az account set --subscription "668927d0-86e8-499a-a9b2-771c02e9dd82"
```

## Usage

### Run with Free Simulator (Default)

```bash
python quantum-ca/qca.py
```

**Output**: `out/HYHB_qca_simulator.gif`
**Cost**: $0.00 (unlimited free usage)

### Run on Real Quantum Hardware

Edit `qca.py` and uncomment the QPU line in `main()`:

```python
# Uncomment this line:
generate_hyhb_gif(output_path="out/HYHB_qca_qpu.gif", backend_type="qpu")
```

**Output**: `out/HYHB_qca_qpu.gif`
**Cost**: ~$0.16 (4 letters × $0.04 per job)

## Cost Breakdown

| Backend | Type | Cost per Job | Total (4 letters) |
|---------|------|--------------|-------------------|
| **rigetti.sim.qvm** | Simulator | $0.00 | **$0.00** |
| **rigetti.qpu.ankaa-3** | Real QPU (84 qubits) | ~$0.04 | ~$0.16 |

**Note**: QPU pricing is based on execution time (~100-200ms per circuit).

## How It Works

### Quantum Circuit Design

Each letter uses a 5-qubit circuit:

1. **Superposition**: Hadamard gates create equal probability states
2. **QCA Evolution**: CZ gates entangle neighboring qubits (mimicking CA neighbor interactions)
3. **Letter Encoding**: Ry rotations bias each qubit based on letter column intensities
4. **Measurement**: 256 shots produce probability distributions

### Letter Patterns

- **H**: High intensity on columns 0, 2, 4 (vertical bars)
- **Y**: Peak intensity on center column (convergence point)
- **B**: High intensity on columns 0, 2 (curved structure)

### Quantum Noise Effects

- **Simulator**: Clean, deterministic patterns
- **QPU**: Organic noise from real quantum decoherence and gate errors (~10% error rate)

## Output Examples

The generated GIF contains 4 frames (800ms each):

```
Frame 1: H (quantum-perturbed)
Frame 2: Y (quantum-perturbed)
Frame 3: H (quantum-perturbed)
Frame 4: B (quantum-perturbed)
```

Each frame is a 200×200 pixel image with black pixels on white background.

## Technical Details

### Rigetti Ankaa-3 QPU

- **Qubits**: 84 (we use 5)
- **Topology**: Square lattice with 4-fold connectivity
- **Gate Fidelity**: 99.5% (two-qubit)
- **Native Gates**: RX, RZ, iSWAP/fSim
- **Automatic Compilation**: H, CZ, Ry → native gate set

### Expected Fidelity

- **Circuit Depth**: ~10 layers (original) → ~25 layers (after compilation)
- **Estimated Fidelity**: ~90-92%
- **Result**: Visible quantum noise, ideal for artistic exploration

## Comparison: Rigetti vs IonQ

| Feature | Rigetti Ankaa-3 | IonQ Aria 1 |
|---------|----------------|-------------|
| Qubits | 84 | 25 |
| Technology | Superconducting | Trapped ion |
| Simulator Cost | **$0.00** | $0.00 |
| QPU Cost (this project) | **$0.16** | $49.68 |
| Gate Fidelity | 99.5% | 99.9% |
| **Available in Workspace** | ✅ Yes | ❌ No (requires subscription upgrade) |

**Verdict**: Rigetti is 300× cheaper and already configured!

## Troubleshooting

### Authentication Errors

```bash
az login
az account set --subscription "668927d0-86e8-499a-a9b2-771c02e9dd82"
```

### Module Not Found

```bash
pip install azure-quantum qiskit 'azure-quantum[qiskit]' pillow numpy
```

### Backend Not Found

Make sure you're using `rigetti.sim.qvm` (not `ionq.simulator`). The workspace was configured with Rigetti.

## Next Steps

- Compare simulator vs QPU outputs side-by-side
- Experiment with different qubit counts (3-qubit, 7-qubit)
- Try other Rigetti backends (Cepheus-1-36Q)
- Add classical CA comparison for benchmark

## References

- [Azure Quantum Documentation](https://learn.microsoft.com/en-us/azure/quantum/)
- [Rigetti Provider Documentation](https://learn.microsoft.com/en-us/azure/quantum/provider-rigetti)
- [Qiskit Documentation](https://qiskit.org/documentation/)

---

**Project**: Conway's Game of Life + CNN + Quantum CA Exploration
**Author**: Quantum CA Experiment
**Last Updated**: 2025-11-17
