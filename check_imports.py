#!/usr/bin/env python3
"""
Check if GraphIt imports work correctly for testing
"""

import sys
import traceback

def check_import(module_name, description):
    """Try to import a module and report the result"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {description}: {module_name}")
        print(f"   Unexpected error: {e}")
        return False

def main():
    print("Checking GraphIt imports for testing...")
    print("=" * 50)
    
    imports_to_check = [
        ("graphit", "Base graphit package"),
        ("graphit.base", "Base classes"),
        ("graphit.base.llm_service", "LLM service base class"),
        ("graphit.schema", "Schema definitions"),
        ("graphit.exceptions", "Exception classes"),
        ("graphit.model", "Model package"),
        ("graphit.model.text_completion", "Text completion package"),
        ("graphit.model.text_completion.vertexai", "VertexAI package"),
    ]
    
    success_count = 0
    total_count = len(imports_to_check)
    
    for module_name, description in imports_to_check:
        if check_import(module_name, description):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"Import Check Results: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        print("✅ All imports successful! Tests should work.")
    else:
        print("❌ Some imports failed. Please install missing packages.")
        print("\nTo fix, run:")
        print("  ./install_packages.sh")
        print("or install packages manually:")
        print("  cd graphit-base && pip install -e . && cd ..")
        print("  cd graphit-vertexai && pip install -e . && cd ..")
        print("  cd graphit-flow && pip install -e . && cd ..")
    
    # Test the specific import used in the test
    print("\n" + "=" * 50)
    print("Testing specific import from test file...")
    try:
        from graphit.model.text_completion.vertexai.llm import Processor
        from graphit.schema import TextCompletionRequest, TextCompletionResponse, Error
        from graphit.base import LlmResult
        print("✅ Test imports successful!")
    except Exception as e:
        print(f"❌ Test imports failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
