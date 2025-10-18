from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# numpy의 모든 서브모듈 수집
hiddenimports = collect_submodules('numpy')

# numpy 핵심 모듈 명시적 추가
hiddenimports += [
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    'numpy.core._rational_tests',
    'numpy.core._struct_ufunc_tests',
    'numpy.random',
    'numpy.linalg',
    'numpy.fft',
]

# numpy 데이터 파일 수집
datas = collect_data_files('numpy')
