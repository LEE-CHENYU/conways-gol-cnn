from classiq import *
import json
import inspect

# Import the main function from qa_test
import sys
sys.path.insert(0, '/Users/chenyusu/vscode/conways-gol-cnn')

# Rebuild just the model creation part
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

# Create the model
qmod = create_model(main)

# Explore what's available
print("Type of qmod:", type(qmod))
print("\nAvailable methods:")
for attr in dir(qmod):
    if not attr.startswith('_'):
        print(f"  {attr}")

# Try to get the underlying model
try:
    # Method 1: Check if there's a get_model method
    if hasattr(qmod, 'get_model'):
        model = qmod.get_model()
        print("\n✓ Found get_model() method")
        print("Model type:", type(model))

        # Try to serialize
        if hasattr(model, 'model_dump'):
            model_dict = model.model_dump()
            print("✓ Successfully serialized with model_dump()")
        elif hasattr(model, 'dict'):
            model_dict = model.dict()
            print("✓ Successfully serialized with dict()")

        # Save to file
        with open("grover_hby_search.qprog", "w") as f:
            json.dump(model_dict, f, indent=2)

        print("\n✓ Saved to grover_hby_search.qprog")
        print("File size:", len(json.dumps(model_dict)), "bytes")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTrying alternative method...")

    # Method 2: Use QuantumProgram.model_dump if available
    try:
        from classiq.interface.generator.model.model import Model as ModelClass
        print("Checking for Model serialization...")
    except:
        pass
