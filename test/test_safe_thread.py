#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
안전한 쓰레드 테스트 - 전역 관리 방식
"""

import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer

# 전역 쓰레드 관리
active_threads = []

class SafeWorker(QObject):
    finished = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        for i in range(5):
            if self._cancelled:
                return
            time.sleep(1)
        
        if not self._cancelled:
            self.finished.emit("작업 완료")

class SafeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('안전한 쓰레드 테스트')
        self.setGeometry(100, 100, 300, 200)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        self.start_button = QPushButton('시작')
        self.start_button.clicked.connect(self.start_work)
        layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton('취소')
        self.cancel_button.clicked.connect(self.cancel_work)
        layout.addWidget(self.cancel_button)
        
        self.setCentralWidget(central_widget)
        
        self.current_worker = None
    
    def start_work(self):
        self.text_display.append("작업 시작...")
        
        # 새 쓰레드 생성
        thread = QThread()
        worker = SafeWorker()
        worker.moveToThread(thread)
        
        # 전역 리스트에 추가하여 자동 삭제 방지
        active_threads.append((thread, worker))
        self.current_worker = worker
        
        # 시그널 연결
        thread.started.connect(worker.run)
        worker.finished.connect(self.on_finished)
        worker.finished.connect(lambda: self.cleanup_thread(thread, worker))
        
        thread.start()
    
    def cancel_work(self):
        self.text_display.append("취소 요청...")
        
        if self.current_worker:
            self.current_worker.cancel()
        
        self.text_display.append("취소 완료")
    
    def cleanup_thread(self, thread, worker):
        """쓰레드 정리"""
        try:
            # 전역 리스트에서 제거
            if (thread, worker) in active_threads:
                active_threads.remove((thread, worker))
            
            # 쓰레드 종료 대기
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
            
        except Exception as e:
            print(f"정리 오류: {e}")
    
    def on_finished(self, message):
        self.text_display.append(f"결과: {message}")
    
    def closeEvent(self, event):
        """모든 쓰레드 정리"""
        print("애플리케이션 종료 시작")
        
        # 모든 워커 취소
        for thread, worker in active_threads:
            try:
                worker.cancel()
            except:
                pass
        
        # 모든 쓰레드 종료 대기
        for thread, worker in active_threads[:]:  # 복사본으로 순회
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)
            except:
                pass
        
        # 전역 리스트 정리
        active_threads.clear()
        
        print("애플리케이션 종료 완료")
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SafeWindow()
    window.show()
    
    result = app.exec()
    
    # 애플리케이션 종료 시 남은 쓰레드 정리
    print("최종 정리 시작")
    for thread, worker in active_threads[:]:
        try:
            worker.cancel()
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
        except:
            pass
    active_threads.clear()
    print("최종 정리 완료")
    
    sys.exit(result)

if __name__ == '__main__':
    main()
