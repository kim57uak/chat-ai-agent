"""
Runtime hook for pandas to ensure all submodules are importable
"""
import sys

try:
    import pandas
    import pandas.plotting
    import pandas.plotting._core
    import pandas.plotting._matplotlib
    import pandas.plotting._misc
    import pandas._libs
    import pandas._libs.tslibs
    import pandas.core
except ImportError:
    pass
