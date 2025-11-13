# 데이터 분석 에이전트 강화 기획

## 📊 현재 구조 분석

### 기존 에이전트
1. **PandasAgent**: CSV/Excel 기본 분석
2. **PythonREPLAgent**: 코드 실행
3. **SQLAgent**: DB 쿼리
4. **FileSystemAgent**: 파일 읽기
5. **MCPAgent**: 외부 도구
6. **RAGAgent**: 문서 검색

### 현재 한계
- ✅ 단순 통계 계산 가능
- ❌ 복잡한 다단계 분석 부족
- ❌ 시각화 자동 생성 없음
- ❌ 보고서 작성 기능 없음
- ❌ 데이터 전처리 자동화 부족

---

## 🎯 개선 목표

### 1단계: 데이터 분석 파이프라인
```
데이터 로드 → 전처리 → 탐색적 분석 → 시각화 → 인사이트 추출 → 보고서 생성
```

### 2단계: 전문 에이전트 추가
- **DataCleaningAgent**: 결측치, 이상치 처리
- **StatisticalAgent**: 고급 통계 분석
- **VisualizationAgent**: 차트/그래프 생성
- **ReportAgent**: 자동 보고서 작성

### 3단계: 멀티 에이전트 협업
- **AnalysisOrchestrator**: 분석 워크플로우 조율
- **InsightExtractor**: AI 기반 인사이트 도출

---

## 🏗️ 새로운 아키텍처

### Agent 계층 구조
```
MultiAgentOrchestrator
├── DataAnalysisOrchestrator (신규)
│   ├── DataCleaningAgent (신규)
│   ├── StatisticalAgent (신규)
│   ├── VisualizationAgent (신규)
│   └── ReportAgent (신규)
├── PandasAgent (강화)
├── PythonREPLAgent
└── SQLAgent
```

---

## 💡 신규 에이전트 상세 설계

### 1. DataCleaningAgent
**역할**: 데이터 전처리 자동화

#### 1.1 결측치(Missing Values) 처리

**탐지 방법**:
- `pandas.isnull()`, `pandas.isna()`
- 결측치 비율 계산
- 패턴 분석 (MCAR, MAR, MNAR)

**처리 전략**:
```python
# 1. 삭제 (Deletion)
- 행 삭제: 결측치 비율 < 5%
- 열 삭제: 결측치 비율 > 50%

# 2. 대체 (Imputation)
- 평균값: 정규분포 수치형 데이터
- 중앙값: 이상치 있는 수치형 데이터
- 최빈값: 범주형 데이터
- 전방/후방 채우기: 시계열 데이터
- KNN Imputation: 다변량 관계 고려

# 3. 예측 (Prediction)
- 회귀 모델로 결측치 예측
- 다중 대체 (Multiple Imputation)

# 4. 표시 (Flagging)
- 결측 여부를 별도 컬럼으로 추가
- 특수값 사용 (예: -999, "Unknown")
```

#### 1.2 이상치(Outliers) 처리

**탐지 방법**:

##### 📊 통계적 방법

**1) IQR (Interquartile Range) 방법** ⭐ 가장 많이 사용
```python
Q1 = 25번째 백분위수
Q3 = 75번째 백분위수
IQR = Q3 - Q1

이상치 기준:
- 하한: Q1 - 1.5 × IQR
- 상한: Q3 + 1.5 × IQR

# 예시
데이터: [10, 12, 13, 14, 15, 16, 18, 100]
Q1 = 12.5, Q3 = 16.5, IQR = 4
하한 = 12.5 - 6 = 6.5
상한 = 16.5 + 6 = 22.5
→ 100은 이상치

# 장점: 비정규분포에 강건, 빠른 계산
# 단점: 다차원 데이터 처리 어려움
```

**2) Z-Score (표준편차) 방법**
```python
Z-Score = (값 - 평균) / 표준편차

이상치 기준:
- |Z-Score| > 3 (엄격, 99.7% 신뢰구간)
- |Z-Score| > 2 (일반적, 95% 신뢰구간)

# 예시
데이터: [10, 12, 14, 16, 100]
평균 = 30.4, 표준편차 = 35.8
100의 Z-Score = (100 - 30.4) / 35.8 = 1.94
→ 경계선 (2 이하)

# 장점: 정규분포 데이터에 효과적
# 단점: 이상치에 민감 (평균/표준편차가 이상치 영향 받음)
```

**3) Modified Z-Score (MAD 기반)**
```python
MAD = Median Absolute Deviation
Modified Z-Score = 0.6745 × (값 - 중앙값) / MAD

이상치 기준: |Modified Z-Score| > 3.5

# 장점: 이상치에 강건 (중앙값 사용)
# 단점: 계산 복잡도 높음
```

##### 🤖 머신러닝 방법

**4) Isolation Forest**
```python
from sklearn.ensemble import IsolationForest

# 원리: 랜덤하게 데이터를 분할하여 고립시키기 쉬운 점을 이상치로 판별
# 장점: 다차원 데이터에 효과적, 비지도 학습
# 단점: 하이퍼파라미터 튜닝 필요
```

**5) DBSCAN (밀도 기반 클러스터링)**
```python
from sklearn.cluster import DBSCAN

# 원리: 밀도가 낮은 영역의 점을 이상치로 판별
# 장점: 임의 형태의 클러스터 탐지
# 단점: 파라미터(eps, min_samples) 설정 민감
```

**6) Local Outlier Factor (LOF)**
```python
from sklearn.neighbors import LocalOutlierFactor

# 원리: 주변 이웃과의 밀도 비교
# 장점: 국소적 이상치 탐지에 강함
# 단점: 계산 비용 높음 (O(n²))
```

##### 📈 시각적 방법

**7) Box Plot (상자 그림)**
```
    |----[====|====]----| 
    최소  Q1  중앙 Q3  최대
    
    ●  ← 이상치 (상한 밖)
    
# 장점: 직관적, 빠른 시각적 확인
# 단점: 1차원 데이터만 가능
```

**8) Scatter Plot (산점도)**
```python
# 2개 변수 간 관계에서 벗어난 점 시각적 확인
# 장점: 2차원 관계 파악 용이
# 단점: 3차원 이상 어려움
```

##### 🎯 도메인 기반 방법

**9) 비즈니스 규칙**
```python
# 예시
나이: 0 < 나이 < 120
연봉: 최저임금 < 연봉 < 10억
온도: -50°C < 온도 < 60°C
주문량: 0 < 주문량 < 재고량

# 장점: 명확한 기준, 도메인 지식 반영
# 단점: 규칙 정의 필요, 유연성 부족
```

**10) 시계열 기반**
```python
# 이동평균 대비 급격한 변화
# 계절성 패턴에서 벗어난 값
# STL 분해 (Seasonal-Trend-Loess)

# 장점: 시간적 맥락 고려
# 단점: 충분한 데이터 필요
```

#### 이상치 처리 전략

```python
# 1. 제거 (Removal)
- 명백한 오류인 경우
- 데이터 충분히 많은 경우
- 주의: 정보 손실 가능

# 2. 변환 (Transformation)
- 캡핑(Capping): 상/하한값으로 조정
- 로그 변환: 분포 정규화
- Winsorization: 극단값을 백분위수로 대체

# 3. 분리 (Separation)
- 별도 분석 대상으로 분류
- 이상 거래 탐지 등

# 4. 유지 (Keep)
- 의미있는 극단값 (VIP 고객 등)
- 도메인 전문가 확인 후 결정
```

#### 방법 선택 가이드

| 상황 | 추천 방법 | 이유 |
|------|----------|------|
| **단일 변수, 정규분포** | Z-Score | 통계적 근거 명확 |
| **단일 변수, 비정규분포** | IQR ⭐ | 강건성, 빠른 계산 |
| **다차원 데이터** | Isolation Forest, LOF | 변수 간 관계 고려 |
| **시계열 데이터** | 이동평균, 계절성 분석 | 시간적 맥락 반영 |
| **명확한 업무 규칙** | 도메인 규칙 | 비즈니스 요구사항 |
| **빠른 탐지 필요** | IQR | 계산 복잡도 낮음 |
| **고차원 데이터** | Isolation Forest | 차원의 저주 극복 |

#### 실전 조합 전략

```python
# 추천 파이프라인
def detect_outliers(data):
    # 1단계: 도메인 규칙으로 명백한 오류 제거
    data = apply_business_rules(data)
    
    # 2단계: IQR로 통계적 이상치 탐지
    outliers_iqr = detect_iqr_outliers(data)
    
    # 3단계: 시각화로 검증
    visualize_boxplot(data, outliers_iqr)
    
    # 4단계: 다차원 데이터는 Isolation Forest 추가
    if data.shape[1] > 3:
        outliers_if = detect_isolation_forest(data)
        outliers = outliers_iqr & outliers_if  # 교집합
    
    # 5단계: 도메인 전문가 확인
    return outliers
```

**가장 실용적인 조합**: **IQR + 도메인 규칙 + 시각적 검증** ✅

#### 기타 기능

**데이터 타입 자동 변환**:
- 문자열 → 숫자 (가능한 경우)
- 날짜 형식 자동 인식
- 범주형 변수 인코딩

**중복 제거**:
- 완전 중복 행 제거
- 부분 중복 탐지 (유사도 기반)

**정규화/표준화**:
- Min-Max Scaling: [0, 1] 범위
- Standard Scaling: 평균 0, 표준편차 1
- Robust Scaling: 이상치에 강건

**도구**:
- pandas
- numpy
- scikit-learn (preprocessing)
- scipy.stats

**프롬프트 예시**:
```
"이 데이터의 결측치를 처리하고 IQR 방법으로 이상치를 제거해줘"
→ DataCleaningAgent 실행
→ 전처리 보고서 + 정제된 데이터 반환

"매출 데이터에서 이상치를 탐지하되, 상위 1% 고객은 유지해줘"
→ 도메인 규칙 + IQR 조합 적용
```

---

### 2. StatisticalAgent
**역할**: 고급 통계 분석

**기능**:
- 기술 통계 (평균, 분산, 왜도, 첨도)
- 상관관계 분석
- 가설 검정 (t-test, ANOVA, chi-square)
- 회귀 분석 (선형/다항)
- 시계열 분석 (추세, 계절성)

**도구**:
- scipy.stats
- statsmodels
- scikit-learn

**프롬프트 예시**:
```
"매출과 광고비의 상관관계를 분석하고 회귀 모델을 만들어줘"
→ StatisticalAgent 실행
→ 상관계수, p-value, 회귀식, R² 반환
```

---

### 3. VisualizationAgent
**역할**: 자동 시각화 생성

**기능**:
- 차트 자동 선택 (데이터 타입 기반)
  - 수치형: 히스토그램, 박스플롯, 산점도
  - 범주형: 막대 그래프, 파이 차트
  - 시계열: 선 그래프, 영역 차트
- 다중 차트 대시보드
- 인터랙티브 차트 (Plotly)
- 이미지 저장 (PNG/SVG)

**도구**:
- matplotlib
- seaborn
- plotly
- PIL (이미지 처리)

**프롬프트 예시**:
```
"월별 매출 추이를 시각화하고 제품별 비교 차트도 만들어줘"
→ VisualizationAgent 실행
→ 2개 차트 생성 + 이미지 경로 반환
```

**출력 형식**:
```python
{
    "charts": [
        {
            "type": "line",
            "title": "월별 매출 추이",
            "path": "/path/to/chart1.png",
            "description": "2024년 매출이 전년 대비 15% 증가"
        },
        {
            "type": "bar",
            "title": "제품별 매출 비교",
            "path": "/path/to/chart2.png"
        }
    ]
}
```

---

### 4. ReportAgent
**역할**: 자동 보고서 작성

**기능**:
- 분석 결과 요약
- 차트 삽입
- 인사이트 텍스트 생성 (LLM 활용)
- 다양한 포맷 출력
  - Markdown
  - HTML
  - PDF
  - PowerPoint

**도구**:
- python-docx (Word)
- python-pptx (PowerPoint)
- markdown
- weasyprint (PDF)

**프롬프트 예시**:
```
"지금까지 분석한 내용을 PowerPoint 보고서로 만들어줘"
→ ReportAgent 실행
→ 제목, 요약, 차트, 결론이 포함된 PPTX 생성
```

**보고서 구조**:
```
1. 표지
   - 제목: "데이터 분석 보고서"
   - 날짜, 분석자

2. 요약 (Executive Summary)
   - 핵심 발견사항 3-5개

3. 데이터 개요
   - 데이터 출처, 크기, 기간
   - 전처리 내역

4. 분석 결과
   - 차트 + 설명
   - 통계 수치

5. 인사이트 및 제언
   - AI 생성 인사이트
   - 액션 아이템
```

---

## 🔄 DataAnalysisOrchestrator

### 역할
복잡한 데이터 분석을 **자동으로 워크플로우화**

### 워크플로우 예시
```python
사용자: "이 매출 데이터를 분석하고 보고서 만들어줘"

Orchestrator 실행 순서:
1. PandasAgent: 데이터 로드 및 기본 탐색
2. DataCleaningAgent: 전처리 (결측치 5% 발견 → 제거)
3. StatisticalAgent: 통계 분석 (평균 매출 증가율 12%)
4. VisualizationAgent: 차트 3개 생성
5. ReportAgent: PowerPoint 보고서 생성

최종 출력:
- "분석 완료! 보고서: sales_report_2024.pptx"
- 차트 미리보기 (UI에 표시)
```

### 의사결정 로직
```python
def analyze_data(query, data_path):
    # 1. 데이터 품질 체크
    if has_missing_values(data):
        DataCleaningAgent.clean()
    
    # 2. 분석 유형 판단
    if "상관관계" in query or "회귀" in query:
        StatisticalAgent.correlation_analysis()
    
    if "추이" in query or "변화" in query:
        StatisticalAgent.trend_analysis()
    
    # 3. 시각화 자동 생성
    charts = VisualizationAgent.auto_visualize(data, analysis_results)
    
    # 4. 보고서 생성 (요청 시)
    if "보고서" in query:
        ReportAgent.create_report(analysis_results, charts)
```

---

## 🛠️ 구현 계획

### Phase 1: 기반 구축 (1-2주)
- [ ] `DataAnalysisOrchestrator` 클래스 생성
- [ ] `VisualizationAgent` 구현 (matplotlib/seaborn)
- [ ] 차트 저장 및 UI 표시 기능

### Phase 2: 고급 분석 (2-3주)
- [ ] `StatisticalAgent` 구현
- [ ] `DataCleaningAgent` 구현
- [ ] 멀티 에이전트 협업 로직

### Phase 3: 보고서 생성 (1-2주)
- [ ] `ReportAgent` 구현
- [ ] PowerPoint 템플릿
- [ ] PDF 출력 기능

### Phase 4: UI 통합 (1주)
- [ ] 차트 미리보기 위젯
- [ ] 보고서 다운로드 버튼
- [ ] 분석 진행 상태 표시

---

## 📦 필요한 추가 라이브러리

```python
# 이미 있음
matplotlib
seaborn
pandas
numpy
scikit-learn

# 추가 필요
scipy>=1.11.0           # 통계 분석
statsmodels>=0.14.0     # 시계열, 회귀
plotly>=5.18.0          # 인터랙티브 차트
kaleido>=0.2.1          # Plotly 이미지 저장
weasyprint>=60.0        # HTML → PDF
```

---

## 🎨 UI 개선안

### 1. 차트 표시 영역
```
┌─────────────────────────────────────┐
│  📊 생성된 차트                      │
├─────────────────────────────────────┤
│  [차트1 썸네일]  [차트2 썸네일]      │
│  월별 매출 추이   제품별 비교        │
│  [크게 보기]     [크게 보기]         │
└─────────────────────────────────────┘
```

### 2. 분석 진행 상태
```
┌─────────────────────────────────────┐
│  🔄 데이터 분석 중...                │
├─────────────────────────────────────┤
│  ✅ 데이터 로드 완료                 │
│  ✅ 전처리 완료 (결측치 5% 제거)     │
│  🔄 통계 분석 중... (50%)            │
│  ⏳ 시각화 대기 중                   │
│  ⏳ 보고서 생성 대기 중               │
└─────────────────────────────────────┘
```

### 3. 보고서 다운로드
```
┌─────────────────────────────────────┐
│  📄 보고서 생성 완료!                │
├─────────────────────────────────────┤
│  sales_report_2024.pptx (2.3MB)     │
│  [💾 다운로드] [👁️ 미리보기]         │
└─────────────────────────────────────┘
```

---

## 🚀 사용 시나리오

### 시나리오 1: 매출 분석
```
사용자: "2024년 매출 데이터를 분석하고 인사이트를 찾아줘"

실행 흐름:
1. PandasAgent: sales_2024.csv 로드
2. DataCleaningAgent: 결측치 3건 발견 → 평균값으로 대체
3. StatisticalAgent: 
   - 평균 매출: 1,250만원
   - 증가율: 전년 대비 +15%
   - 최고 매출 월: 12월 (2,100만원)
4. VisualizationAgent:
   - 월별 매출 추이 (선 그래프)
   - 제품별 매출 비중 (파이 차트)
5. LLM 인사이트:
   "12월 매출이 급증한 이유는 연말 프로모션 효과로 추정됩니다.
    2025년에는 분기별 프로모션 전략을 권장합니다."

출력:
- 차트 2개 (UI에 표시)
- 인사이트 텍스트
- "보고서를 만들까요?" (버튼)
```

### 시나리오 2: 고객 세분화
```
사용자: "고객 데이터를 분석해서 세그먼트를 나누고 보고서 만들어줘"

실행 흐름:
1. PandasAgent: customers.csv 로드
2. DataCleaningAgent: 이상치 제거
3. StatisticalAgent: K-means 클러스터링 (3개 그룹)
4. VisualizationAgent:
   - 클러스터 산점도
   - 그룹별 특성 비교 (막대 그래프)
5. ReportAgent: PowerPoint 생성
   - 슬라이드 1: 고객 세그먼트 개요
   - 슬라이드 2-4: 각 그룹 특성
   - 슬라이드 5: 마케팅 제언

출력:
- customer_segmentation_report.pptx
```

---

## 🎯 핵심 차별화 포인트

1. **완전 자동화**: 사용자는 질문만, AI가 전체 파이프라인 실행
2. **멀티 에이전트 협업**: 각 전문 에이전트가 역할 분담
3. **시각화 자동 생성**: 데이터 타입에 맞는 최적 차트 선택
4. **보고서 원클릭**: 분석 → 보고서까지 한 번에
5. **인사이트 추출**: LLM이 숫자 너머의 의미 해석

---

## 📝 다음 단계

1. **프로토타입 개발**: VisualizationAgent 먼저 구현
2. **테스트 데이터**: 샘플 CSV로 전체 플로우 검증
3. **UI 목업**: 차트 표시 영역 디자인
4. **사용자 피드백**: 실제 사용 시나리오 수집

---

## 💬 질문 사항

1. 보고서 포맷 우선순위? (PowerPoint > PDF > Word)
2. 차트 스타일 선호도? (Material Design vs 전문적)
3. 실시간 분석 vs 백그라운드 처리?
4. 분석 결과 저장 위치? (사용자 지정 경로)
