# Runtime hook for filelock
import sys
import os

# Ensure filelock can be imported at runtime
try:
    import filelock
    print(f"✓ filelock loaded: {filelock.__file__}")
except ImportError as e:
    print(f"✗ filelock import failed: {e}")
    # Try to add the path manually
    if hasattr(sys, '_MEIPASS'):
        filelock_path = os.path.join(sys._MEIPASS, 'filelock')
        if os.path.exists(filelock_path):
            sys.path.insert(0, filelock_path)
            try:
                import filelock
                print(f"✓ filelock loaded from MEIPASS: {filelock.__file__}")
            except ImportError as e2:
                print(f"✗ filelock still failed: {e2}")