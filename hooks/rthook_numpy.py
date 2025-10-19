"""
Runtime hook for numpy to ensure core modules are importable
"""
try:
    import numpy.core._multiarray_umath
    import numpy.random
    import numpy.linalg
    import numpy.fft
except ImportError as e:
    print(f"Warning: Failed to pre-import numpy modules: {e}")
