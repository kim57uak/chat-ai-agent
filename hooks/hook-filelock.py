# PyInstaller hook for filelock
from PyInstaller.utils.hooks import collect_all

# Collect all filelock components
datas, binaries, hiddenimports = collect_all('filelock')

# Ensure the main module is included
hiddenimports += [
    'filelock',
    'filelock._api',
    'filelock._error',
    'filelock._soft',
    'filelock._unix',
    'filelock._windows',
]