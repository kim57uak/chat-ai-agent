"""
Runtime hook for scipy to ensure core modules are importable
"""
try:
    import scipy.stats
    import scipy.special
    import scipy.linalg
    import scipy.sparse
except ImportError as e:
    print(f"Warning: Failed to pre-import scipy modules: {e}")
