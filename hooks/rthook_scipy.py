"""
Runtime hook for scipy to ensure core modules are importable
"""
import sys

try:
    import scipy.stats
    import scipy.special
    import scipy.linalg
    import scipy.sparse
    
    sys.modules['scipy.stats'] = scipy.stats
    sys.modules['scipy.special'] = scipy.special
    sys.modules['scipy.linalg'] = scipy.linalg
    sys.modules['scipy.sparse'] = scipy.sparse
except Exception:
    pass
