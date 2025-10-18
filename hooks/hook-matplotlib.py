from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# matplotlib의 모든 서브모듈 수집
hiddenimports = collect_submodules('matplotlib')

# matplotlib 핵심 모듈 명시적 추가
hiddenimports += [
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_agg',
    'matplotlib.backends.backend_pdf',
    'matplotlib.figure',
]

# matplotlib 데이터 파일 수집
datas = collect_data_files('matplotlib')
