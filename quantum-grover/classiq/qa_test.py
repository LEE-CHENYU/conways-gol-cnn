from classiq import *


# ---------- 1. Basic helpers ----------

@qfunc
def prepare_minus_state(x: QBit):
    # |0> -> |-> = (|0> - |1>)/sqrt(2)
    X(x)
    H(x)


@qfunc
def uniform_superposition(reg: QArray):
    # Apply H to all qubits in the pixel register
    apply_to_all(lambda qb: H(qb), reg)


# ---------- 2. Bitmap encoding for H/B/Y (3×5) ----------

# 15-bit constants for H, B, Y.
# IMPORTANT: adjust bit order to match how `bind` packs QArray -> QNum on your setup.
H_CONST = 0b101101111101101
B_CONST = 0b110101110101110
Y_CONST = 0b101010010010010

NUM_PIXELS = 15


# ---------- 3. Oracle: mark H, B, Y ----------

@qperm
def oracle_black_box(res: QBit, x: Const[QNum]):
    # Set `res` = 1 iff x encodes H, B, or Y.
    # The ^= means "res = res XOR (condition)".
    # Bitwise OR is allowed between comparisons.
    res ^= (x == H_CONST) | (x == B_CONST) | (x == Y_CONST)


@qperm(disable_perm_check=True)
def oracle_pixels(pixels: Const[QArray[QBit]]):
    """
    Phase oracle over the 15-pixel bitmap.
    Implements a standard Grover phase kickback using an aux qubit in |->.
    """
    aux = QBit()
    allocate(aux)
    prepare_minus_state(aux)

    # Pack the pixel bits into a QNum so we can compare to integer constants.
    x = QNum()
    bind(pixels, x)  # pixels -> x

    oracle_black_box(aux, x)

    # Unbind to restore pixels
    bind(x, pixels)

    # Uncompute aux so it can be re-used, as in the official Grover workshop.
    invert(lambda: prepare_minus_state(aux))
    free(aux)


# ---------- 4. Optional: custom diffuser about uniform superposition ----------

@qfunc
def initial_state_diffuser(pixels: QArray[QBit]):
    """
    Reflection about the uniform superposition state A|0>, where A = uniform_superposition.
    This is the "Grover diffuser": A S_0 A^\dagger.
    """
    # Create A|0>
    uniform_superposition(pixels)

    # Pack to a QNum (so we can reuse the "zero diffuser" pattern)
    packed = QNum()
    bind(pixels, packed)

    # Zero-diffuser on packed:
    aux = QBit()
    allocate(aux)
    prepare_minus_state(aux)

    # Not-equal-zero test with phase kickback:
    @qperm
    def not_equal_zero(aux_bit: QBit, val: Const[QNum]):
        aux_bit ^= (val == 0)
        X(aux_bit)

    not_equal_zero(aux, packed)

    invert(lambda: prepare_minus_state(aux))
    free(aux)

    # Unpack back to pixels and uncompute A
    bind(packed, pixels)
    invert(lambda: uniform_superposition(pixels))


# ---------- 5. Grover operator (one iteration) ----------

@qfunc
def my_grover_operator(pixels: QArray[QBit]):
    # Oracle: flip phase on H/B/Y images
    oracle_pixels(pixels)

    # Diffuser: reflect about uniform superposition
    initial_state_diffuser(pixels)


# ---------- 6. Entry point ----------

NUM_GROVER_ITERS = 20  # for 15 qubits & 3 marked states, ~16–24 is good for 10–20% success

@qfunc
def main(pixels: Output[QArray[QBit]]):
    # Allocate 15 qubits, one per pixel
    allocate(NUM_PIXELS, pixels)

    # Prepare uniform superposition over all 2^15 bitmaps
    uniform_superposition(pixels)

    # Apply Grover iterations
    for _ in range(NUM_GROVER_ITERS):
        my_grover_operator(pixels)


# ---------- 7. Create model and export ----------

from classiq.interface.generator.model import Model
import json

# Build the model
qmod = create_model(main)

# The qmod object has a 'model' attribute that contains the actual Pydantic model
# We need to serialize this to JSON format for .qprog
if hasattr(qmod, 'model'):
    model_json = qmod.model.model_dump_json(indent=2)
else:
    # Fallback: try to get the serializable dict
    from classiq.interface.generator.model import SerializedModel
    model_json = qmod.get_model().model_dump_json(indent=2)

# Save to .qprog file (JSON format)
with open("grover_hby_search.qprog", "w") as f:
    f.write(model_json)

print("Model saved to grover_hby_search.qprog")
print("You can now upload this file to Classiq platform at https://platform.classiq.io")
print("File size:", len(model_json), "bytes")