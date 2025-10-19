"""
Runtime hook for pandas to ensure all submodules are importable
"""
import sys

print("[RTHOOK] pandas runtime hook 실행 시작")
try:
    import pandas.plotting
    import pandas.plotting._core
    import pandas.plotting._matplotlib
    import pandas.plotting._misc
    
    sys.modules['pandas.plotting'] = pandas.plotting
    sys.modules['pandas.plotting._core'] = pandas.plotting._core
    sys.modules['pandas.plotting._matplotlib'] = pandas.plotting._matplotlib
    sys.modules['pandas.plotting._misc'] = pandas.plotting._misc
    print("[RTHOOK] pandas.plotting 모듈 등록 완료")
except Exception as e:
    print(f"[RTHOOK] pandas runtime hook 실패: {e}")
