#!/usr/bin/env python3
"""
쓰레드 이슈 수정사항 테스트
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer

class TestWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
        print("Worker 취소 요청됨")
    
    def run(self):
        try:
            for i in range(10):
                if self._cancelled:
                    print("Worker 취소됨")
                    return
                
                self.progress.emit(f"작업 진행 중... {i+1}/10")
                time.sleep(0.5)  # 시뮬레이션
            
            if not self._cancelled:
                self.finished.emit("작업 완료!")
        except Exception as e:
            if not self._cancelled:
                self.error.emit(f"오류: {e}")

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('쓰레드 테스트')
        self.setGeometry(100, 100, 400, 300)
        
        # UI 설정
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        self.start_button = QPushButton('작업 시작')
        self.start_button.clicked.connect(self.start_work)
        layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton('작업 취소')
        self.cancel_button.clicked.connect(self.cancel_work)
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button)
        
        self.setCentralWidget(central_widget)
        
        # 쓰레드 관련 변수
        self.thread = None
        self.worker = None
    
    def start_work(self):
        if self.thread and self.thread.isRunning():
            self.append_text("이미 작업이 진행 중입니다.")
            return
        
        self.append_text("작업 시작...")
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # 새 쓰레드와 워커 생성
        self.thread = QThread()
        self.worker = TestWorker()
        self.worker.moveToThread(self.thread)
        
        # 시그널 연결
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        
        # 정리 시그널 연결
        self.worker.finished.connect(self._cleanup_thread)
        self.worker.error.connect(self._cleanup_thread)
        
        # 쓰레드 시작
        self.thread.start()
        
        # 타임아웃 설정 (10초)
        QTimer.singleShot(10000, self._check_timeout)
    
    def cancel_work(self):
        print("취소 요청 시작")
        
        if self.worker:
            self.worker.cancel()
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(2000):  # 2초 대기
                print("쓰레드 강제 종료")
                self.thread.terminate()
                self.thread.wait(1000)
        
        self._cleanup_thread()
        self.append_text("작업이 취소되었습니다.")
        print("취소 완료")
    
    def _cleanup_thread(self):
        """쓰레드 정리"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(2000):
                self.thread.terminate()
                self.thread.wait(1000)
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        if self.thread:
            self.thread.deleteLater()
            self.thread = None
        
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
    
    def _check_timeout(self):
        """타임아웃 체크"""
        if self.thread and self.thread.isRunning():
            self.append_text("작업 시간이 초과되었습니다.")
            self.cancel_work()
    
    def on_finished(self, message):
        self.append_text(f"완료: {message}")
    
    def on_error(self, message):
        self.append_text(f"오류: {message}")
    
    def on_progress(self, message):
        self.append_text(message)
    
    def append_text(self, text):
        self.text_display.append(text)
    
    def closeEvent(self, event):
        """윈도우 종료 시 쓰레드 정리"""
        print("윈도우 종료 시작")
        
        if self.worker:
            self.worker.cancel()
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(3000):
                self.thread.terminate()
                self.thread.wait(1000)
        
        print("윈도우 종료 완료")
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("테스트 애플리케이션 시작")
    print("- '작업 시작' 버튼을 클릭하여 쓰레드 작업 시작")
    print("- '작업 취소' 버튼을 클릭하여 작업 중단 테스트")
    print("- 윈도우를 닫아서 종료 처리 테스트")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()