#!/usr/bin/env python3
"""
간단한 쓰레드 테스트 - 크래시 방지 확인
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer

class SimpleWorker(QObject):
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

class SimpleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('간단한 쓰레드 테스트')
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
        
        self.thread = None
        self.worker = None
    
    def start_work(self):
        self.text_display.append("작업 시작...")
        
        self.thread = QThread()
        self.worker = SimpleWorker()
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.cleanup)
        
        self.thread.start()
    
    def cancel_work(self):
        self.text_display.append("취소 요청...")
        
        if self.worker:
            self.worker.cancel()
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            # wait 호출 제거
        
        # 참조만 제거
        self.worker = None
        self.thread = None
        self.text_display.append("취소 완료")
    
    def cleanup(self):
        """안전한 정리"""
        self.worker = None
        self.thread = None
    
    def on_finished(self, message):
        self.text_display.append(f"결과: {message}")
    
    def closeEvent(self, event):
        if self.worker:
            self.worker.cancel()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            # wait 호출 제거
        # 참조만 제거
        self.worker = None
        self.thread = None
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()