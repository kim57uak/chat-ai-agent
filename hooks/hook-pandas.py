from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# pandas의 모든 서브모듈 수집
hiddenimports = collect_submodules('pandas')

# pandas.plotting 명시적 추가
hiddenimports += [
    'pandas.plotting',
    'pandas.plotting._core',
    'pandas.plotting._matplotlib',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.skiplist',
]

# pandas 데이터 파일 수집
datas = collect_data_files('pandas')
