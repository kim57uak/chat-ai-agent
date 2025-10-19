"""
Runtime hook for numpy to ensure core modules are importable
"""
import sys

try:
    import numpy
    if 'numpy.core' not in sys.modules:
        import numpy.core
        sys.modules['numpy.core'] = numpy.core
    if 'numpy.random' not in sys.modules:
        import numpy.random
        sys.modules['numpy.random'] = numpy.random
    if 'numpy.linalg' not in sys.modules:
        import numpy.linalg
        sys.modules['numpy.linalg'] = numpy.linalg
    if 'numpy.fft' not in sys.modules:
        import numpy.fft
        sys.modules['numpy.fft'] = numpy.fft
except Exception as e:
    print(f"numpy runtime hook warning: {e}")
