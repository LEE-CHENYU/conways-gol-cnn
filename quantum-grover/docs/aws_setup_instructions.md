# AWS Braket Setup Instructions

Complete guide to running your Grover's algorithm quantum circuit on AWS Braket.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Local Testing (FREE)](#local-testing-free)
4. [Cloud Setup](#cloud-setup)
5. [Running on AWS](#running-on-aws)
6. [Cost Management](#cost-management)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Software Requirements
- Python 3.8 or higher
- pip package manager
- AWS CLI (optional but recommended)

### Install Required Packages

```bash
# Install from requirements file
pip install -r requirements_braket.txt

# Or install manually
pip install amazon-braket-sdk boto3
```

---

## AWS Account Setup

### Step 1: Create AWS Account

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow the registration process
4. You'll need:
   - Email address
   - Credit card (for verification, won't be charged with free tier)
   - Phone number

### Step 2: Enable AWS Braket

1. Sign in to AWS Console
2. Search for "Braket" in the services search bar
3. Click "Amazon Braket"
4. Click "Get Started" if prompted
5. Accept the terms of service

### Step 3: Create IAM User (Recommended for CLI access)

1. Go to IAM (Identity and Access Management)
2. Click "Users" → "Add user"
3. User name: `braket-user` (or your choice)
4. Select: "Programmatic access"
5. Click "Next: Permissions"
6. Attach policies:
   - `AmazonBraketFullAccess`
   - `AmazonS3FullAccess` (or create custom policy with limited S3 access)
7. Click through to create user
8. **IMPORTANT:** Save the Access Key ID and Secret Access Key

---

## Local Testing (FREE)

The local simulator runs entirely on your machine at no cost.

### Quick Start

```bash
# Run on local simulator (completely FREE)
python run_on_braket.py
```

This will:
- Execute your circuit on your local machine
- Run 1000 measurement shots
- Display results and analysis
- Take about 30-60 seconds

**Advantages:**
- Completely FREE
- No AWS setup required
- Instant execution
- Up to 25 qubits supported

**Limitations:**
- Limited to 25 qubits
- Slower than cloud simulators for large circuits
- No access to real quantum hardware

---

## Cloud Setup

### Step 1: Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
pip install awscli

# Verify installation
aws --version
```

### Step 2: Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: [From IAM user creation]
- **AWS Secret Access Key**: [From IAM user creation]
- **Default region**: `us-east-1` (or `us-west-1`)
- **Default output format**: `json`

### Step 3: Create S3 Bucket

AWS Braket requires an S3 bucket to store results. The bucket name **must** start with `amazon-braket-`.

```bash
# Create bucket (replace YOUR-NAME with something unique)
aws s3 mb s3://amazon-braket-YOUR-NAME-grover --region us-east-1

# Verify bucket was created
aws s3 ls | grep amazon-braket
```

**Important Notes:**
- Bucket names must be globally unique
- Must start with `amazon-braket-`
- Recommended region: `us-east-1` or `us-west-1`

### Step 4: Set Environment Variable (Optional)

```bash
# Add to your ~/.bashrc or ~/.zshrc
export BRAKET_S3_BUCKET="amazon-braket-YOUR-NAME-grover"

# Or set for current session
export BRAKET_S3_BUCKET="amazon-braket-YOUR-NAME-grover"
```

Or edit `run_on_braket_cloud.py` and change:
```python
DEFAULT_S3_BUCKET = "amazon-braket-your-bucket-name"  # Change this line
```

---

## Running on AWS

### Option 1: Local Simulator (FREE)

```bash
python run_on_braket.py
```

**Use this for:**
- Testing and development
- Unlimited runs
- Quick iteration

### Option 2: Cloud Simulator (FREE tier: 1 hour/month)

```bash
python run_on_braket_cloud.py
```

**Choose between:**
- **SV1**: State vector simulator (up to 34 qubits) - Default, best for most cases
- **TN1**: Tensor network simulator (up to 50 qubits) - For sparse circuits
- **DM1**: Density matrix simulator (up to 17 qubits) - For noisy simulations

**When to use:**
- Circuit too large for local simulator (>25 qubits)
- Need faster execution
- Testing before running on real hardware

### Option 3: Quantum Hardware (Expensive - Not Recommended)

Real quantum computers are available but expensive:
- Cost: $0.30-0.35 per task + $0.00145-0.003 per shot
- For 1000 shots: ~$1.75-3.35 per run
- Current hardware has high noise (results may not be accurate)

**Only use hardware if:**
- You have specific research requirements
- You understand quantum noise and error mitigation
- Budget allows

---

## Cost Management

### Free Tier

AWS Braket free tier (first year):
- **1 hour per month** of simulation time on SV1, TN1, or DM1
- This is usually enough for 30-120 runs of your circuit
- Resets monthly

### Cost Breakdown

| Service | Free Tier | Cost After Free Tier |
|---------|-----------|----------------------|
| Local Simulator | Unlimited FREE | Always FREE |
| Cloud Simulator (SV1/TN1/DM1) | 1 hour/month | $0.075/minute |
| S3 Storage | 5 GB | $0.023/GB/month |
| Data Transfer | 1 GB/month | Minimal |

### Estimated Costs for Your Circuit

**For 100 runs:**
- Local: **FREE**
- Cloud (with free tier): **FREE to $7.50**
- Cloud (without free tier): **$7.50**
- Real QPU: **$175-335**

### Tips to Minimize Costs

1. **Always test locally first**
   ```bash
   python run_on_braket.py  # Test here first
   ```

2. **Monitor usage**
   ```bash
   # Check AWS Braket usage
   aws braket list-quantum-tasks
   ```

3. **Set up billing alerts**
   - AWS Console → Billing → Billing Preferences
   - Enable "Receive Billing Alerts"
   - Create CloudWatch alarm for spending threshold

4. **Use AWS Cost Explorer**
   - Track daily spending
   - Set budgets

5. **Clean up S3 regularly**
   ```bash
   # List objects in bucket
   aws s3 ls s3://amazon-braket-YOUR-NAME-grover/

   # Delete old results (optional)
   aws s3 rm s3://amazon-braket-YOUR-NAME-grover/grover-results/ --recursive
   ```

---

## Troubleshooting

### Problem: "No module named 'braket'"

**Solution:**
```bash
pip install amazon-braket-sdk
```

### Problem: "Unable to locate credentials"

**Solution:**
```bash
# Reconfigure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Problem: "S3 bucket not found"

**Solution:**
```bash
# Check bucket exists
aws s3 ls | grep amazon-braket

# Create if missing
aws s3 mb s3://amazon-braket-YOUR-NAME-grover --region us-east-1

# Verify bucket name in script
grep "DEFAULT_S3_BUCKET" run_on_braket_cloud.py
```

### Problem: "Access Denied" when running cloud simulator

**Solution:**

1. Check IAM permissions:
   ```bash
   aws iam list-attached-user-policies --user-name braket-user
   ```

2. Ensure user has these policies:
   - `AmazonBraketFullAccess`
   - `AmazonS3FullAccess` (or custom S3 policy)

3. Check bucket policy allows your IAM user

### Problem: Circuit execution fails with "qelib1.inc not found"

**Solution:**

The QASM file references a standard library that's not available locally. Either:

1. Use the programmatic circuit (it will fall back automatically)
2. Generate proper QASM from Classiq with synthesis API access
3. Remove the `include "qelib1.inc"` line and use inline gate definitions

### Problem: "Region not supported"

**Solution:**

AWS Braket is only available in certain regions:
- `us-east-1` (N. Virginia) ✓ Recommended
- `us-west-1` (N. California)
- `us-west-2` (Oregon)
- `eu-west-2` (London)

Change region:
```bash
aws configure set region us-east-1
```

### Problem: Results don't show H, B, or Y patterns

**Expected Behavior:**

The current circuit is simplified and won't find the target patterns. This is normal.

**Why:**
- Full Grover's oracle requires 100-1000 gates to check for specific patterns
- Current circuit only demonstrates infrastructure
- Need complete QASM from Classiq synthesis to actually find patterns

**Next Steps:**
1. Get Classiq API access to synthesize full circuit
2. Or manually implement the complete oracle (advanced)

---

## Next Steps

### Current Status
✅ Local simulator working
✅ Infrastructure ready
⚠️ Circuit is simplified (won't find H/B/Y patterns)

### To Get Full Functionality

1. **Option A: Get Classiq API Access**
   - Contact support@classiq.io
   - Request API synthesis permissions
   - Run `qa_test.py` to generate complete QASM
   - Use generated QASM with Braket

2. **Option B: Manual Implementation**
   - Implement Grover oracle manually
   - Create controlled gates for pattern matching
   - Add diffuser operator
   - Repeat for 20 iterations

3. **Option C: Use as Template**
   - Current code works as template
   - Modify oracle for your own search problems
   - Test with local simulator
   - Scale to cloud when ready

---

## Resources

### AWS Documentation
- [AWS Braket Documentation](https://docs.aws.amazon.com/braket/)
- [Braket Python SDK](https://github.com/aws/amazon-braket-sdk-python)
- [Braket Examples](https://github.com/aws/amazon-braket-examples)

### Pricing
- [AWS Braket Pricing](https://aws.amazon.com/braket/pricing/)
- [AWS Free Tier](https://aws.amazon.com/free/)

### Support
- [AWS Braket Forum](https://repost.aws/tags/TA4ckPBVVkQ_2H0lcXBV_5NQ/amazon-braket)
- [AWS Support](https://console.aws.amazon.com/support/)

### Quantum Computing Resources
- [Grover's Algorithm Tutorial](https://qiskit.org/textbook/ch-algorithms/grover.html)
- [Classiq Documentation](https://docs.classiq.io/)

---

## Quick Reference

```bash
# Test locally (FREE, no AWS needed)
python run_on_braket.py

# Run on AWS cloud (requires setup)
python run_on_braket_cloud.py

# Check AWS credentials
aws sts get-caller-identity

# List Braket tasks
aws braket list-quantum-tasks

# Check S3 bucket
aws s3 ls s3://amazon-braket-YOUR-NAME-grover/

# Monitor costs
# Go to: AWS Console → Billing Dashboard
```

---

**Questions?** Check the troubleshooting section or open an issue on GitHub.

**Ready to run?** Start with `python run_on_braket.py` for FREE local testing!
