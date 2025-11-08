"""
PyInstaller hook for sentence-transformers
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('sentence_transformers')

# Ensure all submodules are included
hiddenimports += collect_submodules('sentence_transformers')
hiddenimports += [
    'sentence_transformers.models',
    'sentence_transformers.util',
    'sentence_transformers.evaluation',
    'sentence_transformers.losses',
]
