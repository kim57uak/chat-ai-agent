"""
PyInstaller hook for Pygments
Ensures all lexers and formatters are included
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules
hiddenimports = collect_submodules('pygments')
hiddenimports += collect_submodules('pygments.lexers')
hiddenimports += collect_submodules('pygments.formatters')
hiddenimports += collect_submodules('pygments.styles')
hiddenimports += collect_submodules('pygments.filters')

# Collect data files (lexer/formatter metadata)
datas = collect_data_files('pygments')
