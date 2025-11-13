from classiq import *

# Simple test functions
@qfunc
def prepare_minus_state(x: QBit):
    X(x)
    H(x)

@qfunc
def uniform_superposition(reg: QArray):
    apply_to_all(lambda qb: H(qb), reg)

H_CONST = 0b101101111101101
B_CONST = 0b110101110101110
Y_CONST = 0b101010010010010
NUM_PIXELS = 15

@qperm
def oracle_black_box(res: QBit, x: Const[QNum]):
    res ^= (x == H_CONST) | (x == B_CONST) | (x == Y_CONST)

@qperm(disable_perm_check=True)
def oracle_pixels(pixels: Const[QArray[QBit]]):
    aux = QBit()
    allocate(aux)
    prepare_minus_state(aux)
    x = QNum()
    bind(pixels, x)
    oracle_black_box(aux, x)
    bind(x, pixels)
    invert(lambda: prepare_minus_state(aux))
    free(aux)

@qperm
def not_equal_zero(aux_bit: QBit, val: Const[QNum]):
    aux_bit ^= (val == 0)
    X(aux_bit)

@qfunc
def initial_state_diffuser(pixels: QArray[QBit]):
    uniform_superposition(pixels)
    packed = QNum()
    bind(pixels, packed)
    aux = QBit()
    allocate(aux)
    prepare_minus_state(aux)
    not_equal_zero(aux, packed)
    invert(lambda: prepare_minus_state(aux))
    free(aux)
    bind(packed, pixels)
    invert(lambda: uniform_superposition(pixels))

@qfunc
def my_grover_operator(pixels: QArray[QBit]):
    oracle_pixels(pixels)
    initial_state_diffuser(pixels)

NUM_GROVER_ITERS = 20

@qfunc
def main(pixels: Output[QArray[QBit]]):
    allocate(NUM_PIXELS, pixels)
    uniform_superposition(pixels)
    for _ in range(NUM_GROVER_ITERS):
        my_grover_operator(pixels)

# Create model using the proper approach
model = create_model(main)

# Write to JSON - this should create a proper .qprog format
from classiq.interface.generator.model.model import Model

# Serialize the model
model_str = str(model)  # This returns the QMOD string representation

# Try the internal serialization
try:
    # The model string is actually QMOD format, we need to synthesize to get qprog
    # But since we can't synthesize, let's save the QMOD in a format that might work

    # Write the QMOD representation
    with open("grover_hby_search_model.txt", "w") as f:
        f.write(model_str)

    print("✓ Saved QMOD representation to grover_hby_search_model.txt")

    # Try using QuantumProgram.parse to create a structure
    # A .qprog file is essentially a synthesized quantum program in JSON format
    # Since we can't synthesize without API access, we can't create a true .qprog

    print("\nUnfortunately, a .qprog file can only be created after synthesis.")
    print("A .qprog is a synthesized quantum circuit, not just the high-level model.")
    print("\nAlternative: Generate QASM directly from a simple circuit")

except Exception as e:
    print(f"Error: {e}")
