"""
Runtime hook for sentence_transformers
Ensures sentence_transformers and transformers can be imported in packaged app
"""

import sys
import os
from pathlib import Path

# Add sentence_transformers and dependencies to path
if getattr(sys, 'frozen', False):
    # Running in packaged app
    if sys.platform == 'darwin':
        base_path = Path(sys.executable).parent.parent / 'Resources'
    else:
        base_path = Path(sys.executable).parent
    
    # Add base path first
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
        print(f"[RTHOOK] Added base path: {base_path}")
    
    # Pre-import critical transformers modules to avoid lazy import issues
    try:
        import transformers
        import transformers.models
        import transformers.models.auto
        import transformers.models.auto.modeling_auto
        import transformers.models.auto.tokenization_auto
        import transformers.models.auto.configuration_auto
        print("[RTHOOK] Pre-imported transformers modules")
    except Exception as e:
        print(f"[RTHOOK] Warning: Could not pre-import transformers: {e}")
    
    # Pre-import torch
    try:
        import torch
        import torch.nn
        print("[RTHOOK] Pre-imported torch modules")
    except Exception as e:
        print(f"[RTHOOK] Warning: Could not pre-import torch: {e}")
