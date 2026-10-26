import sys
import os

def test_import(module_name):
    try:
        print(f"Testing {module_name}...")
        __import__(module_name)
        print(f"  OK: {module_name}")
        return True
    except Exception as e:
        print(f"  FAILED: {module_name} - {e}")
        return False

print("--- Dependency Diagnostic ---")
modules = ['os', 'sys', 'json', 'threading', 'psutil', 'numpy', 'PyQt6', 'sounddevice', 'scipy']
for m in modules:
    test_import(m)

print("\n--- Additional Info ---")
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print("--- End Diagnostic ---")
