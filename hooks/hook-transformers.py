"""
PyInstaller hook for transformers
Ensures all transformers submodules are included
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('transformers')

# Collect all submodules
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('transformers.models')
hiddenimports += collect_submodules('transformers.models.auto')
hiddenimports += collect_submodules('transformers.generation')

# Critical modules that must be explicitly included
hiddenimports += [
    'transformers.modeling_utils',
    'transformers.generation.utils',
    'transformers.generation.configuration_utils',
    'transformers.models.auto.modeling_auto',
    'transformers.models.auto.tokenization_auto',
    'transformers.models.auto.configuration_auto',
]
