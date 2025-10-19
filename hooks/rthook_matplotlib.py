"""
Runtime hook for matplotlib to ensure backends are importable
"""
import sys

try:
    import matplotlib.pyplot
    import matplotlib.backends
    import matplotlib.backends.backend_agg
    
    sys.modules['matplotlib.pyplot'] = matplotlib.pyplot
    sys.modules['matplotlib.backends'] = matplotlib.backends
    sys.modules['matplotlib.backends.backend_agg'] = matplotlib.backends.backend_agg
except Exception:
    pass
