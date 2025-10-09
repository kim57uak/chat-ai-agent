"""
PyInstaller hook for loguru
Automatically includes loguru and its dependencies
"""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('loguru')
