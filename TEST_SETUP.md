# Quick Test Setup Guide

## TL;DR - Just Run This

```bash
# From the graphit project root directory
./run_tests.sh
```

This script will:
1. Check current imports
2. Install all required GraphIt packages
3. Install test dependencies
4. Run the VertexAI tests

## If You Get Import Errors

The most common issue is that GraphIt packages aren't installed. Here's how to fix it:

### Step 1: Check What's Missing
```bash
./check_imports.py
```

### Step 2: Install GraphIt Packages
```bash
./install_packages.sh
```

### Step 3: Verify Installation
```bash
./check_imports.py
```

### Step 4: Run Tests
```bash
pytest tests/unit/test_text_completion/test_vertexai_processor.py -v
```

## What the Scripts Do

### `check_imports.py`
- Tests all the imports needed for the tests
- Shows exactly what's missing
- Helps diagnose import issues

### `install_packages.sh`
- Installs graphit-base (required by others)
- Installs graphit-cli
- Installs graphit-vertexai
- Installs graphit-flow
- Uses `pip install -e .` for editable installs

### `run_tests.sh`
- Runs all the above steps in order
- Installs test dependencies
- Runs the VertexAI tests
- Shows clear output at each step

## Manual Installation (If Scripts Don't Work)

```bash
# Install packages in order (base first!)
cd graphit-base && pip install -e . && cd ..
cd graphit-cli && pip install -e . && cd ..
cd graphit-vertexai && pip install -e . && cd ..
cd graphit-flow && pip install -e . && cd ..

# Install test dependencies
cd tests && pip install -r requirements.txt && cd ..

# Run tests
pytest tests/unit/test_text_completion/test_vertexai_processor.py -v
```

## Common Issues

1. **"No module named 'graphit'"** → Run `./install_packages.sh`
2. **"No module named 'graphit.base'"** → Install graphit-base first
3. **"No module named 'graphit.model.text_completion.vertexai'"** → Install graphit-vertexai
4. **Scripts not executable** → Run `chmod +x *.sh`
5. **Wrong directory** → Make sure you're in the project root (where README.md is)

## Test Results

When working correctly, you should see:
- ✅ All imports successful
- 139 test cases running
- Tests passing (or failing for logical reasons, not import errors)

## Getting Help

If you're still having issues:
1. Share the output of `./check_imports.py`
2. Share the exact error message
3. Confirm you're in the right directory: `/home/mark/work/graphit.ai/graphit`