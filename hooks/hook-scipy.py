from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('scipy')
hiddenimports += collect_submodules('scipy.stats')
hiddenimports += collect_submodules('scipy.special')
hiddenimports += collect_submodules('scipy.linalg')
hiddenimports += collect_submodules('scipy.integrate')
hiddenimports += collect_submodules('scipy.optimize')
hiddenimports += collect_submodules('scipy.interpolate')
hiddenimports += collect_submodules('scipy.sparse')

datas = collect_data_files('scipy')
