from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# scipy의 모든 서브모듈 수집
hiddenimports = collect_submodules('scipy')

# scipy 핵심 모듈 명시적 추가
hiddenimports += [
    'scipy.stats',
    'scipy.special',
    'scipy.linalg',
    'scipy.integrate',
    'scipy.optimize',
    'scipy.interpolate',
    'scipy.sparse',
]

# scipy 데이터 파일 수집
datas = collect_data_files('scipy')
