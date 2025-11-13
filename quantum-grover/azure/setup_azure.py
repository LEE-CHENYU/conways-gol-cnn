"""
Azure Quantum Setup and Connection

Sets up connection to Azure Quantum workspace and Quantinuum H2-1 hardware.

Prerequisites:
1. Azure account: https://portal.azure.com
2. Azure Quantum workspace created
3. Applied for $10,000 research credits
4. Installed: pip install azure-quantum[qiskit] qiskit
"""

import os
from azure.quantum.qiskit import AzureQuantumProvider


# Configuration
# TODO: Replace these with your actual values
RESOURCE_ID = os.environ.get(
    'AZURE_QUANTUM_RESOURCE_ID',
    "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Quantum/Workspaces/<workspace-name>"
)
LOCATION = os.environ.get('AZURE_QUANTUM_LOCATION', 'eastus')


def test_connection():
    """Test connection to Azure Quantum workspace"""
    print("="*60)
    print("AZURE QUANTUM CONNECTION TEST")
    print("="*60)

    try:
        print(f"\nConnecting to workspace...")
        print(f"  Resource ID: {RESOURCE_ID}")
        print(f"  Location: {LOCATION}")

        provider = AzureQuantumProvider(
            resource_id=RESOURCE_ID,
            location=LOCATION
        )

        print("\n✓ Connected successfully!")

        # List available backends
        print("\nAvailable backends:")
        backends = provider.backends()
        for backend in backends:
            print(f"  - {backend.name()}")
            if 'quantinuum' in backend.name().lower():
                print(f"    Status: {backend.status()}")

        # Try to get Quantinuum H2-1
        print("\nChecking Quantinuum H2-1 access...")
        try:
            h2_backend = provider.get_backend("quantinuum.qpu.h2-1")
            print(f"✓ Quantinuum H2-1 available!")
            print(f"  Backend: {h2_backend}")

            # Get backend configuration
            config = h2_backend.configuration()
            print(f"\nH2-1 Configuration:")
            print(f"  Qubits: {config.n_qubits if hasattr(config, 'n_qubits') else 'N/A'}")
            print(f"  Basis gates: {config.basis_gates if hasattr(config, 'basis_gates') else 'N/A'}")

        except Exception as e:
            print(f"✗ Could not access H2-1: {e}")

        # Check syntax checker (FREE)
        try:
            syntax_checker = provider.get_backend("quantinuum.sim.h2-1sc")
            print(f"\n✓ Syntax checker available (FREE for validation)")
        except:
            print(f"\n✗ Syntax checker not available")

        # Check emulator
        try:
            emulator = provider.get_backend("quantinuum.sim.h2-1e")
            print(f"✓ Emulator available (uses eHQCs)")
        except:
            print(f"✗ Emulator not available")

        print("\n" + "="*60)
        print("SETUP COMPLETE")
        print("="*60)
        print("\nYou're ready to run quantum circuits on Azure Quantum!")

        return provider

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check RESOURCE_ID is correct")
        print("2. Ensure you have proper permissions")
        print("3. Verify workspace exists in Azure Portal")
        print("4. Check environment variables:")
        print(f"   export AZURE_QUANTUM_RESOURCE_ID='<your-resource-id>'")
        print(f"   export AZURE_QUANTUM_LOCATION='{LOCATION}'")

        return None


def setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("AZURE QUANTUM SETUP INSTRUCTIONS")
    print("="*60)

    print("\n1. Create Azure Account")
    print("   - Go to https://portal.azure.com")
    print("   - Sign up (credit card needed for verification)")

    print("\n2. Create Azure Quantum Workspace")
    print("   - In Azure Portal, search 'Azure Quantum'")
    print("   - Click 'Create'")
    print("   - Select region: East US or West US")
    print("   - Add provider: Quantinuum")
    print("   - Note your Resource ID")

    print("\n3. Apply for Free Credits")
    print("   - Visit Azure Quantum Credits Program")
    print("   - Apply for $10,000 research credits")
    print("   - Automatic $500 credits per provider")

    print("\n4. Install SDK")
    print("   pip install azure-quantum[qiskit] qiskit matplotlib")

    print("\n5. Configure Connection")
    print("   export AZURE_QUANTUM_RESOURCE_ID='/subscriptions/<id>/...'")
    print("   export AZURE_QUANTUM_LOCATION='eastus'")

    print("\n6. Test Connection")
    print("   python setup_azure.py")

    print("\n" + "="*60)


if __name__ == "__main__":
    # Check if configuration is set
    if "<subscription-id>" in RESOURCE_ID:
        print("⚠ WARNING: RESOURCE_ID not configured!")
        print("\nPlease set your Azure Quantum workspace details:")
        print("1. Edit this file and replace <subscription-id>, etc.")
        print("2. OR set environment variable AZURE_QUANTUM_RESOURCE_ID")
        print("\n")
        setup_instructions()
    else:
        # Test connection
        provider = test_connection()

        if provider:
            print("\n✓ Setup successful! You can now run quantum programs.")
            print("\nNext steps:")
            print("1. Run: python grover_h2_optimized.py")
            print("2. Check docs/cost_analysis.md for budget planning")
