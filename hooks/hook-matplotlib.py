from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('matplotlib')
hiddenimports += collect_submodules('matplotlib.backends')
hiddenimports += collect_submodules('matplotlib.pyplot')

datas = collect_data_files('matplotlib')
