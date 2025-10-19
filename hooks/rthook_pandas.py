"""
Runtime hook for pandas to ensure all submodules are importable
"""
import sys
import os

# Add pandas package to sys.modules to force recognition
try:
    import pandas
    # Force pandas.plotting to be in sys.modules
    if 'pandas.plotting' not in sys.modules:
        import pandas.plotting
        sys.modules['pandas.plotting'] = pandas.plotting
    if 'pandas.plotting._core' not in sys.modules:
        import pandas.plotting._core
        sys.modules['pandas.plotting._core'] = pandas.plotting._core
    if 'pandas.plotting._matplotlib' not in sys.modules:
        import pandas.plotting._matplotlib
        sys.modules['pandas.plotting._matplotlib'] = pandas.plotting._matplotlib
except Exception as e:
    print(f"pandas runtime hook warning: {e}")
