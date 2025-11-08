"""
PyInstaller hook for lancedb
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('lancedb')

# Ensure all submodules are included
hiddenimports += collect_submodules('lancedb')
hiddenimports += ['lancedb.embeddings', 'lancedb.db', 'lancedb.table', 'lancedb.query']
