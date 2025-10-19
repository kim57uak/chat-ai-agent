"""
Runtime hook for matplotlib to ensure backends are importable
"""
import sys

try:
    import matplotlib
    if 'matplotlib.pyplot' not in sys.modules:
        import matplotlib.pyplot
        sys.modules['matplotlib.pyplot'] = matplotlib.pyplot
    if 'matplotlib.backends' not in sys.modules:
        import matplotlib.backends
        sys.modules['matplotlib.backends'] = matplotlib.backends
    if 'matplotlib.backends.backend_agg' not in sys.modules:
        import matplotlib.backends.backend_agg
        sys.modules['matplotlib.backends.backend_agg'] = matplotlib.backends.backend_agg
except Exception as e:
    print(f"matplotlib runtime hook warning: {e}")
