"""
Code Executor
Python 및 JavaScript 코드 실행
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
import subprocess
import tempfile
import os
from core.logging import get_logger

# PyInstaller를 위한 명시적 import
try:
    import pandas.plotting  # noqa: F401
    import pandas._libs.tslibs.np_datetime  # noqa: F401
    import pandas._libs.tslibs.nattype  # noqa: F401
    import pandas._libs.skiplist  # noqa: F401
    import numpy.core._multiarray_umath  # noqa: F401
    import scipy  # noqa: F401
    import scipy.stats  # noqa: F401
    import matplotlib  # noqa: F401
    import matplotlib.pyplot  # noqa: F401
    import seaborn  # noqa: F401
except ImportError:
    pass

logger = get_logger("code_executor")


class CodeExecutionThread(QThread):
    """코드 실행 스레드"""
    
    finished = pyqtSignal(str, str)  # output, error
    
    def __init__(self, code, language):
        super().__init__()
        self.code = code
        self.language = language
    
    def run(self):
        """코드 실행"""
        try:
            if self.language == 'python':
                output, error = self._execute_python()
            elif self.language == 'javascript':
                output, error = self._execute_javascript()
            else:
                output = ""
                error = f"지원하지 않는 언어: {self.language}"
            
            self.finished.emit(output, error)
            
        except Exception as e:
            self.finished.emit("", f"실행 오류: {str(e)}")
    
    def _execute_python(self):
        """Python 코드 실행"""
        import sys
        from io import StringIO
        
        # input() 사용 감지
        if 'input(' in self.code:
            return "", "오류: input() 함수는 지원하지 않습니다. 대화형 입력이 필요한 코드는 실행할 수 없습니다."
        
        try:
            # 표준 출력 캐처
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            try:
                # 코드 실행
                exec(self.code, {'__name__': '__main__'})
                
                output = sys.stdout.getvalue()
                error = sys.stderr.getvalue()
                
                return output, error
                
            finally:
                # 표준 출력 복원
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            logger.error(f"Python 실행 오류: {e}")
            import traceback
            return "", traceback.format_exc()
    

    def _execute_javascript(self):
        """JavaScript 코드 실행"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(self.code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8'
                )
                return result.stdout, result.stderr
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return "", "실행 시간 초과 (10초)"
        except FileNotFoundError:
            return "", "Node.js가 설치되어 있지 않습니다."
        except Exception as e:
            return "", f"JavaScript 실행 오류: {str(e)}"


class CodeExecutor(QObject):
    """코드 실행 관리자"""
    
    execution_finished = pyqtSignal(str, str)  # output, error
    
    def __init__(self):
        super().__init__()
        self.thread = None
    
    def executeCode(self, code, language):
        """코드 실행"""
        if self.thread and self.thread.isRunning():
            logger.debug("이미 실행 중인 코드가 있습니다.")
            return
        
        self.thread = CodeExecutionThread(code, language)
        self.thread.finished.connect(self._on_finished)
        self.thread.start()
    
    def _on_finished(self, output, error):
        """실행 완료"""
        self.execution_finished.emit(output, error)
