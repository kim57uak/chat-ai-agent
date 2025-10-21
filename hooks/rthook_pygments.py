"""
Runtime hook for Pygments
Ensures Pygments is properly initialized in packaged environment
"""
import sys
import os

# Verify Pygments is available
try:
    import pygments
    import pygments.lexers
    print(f"[RTHOOK] Pygments {pygments.__version__} loaded successfully")
    print(f"[RTHOOK] Pygments path: {pygments.__file__}")
except ImportError as e:
    print(f"[RTHOOK] WARNING: Pygments import failed: {e}")
    sys.exit(1)

# Pre-import commonly used lexers for faster access
try:
    from pygments.lexers import PythonLexer, JavascriptLexer, BashLexer
    from pygments.lexers import get_lexer_by_name, guess_lexer
    print("[RTHOOK] Pygments lexers pre-loaded")
except Exception as e:
    print(f"[RTHOOK] WARNING: Lexer pre-load failed: {e}")
