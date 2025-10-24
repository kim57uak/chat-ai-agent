"""
Runtime hook for astropy to ensure core modules are importable
"""
import sys

try:
    import astropy.units
    import astropy.coordinates
    import astropy.time
    import astropy.constants
    
    sys.modules['astropy.units'] = astropy.units
    sys.modules['astropy.coordinates'] = astropy.coordinates
    sys.modules['astropy.time'] = astropy.time
    sys.modules['astropy.constants'] = astropy.constants
except Exception:
    pass
