"""
Runtime hook for pandas to ensure all submodules are importable
"""
import sys

try:
    import pandas.plotting
    import pandas.plotting._core
    import pandas.plotting._matplotlib
    import pandas.plotting._misc
    
    sys.modules['pandas.plotting'] = pandas.plotting
    sys.modules['pandas.plotting._core'] = pandas.plotting._core
    sys.modules['pandas.plotting._matplotlib'] = pandas.plotting._matplotlib
    sys.modules['pandas.plotting._misc'] = pandas.plotting._misc
except Exception:
    pass
