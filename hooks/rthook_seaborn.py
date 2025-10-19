"""
Runtime hook for seaborn to ensure it's importable
"""
try:
    import seaborn
except ImportError as e:
    print(f"Warning: Failed to pre-import seaborn: {e}")
