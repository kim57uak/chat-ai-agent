"""
Runtime hook for seaborn to ensure it's importable
"""
import sys

try:
    import seaborn
    if 'seaborn' not in sys.modules:
        sys.modules['seaborn'] = seaborn
except Exception as e:
    print(f"seaborn runtime hook warning: {e}")
