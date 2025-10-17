# AI 코드 실행 기능 설계 문서

## 📋 목차
1. [개요](#개요)
2. [핵심 기능](#핵심-기능)
3. [기술 스택](#기술-스택)
4. [시스템 아키텍처](#시스템-아키텍처)
5. [시퀀스 다이어그램](#시퀀스-다이어그램)
6. [구현 상세](#구현-상세)
7. [보안 고려사항](#보안-고려사항)
8. [배포 전략](#배포-전략)

---

## 개요

### 목적
사용자가 AI와 대화하며 데이터 분석을 수행할 수 있도록, AI가 생성한 Python 코드를 앱 내부에서 직접 실행하는 기능을 제공합니다.

### 핵심 가치
- **Zero Installation**: Python 및 라이브러리 별도 설치 불필요
- **Dynamic Analysis**: AI가 실행 결과를 보고 다음 분석 전략 결정
- **Exploratory Data Analysis**: 탐색적 데이터 분석 자동화
- **Report Generation**: 분석 결과를 보고서로 자동 생성

---

## 핵심 기능

### 1. 코드 생성 및 실행
- AI가 데이터 분석용 Python 코드 생성
- UI에 [▶ 실행] 버튼 자동 표시
- 사용자 클릭 시 앱 내부에서 코드 실행
- 실행 결과를 채팅에 표시

### 2. 반복적 분석
- 실행 결과를 AI에게 자동 전달
- AI가 결과를 분석하고 다음 코드 생성
- 사용자 개입 없이 연속적 분석 가능

### 3. 파일 처리
- workspace 디렉토리에서 파일 읽기/쓰기
- CSV, Excel, JSON 등 다양한 형식 지원
- 분석 결과를 파일로 저장

### 4. 보고서 생성
- 분석 과정을 마크다운 보고서로 작성
- PDF, HTML, Markdown 형식 지원
- 차트 및 통계 자동 포함

---

## 기술 스택

### 프론트엔드
- **PyQt6**: 데스크톱 UI 프레임워크
- **QWebEngineView**: 마크다운 렌더링 및 코드 하이라이팅
- **JavaScript Bridge**: Python-JavaScript 통신

### 백엔드
- **LangChain**: AI 에이전트 프레임워크
- **exec()**: Python 코드 동적 실행
- **ConversationManager**: 대화 히스토리 관리

### 데이터 분석
- **pandas**: 데이터 처리 및 분석
- **numpy**: 수치 계산
- **matplotlib**: 데이터 시각화
- **seaborn**: 고급 시각화
- **scikit-learn**: 머신러닝

### 패키징
- **PyInstaller**: 실행 파일 생성
- **모든 라이브러리 번들링**: 사용자 설치 불필요

---

## 시스템 아키텍처

### 컴포넌트 구조

```
┌─────────────────────────────────────────────────────────┐
│                     Chat UI (PyQt6)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  QWebEngineView (마크다운 렌더링)                │   │
│  │  - 코드 블록 표시                                │   │
│  │  - [▶ 실행] 버튼                                 │   │
│  │  - 실행 결과 표시                                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              AI Agent (LangChain)                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 사용자 요청 분석                              │   │
│  │  - Python 코드 생성                              │   │
│  │  - 실행 결과 해석                                │   │
│  │  - 다음 분석 전략 결정                           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│            Code Executor (exec 기반)                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 작업 디렉토리 설정 (workspace)                │   │
│  │  - stdout/stderr 캡처                            │   │
│  │  - exec() 실행                                   │   │
│  │  - 결과 반환                                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│         Bundled Python Environment                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Python 3.11 + 데이터 분석 라이브러리            │   │
│  │  - pandas, numpy, matplotlib                     │   │
│  │  - seaborn, scikit-learn, scipy                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              Workspace Directory                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 사용자 데이터 파일 (CSV, Excel, etc.)         │   │
│  │  - 분석 결과 파일                                │   │
│  │  - 생성된 차트 이미지                            │   │
│  │  - 보고서 (MD, PDF, HTML)                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 시퀀스 다이어그램

### 전체 워크플로우

```
사용자                Chat UI              AI Agent           Code Executor      File System        Conversation Manager
  │                     │                      │                      │                   │                      │
  │─"data.csv 분석"────>│                      │                      │                   │                      │
  │                     │──메시지 추가(user)──>│                      │                   │                      │
  │                     │──분석 요청──────────>│                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │                     │                      │──코드 생성           │                   │                      │
  │                     │<─코드+[실행]버튼─────│                      │                   │                      │
  │<──코드 표시─────────│                      │                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │─[▶ 실행] 클릭──────>│                      │                      │                   │                      │
  │                     │──execute_code()─────────────────────────>│                   │                      │
  │                     │                      │                      │                   │                      │
  │                     │                      │                      │─workspace 이동    │                      │
  │                     │                      │                      │─stdout 캡처       │                      │
  │                     │                      │                      │─exec(code)        │                      │
  │                     │                      │                      │─pd.read_csv()────>│                      │
  │                     │                      │                      │<─DataFrame────────│                      │
  │                     │                      │                      │─print(df.info())  │                      │
  │                     │                      │                      │─stdout 종료       │                      │
  │                     │                      │                      │                   │                      │
  │                     │<─실행 결과───────────────────────────────│                   │                      │
  │<──결과 표시─────────│                      │                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │                     │──메시지 추가("[실행 결과]...")─────────────────────────────────────────────────────>│
  │                     │──결과 전달──────────>│                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │                     │                      │──결과 분석           │                   │                      │
  │                     │                      │──다음 코드 생성      │                   │                      │
  │                     │<─코드+[실행]버튼─────│                      │                   │                      │
  │<──코드 표시─────────│                      │                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │                     │        (반복 계속...)                       │                   │                      │
  │                     │                      │                      │                   │                      │
  │─"보고서 작성"──────>│                      │                      │                   │                      │
  │                     │──보고서 요청────────>│                      │                   │                      │
  │                     │                      │──보고서 생성         │                   │                      │
  │                     │<─보고서+[저장]버튼───│                      │                   │                      │
  │<──보고서 표시───────│                      │                      │                   │                      │
  │                     │                      │                      │                   │                      │
  │─[💾 저장] 클릭─────>│                      │                      │                   │                      │
  │                     │──report.md 저장─────────────────────────────────────────────>│                      │
  │                     │<─저장 완료───────────────────────────────────────────────────│                      │
  │<──"저장 완료"───────│                      │                      │                   │                      │
```

### 코드 실행 상세 플로우

```
Chat UI          Code Executor       Python Runtime      Data Libraries      Workspace Files
  │                    │                     │                    │                   │
  │─execute_code()────>│                     │                    │                   │
  │                    │                     │                    │                   │
  │                    │─os.chdir(workspace) │                    │                   │
  │                    │─sys.stdout=StringIO │                    │                   │
  │                    │─sys.stderr=StringIO │                    │                   │
  │                    │                     │                    │                   │
  │                    │─exec(code)─────────>│                    │                   │
  │                    │                     │                    │                   │
  │                    │                     │─import pandas─────>│                   │
  │                    │                     │─pd.read_csv()─────>│                   │
  │                    │                     │                    │─파일 읽기────────>│
  │                    │                     │                    │<─파일 데이터──────│
  │                    │                     │<─DataFrame─────────│                   │
  │                    │                     │                    │                   │
  │                    │                     │─df.describe()─────>│                   │
  │                    │                     │                    │─통계 계산         │
  │                    │                     │<─통계 결과─────────│                   │
  │                    │                     │─print(결과)        │                   │
  │                    │                     │                    │                   │
  │                    │                     │─import matplotlib──>│                   │
  │                    │                     │─plt.plot()────────>│                   │
  │                    │                     │                    │─차트 생성         │
  │                    │                     │─plt.savefig()─────>│                   │
  │                    │                     │                    │─이미지 저장──────>│
  │                    │                     │                    │                   │
  │                    │─output=stdout.get() │                    │                   │
  │                    │─error=stderr.get()  │                    │                   │
  │                    │─stdout 복원         │                    │                   │
  │                    │─stderr 복원         │                    │                   │
  │                    │                     │                    │                   │
  │<─{success, output}─│                     │                    │                   │
```

---

## 구현 상세

### 1. Code Executor 구현

**파일**: `ui/components/code_executor.py`

**핵심 기능**:
- `exec()` 기반 코드 실행
- stdout/stderr 캡처
- 작업 디렉토리 관리
- 타임아웃 처리
- 에러 핸들링

**주요 메서드**:
```python
class CodeExecutor:
    def execute_python(code: str, workspace_path: str, timeout: int = 30)
    def _capture_output()
    def _restore_output()
    def _limit_output(output: str, max_length: int = 2000)
```

### 2. UI 통합

**파일**: `ui/components/chat_display.py` (수정)

**추가 기능**:
- 코드 블록 감지
- [▶ 실행] 버튼 자동 생성
- JavaScript Bridge 연결
- 실행 결과 표시

**JavaScript 함수**:
```javascript
function executeCode(codeElement) {
    const code = codeElement.textContent;
    window.pybridge.executeCode(code);
}
```

### 3. AI 프롬프트 수정

**파일**: `ui/prompts.py` (수정)

**추가 규칙**:
```
When analyzing data files:
- Generate Python code for analysis
- Use summary methods (head, info, describe) not full data
- Print only essential information
- Limit output to avoid token overflow
- Use pandas for tabular data
- Use matplotlib for visualization
```

### 4. Conversation Manager 통합

**파일**: `core/client/conversation_manager.py` (수정)

**추가 기능**:
- 실행 결과를 자동으로 대화 히스토리에 추가
- 토큰 최적화 (긴 출력 요약)

### 5. Workspace 관리

**파일**: `core/workspace_manager.py` (신규)

**기능**:
- workspace 디렉토리 생성/관리
- 파일 업로드 처리
- 파일 목록 조회
- 보안 검증 (경로 탐색 방지)

---

## 보안 고려사항

### 1. exec() 보안

**위험**:
- 임의 코드 실행 가능
- 시스템 파일 접근 가능
- 무한 루프 가능

**대책**:
- workspace 디렉토리로 제한
- 타임아웃 설정 (30초)
- 위험한 모듈 import 제한 (os.system, subprocess 등)
- 사용자 확인 후 실행

### 2. 파일 시스템 보안

**제한**:
- workspace 디렉토리 외부 접근 금지
- 경로 탐색 공격 방지 (`../` 차단)
- 파일 크기 제한 (100MB)
- 허용된 확장자만 처리

### 3. 리소스 제한

**제한**:
- 실행 시간: 30초
- 메모리: 시스템 메모리의 50%
- 출력 크기: 2000자 (자동 요약)

---

## 배포 전략

### 1. PyInstaller 설정

**파일**: `chat_ai_agent.spec` (수정 완료)

**포함 라이브러리**:
- numpy, pandas
- matplotlib, seaborn
- scikit-learn, scipy

**번들 크기**: 약 200-300MB

### 2. 플랫폼별 배포

**macOS**:
- `.app` 번들
- 코드 서명 필요
- Gatekeeper 우회 안내

**Windows**:
- `.exe` 실행 파일
- Windows Defender 예외 처리 안내

**Linux**:
- AppImage 또는 실행 파일
- 실행 권한 부여 필요

### 3. 사용자 가이드

**첫 실행**:
1. 앱 다운로드 및 설치
2. workspace 디렉토리 설정
3. 데이터 파일 업로드
4. AI에게 분석 요청

**예시 시나리오**:
```
사용자: "workspace/sales.csv 파일을 분석해줘"
AI: [코드 생성]
사용자: [실행] 클릭
AI: [결과 분석 및 다음 코드 생성]
...
사용자: "보고서 작성해줘"
AI: [보고서 생성]
사용자: [저장] 클릭
```

---

## 구현 파일 목록

### 신규 생성 파일

#### 1. `core/workspace_manager.py`
**목적**: workspace 디렉토리 관리 및 파일 보안

**주요 기능**:
- workspace 디렉토리 생성 및 초기화
- 파일 업로드 처리
- 파일 목록 조회
- 경로 보안 검증 (경로 탐색 공격 방지)
- 파일 크기 및 확장자 검증

**주요 메서드**:
```python
class WorkspaceManager:
    def __init__(workspace_path: str)
    def create_workspace() -> bool
    def upload_file(file_path: str) -> bool
    def list_files() -> List[str]
    def validate_path(file_path: str) -> bool
    def get_file_info(file_path: str) -> Dict
```

#### 2. `ui/components/code_execution_widget.py`
**목적**: 코드 실행 UI 컴포넌트

**주요 기능**:
- 코드 블록에 실행 버튼 추가
- 실행 결과 표시
- 로딩 상태 표시
- 에러 메시지 표시

**주요 메서드**:
```python
class CodeExecutionWidget(QWidget):
    def add_execute_button(code_element)
    def show_loading()
    def show_result(output: str, error: str)
    def show_error(error: str)
```

#### 3. `ui/dialogs/workspace_dialog.py`
**목적**: workspace 설정 및 파일 관리 다이얼로그

**주요 기능**:
- workspace 경로 설정
- 파일 업로드 (드래그 앤 드롭)
- 파일 목록 표시
- 파일 삭제

**주요 메서드**:
```python
class WorkspaceDialog(QDialog):
    def select_workspace_path()
    def upload_files()
    def refresh_file_list()
    def delete_file(file_path: str)
```

---

### 수정할 기존 파일

#### 1. `ui/components/code_executor.py` (기존 파일 수정)
**수정 내용**:
- subprocess 방식 제거
- exec() 기반 실행으로 변경
- workspace 경로 지원 추가
- stdout/stderr 캡처 개선
- 출력 크기 제한 추가

**수정 메서드**:
```python
class CodeExecutor:
    # 기존: subprocess 사용
    # 신규: exec() 사용
    def execute_python(code: str, workspace_path: str, timeout: int = 30)
    def _capture_output()  # 신규
    def _restore_output()  # 신규
    def _limit_output(output: str, max_length: int = 2000)  # 신규
```

#### 2. `ui/components/chat_display.py` (또는 해당 웹뷰 컴포넌트)
**수정 내용**:
- 코드 블록 감지 로직 추가
- [▶ 실행] 버튼 자동 생성
- JavaScript Bridge 연결
- 실행 결과 표시 영역 추가

**추가 메서드**:
```python
def inject_execute_buttons()  # 신규
def handle_code_execution(code: str)  # 신규
def display_execution_result(result: Dict)  # 신규
```

**추가 JavaScript**:
```javascript
function executeCode(button) {
    const code = button.previousElementSibling.querySelector('code').textContent;
    window.pybridge.executeCode(code);
}
```

#### 3. `core/client/conversation_manager.py`
**수정 내용**:
- 실행 결과를 자동으로 대화 히스토리에 추가하는 메서드
- 출력 크기 제한 및 요약

**추가 메서드**:
```python
def add_execution_result(output: str, error: str)  # 신규
def summarize_output(output: str, max_length: int = 2000)  # 신규
```

#### 4. `ui/prompts.py` (또는 `prompt_config.json`)
**수정 내용**:
- 데이터 분석 코드 생성 규칙 추가
- 출력 제한 규칙 추가

**추가 프롬프트**:
```json
{
  "code_execution": {
    "rules": [
      "When analyzing data files, generate Python code",
      "Use summary methods (head, info, describe) not full data",
      "Print only essential information to avoid token overflow",
      "Use pandas for tabular data analysis",
      "Use matplotlib for visualization, save to files"
    ]
  }
}
```

#### 5. `core/ai_agent_v2.py`
**수정 내용**:
- 코드 실행 결과를 처리하는 로직 추가
- 실행 결과를 다음 메시지로 자동 전달

**추가 메서드**:
```python
def process_execution_result(result: Dict) -> str  # 신규
def auto_continue_analysis(result: Dict)  # 신규
```

#### 6. `ui/main_window/main_window.py`
**수정 내용**:
- workspace 메뉴 추가
- workspace 설정 다이얼로그 연결

**추가 메서드**:
```python
def open_workspace_dialog()  # 신규
def set_workspace_path(path: str)  # 신규
```

#### 7. `config.json`
**수정 내용**:
- workspace 설정 추가
- 코드 실행 설정 추가

**추가 설정**:
```json
{
  "workspace": {
    "path": "~/ChatAIAgent/workspace",
    "max_file_size_mb": 100,
    "allowed_extensions": [".csv", ".xlsx", ".json", ".txt", ".pdf"]
  },
  "code_execution": {
    "timeout": 30,
    "max_output_length": 2000,
    "enable_auto_continue": true
  }
}
```

---

## 파일 구조 요약

```
chat-ai-agent/
├── core/
│   ├── workspace_manager.py          # 신규 생성
│   ├── ai_agent_v2.py                # 수정
│   └── client/
│       └── conversation_manager.py   # 수정
├── ui/
│   ├── components/
│   │   ├── code_executor.py          # 수정 (exec 기반으로 변경)
│   │   ├── code_execution_widget.py  # 신규 생성
│   │   └── chat_display.py           # 수정
│   ├── dialogs/
│   │   └── workspace_dialog.py       # 신규 생성
│   ├── main_window/
│   │   └── main_window.py            # 수정
│   └── prompts.py                    # 수정
├── config.json                        # 수정
├── requirements.txt                   # 수정 완료
└── chat_ai_agent.spec                # 수정 완료
```

---

## 향후 개선 사항

### 1. 고급 기능
- 차트 인터랙티브 표시
- 실행 히스토리 관리
- 코드 편집 기능
- 변수 상태 확인

### 2. 성능 최적화
- 코드 캐싱
- 병렬 실행
- 메모리 최적화

### 3. 사용성 개선
- 코드 템플릿 제공
- 자동 완성
- 에러 해결 제안
- 튜토리얼 모드

---

## 결론

이 설계는 사용자가 별도의 Python 설치 없이 AI와 대화하며 데이터 분석을 수행할 수 있는 완전한 솔루션을 제공합니다. exec() 기반 실행과 PyInstaller 번들링을 통해 Zero Installation 경험을 실현하며, LangChain과의 통합으로 지능적인 탐색적 데이터 분석을 가능하게 합니다.
