"""Code execution handler for Python and JavaScript"""

import subprocess
import tempfile
import os
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QThread


class CodeExecutor(QObject):
    """코드 실행을 처리하는 클래스"""
    
    execution_finished = pyqtSignal(str, str)  # (output, error)
    
    def __init__(self):
        super().__init__()
    
    @pyqtSlot(str, str)
    def executeCode(self, code, language):
        """코드 실행"""
        try:
            if language == 'python':
                output, error = self._execute_python(code)
            elif language == 'javascript':
                output, error = self._execute_javascript(code)
            else:
                error = f"지원하지 않는 언어: {language}"
                output = ""
            
            self.execution_finished.emit(output, error)
            
        except Exception as e:
            self.execution_finished.emit("", f"실행 오류: {str(e)}")
    
    def _execute_python(self, code):
        """Python 코드 실행"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8'
                )
                
                output = result.stdout
                error = result.stderr
                
                return output, error
                
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except subprocess.TimeoutExpired:
            return "", "실행 시간 초과 (10초)"
        except Exception as e:
            return "", f"Python 실행 오류: {str(e)}"
    
    def _execute_javascript(self, code):
        """JavaScript 코드 실행"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8'
                )
                
                output = result.stdout
                error = result.stderr
                
                return output, error
                
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except FileNotFoundError:
            return "", "Node.js가 설치되어 있지 않습니다."
        except subprocess.TimeoutExpired:
            return "", "실행 시간 초과 (10초)"
        except Exception as e:
            return "", f"JavaScript 실행 오류: {str(e)}"
