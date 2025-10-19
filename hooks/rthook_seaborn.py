"""
Runtime hook for seaborn to ensure it's importable
"""
import sys

try:
    import seaborn
    sys.modules['seaborn'] = seaborn
except Exception:
    pass
