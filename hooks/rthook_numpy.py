"""
Runtime hook for numpy to ensure core modules are importable
"""
import sys

try:
    import numpy.core
    import numpy.random
    import numpy.linalg
    import numpy.fft
    
    sys.modules['numpy.core'] = numpy.core
    sys.modules['numpy.random'] = numpy.random
    sys.modules['numpy.linalg'] = numpy.linalg
    sys.modules['numpy.fft'] = numpy.fft
except Exception:
    pass
