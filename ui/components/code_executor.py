"""
Code Executor
Python, JavaScript, Java 코드 실행
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
import subprocess
import tempfile
import os
from core.logging import get_logger

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
            # 언어 자동 감지
            detected_language = self._detect_language()
            
            if detected_language == 'java':
                output, error = self._execute_java()
            elif detected_language == 'javascript':
                output, error = self._execute_javascript()
            elif detected_language == 'python':
                output, error = self._execute_python()
            else:
                output = ""
                error = f"지원하지 않는 언어: {self.language}"
            
            self.finished.emit(output, error)
            
        except Exception as e:
            self.finished.emit("", f"실행 오류: {str(e)}")
    
    def _detect_language(self):
        """코드 내용으로 언어 감지"""
        code_lower = self.code.lower().strip()
        
        # Java 감지 (public class 또는 class 선언)
        if 'public class' in self.code or 'public static void main' in self.code:
            return 'java'
        
        # JavaScript 감지
        if any(keyword in code_lower for keyword in ['console.log', 'function(', '=>', 'const ', 'let ', 'var ']):
            return 'javascript'
        
        # 명시적 언어 지정이 있으면 우선
        if self.language:
            return self.language.lower()
        
        # 기본은 Python
        return 'python'
    
    def _execute_python(self):
        """Python 코드 실행"""
        if 'input(' in self.code:
            return "", "오류: input() 함수는 지원하지 않습니다. 대화형 입력이 필요한 코드는 실행할 수 없습니다."
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(self.code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding='utf-8',
                    env={**os.environ, 'MPLBACKEND': 'Agg'}
                )
                return result.stdout, result.stderr
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return "", "실행 시간 초과 (30초)"
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
    
    def _execute_java(self):
        """Java 코드 실행"""
        try:
            # 클래스명 추출
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', self.code)
            if not class_match:
                return "", "오류: public class를 찾을 수 없습니다."
            
            class_name = class_match.group(1)
            
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            java_file = os.path.join(temp_dir, f"{class_name}.java")
            
            try:
                # Java 파일 작성
                with open(java_file, 'w', encoding='utf-8') as f:
                    f.write(self.code)
                
                # 컴파일
                compile_result = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    cwd=temp_dir
                )
                
                if compile_result.returncode != 0:
                    return "", f"컴파일 오류:\n{compile_result.stderr}"
                
                # 실행
                run_result = subprocess.run(
                    ['java', class_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    cwd=temp_dir
                )
                
                return run_result.stdout, run_result.stderr
                
            finally:
                # 임시 파일 정리
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except subprocess.TimeoutExpired:
            return "", "실행 시간 초과 (10초)"
        except FileNotFoundError:
            return "", "Java가 설치되어 있지 않습니다. (javac, java 명령어 필요)"
        except Exception as e:
            return "", f"Java 실행 오류: {str(e)}"


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
