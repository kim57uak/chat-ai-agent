from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# keyring의 모든 서브모듈 수집
hiddenimports = collect_submodules('keyring')

# keyring 데이터 파일 수집
datas = collect_data_files('keyring', include_py_files=True)
