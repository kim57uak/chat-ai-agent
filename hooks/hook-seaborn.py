from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# seaborn의 모든 서브모듈 수집
hiddenimports = collect_submodules('seaborn')

# seaborn 데이터 파일 수집
datas = collect_data_files('seaborn')
