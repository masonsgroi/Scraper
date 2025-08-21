#!/usr/bin/env python3
"""
Test script to verify the Docker environment is working correctly.
This script checks if all required dependencies are available and can be imported.
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing package imports...")
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas imported successfully")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        import tensorflow as tf
        print("✓ TensorFlow imported successfully")
        print(f"  TensorFlow version: {tf.__version__}")
    except ImportError as e:
        print(f"✗ TensorFlow import failed: {e}")
        return False
    
    try:
        import tf_keras as k3
        print("✓ TF-Keras imported successfully")
    except ImportError as e:
        print(f"✗ TF-Keras import failed: {e}")
        return False
    
    try:
        from sklearn.preprocessing import LabelEncoder
        print("✓ Scikit-learn imported successfully")
    except ImportError as e:
        print(f"✗ Scikit-learn import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow imported successfully")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    return True

def test_file_access():
    """Test if required files are accessible."""
    print("\nTesting file access...")
    
    files_to_check = [
        ('labels.csv', 'Dog breed labels file'),
        ('dog_pictures', 'Dog pictures directory'),
        ('model', 'Model directory')
    ]
    
    all_files_ok = True
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {description} found: {file_path}")
        else:
            print(f"✗ {description} not found: {file_path}")
            all_files_ok = False
    
    return all_files_ok

def test_environment():
    """Test environment variables and Python path."""
    print("\nTesting environment...")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Docker Environment Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test file access
    files_ok = test_file_access()
    
    # Test environment
    test_environment()
    
    print("\n" + "=" * 50)
    if imports_ok and files_ok:
        print("✓ All tests passed! Docker environment is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
