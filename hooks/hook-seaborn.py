from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('seaborn')
hiddenimports += collect_submodules('seaborn.objects')
hiddenimports += collect_submodules('seaborn.external')

datas = collect_data_files('seaborn')
