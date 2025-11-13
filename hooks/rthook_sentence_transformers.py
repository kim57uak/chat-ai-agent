"""
Runtime hook for sentence_transformers
Ensures sentence_transformers can be imported in packaged app
"""

import sys
import os
from pathlib import Path

# Add sentence_transformers to path
if getattr(sys, 'frozen', False):
    # Running in packaged app
    if sys.platform == 'darwin':
        base_path = Path(sys.executable).parent.parent / 'Resources'
    else:
        base_path = Path(sys.executable).parent
    
    # Ensure sentence_transformers is in path
    st_path = base_path / 'sentence_transformers'
    if st_path.exists() and str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
        print(f"[RTHOOK] Added to path: {base_path}")
