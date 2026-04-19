print("Testing Python environment...")
try:
    import sys
    print(f"Python version: {sys.version}")
    print("Environment test successful!")
except Exception as e:
    print(f"Error: {e}")