"""
Runtime hook for matplotlib to ensure backends are importable
"""
try:
    import matplotlib.pyplot
    import matplotlib.backends.backend_agg
    import matplotlib.figure
except ImportError as e:
    print(f"Warning: Failed to pre-import matplotlib modules: {e}")
