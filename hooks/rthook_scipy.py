"""
Runtime hook for scipy to ensure core modules are importable
"""
import sys

try:
    import scipy
    if 'scipy.stats' not in sys.modules:
        import scipy.stats
        sys.modules['scipy.stats'] = scipy.stats
    if 'scipy.special' not in sys.modules:
        import scipy.special
        sys.modules['scipy.special'] = scipy.special
    if 'scipy.linalg' not in sys.modules:
        import scipy.linalg
        sys.modules['scipy.linalg'] = scipy.linalg
    if 'scipy.sparse' not in sys.modules:
        import scipy.sparse
        sys.modules['scipy.sparse'] = scipy.sparse
except Exception as e:
    print(f"scipy runtime hook warning: {e}")
