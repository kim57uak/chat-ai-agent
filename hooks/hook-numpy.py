from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('numpy')
hiddenimports += collect_submodules('numpy.core')
hiddenimports += collect_submodules('numpy.random')
hiddenimports += collect_submodules('numpy.linalg')
hiddenimports += collect_submodules('numpy.fft')

datas = collect_data_files('numpy')
