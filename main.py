import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.main_window import MainWindow

def signal_handler(signum, frame):
    """시그널 핸들러 - 안전한 종료"""
    print(f"시그널 {signum} 수신, 안전하게 종료합니다...")
    QApplication.quit()

if __name__ == '__main__':
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Ctrl+C 처리를 위한 타이머
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    
    window = MainWindow()
    window.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("키보드 인터럽트 감지, 종료합니다...")
        app.quit()