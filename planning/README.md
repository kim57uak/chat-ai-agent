# Planning & Documentation

이 폴더는 Chat AI Agent 프로젝트의 기획서, 리팩토링 문서, 설계 문서를 관리합니다.

## 📁 폴더 구조

```
planning/
├── README.md                                    # 이 파일
│
├── [RAG 시스템 설계] ⭐ NEW
├── RAG_TOPIC_MANAGEMENT_DESIGN.md              # RAG 주제별 문서 관리 시스템 설계
├── CHUNKING_STRATEGY_DESIGN.md                 # 청킹 전략 상세 설계
├── BATCH_UPLOAD_AUTO_TOPIC_DESIGN.md           # 배치 업로드 & 자동 주제 분류
│
├── [RAG 관련]
├── RAG_AGENT_REDESIGN.md                       # RAG Agent 재설계
├── RAG_MODE_FIX.md                             # RAG 모드 수정
├── RAG_MULTIAGENT_REFACTORING_PLAN.md          # RAG 멀티에이전트 리팩토링 계획
├── RAG_STATUS.md                               # RAG 상태
├── PHASE4_RAG_CHAT_PROCESSOR.md                # Phase 4: RAG Chat Processor
│
├── [리팩토링 관련]
├── REFACTORING_COMPLETE.md                     # 리팩토링 완료
├── REFACTORING_FINAL.md                        # 리팩토링 최종
├── REFACTORING_STATUS.md                       # 리팩토링 상태
├── PHASE3_HARDCODING_REFACTORING.md            # Phase 3: 하드코딩 리팩토링
├── 마이지니_랭체인_벡터화_리펙토링.md            # 랭체인 벡터화 리팩토링
│
├── [토큰 추적 관련]
├── TOKEN_TRACKING_COMPLETE.md                  # 토큰 추적 완료
├── TOKEN_TRACKING_ENHANCEMENT_PLAN.md          # 토큰 추적 개선 계획
├── TOKEN_TRACKING_FIX_SUMMARY.md               # 토큰 추적 수정 요약
├── TOKEN_TRACKING_PHASE1-5_COMPLETE.md         # Phase 1-5 완료
├── TOKEN_TRACKING_PHASE6_COMPLETE.md           # Phase 6 완료
├── TOKEN_ACCURACY_GUIDE.md                     # 토큰 정확도 가이드
│
├── [구현 가이드]
├── MULTI_AGENT_GUIDE.md                        # 멀티 에이전트 가이드
├── PANDAS_AGENT_GUIDE.md                       # Pandas 에이전트 가이드
├── CODE_EXECUTION_DESIGN.md                    # 코드 실행 설계
│
├── [Phase 문서]
├── PHASE5_UI_IMPLEMENTATION.md                 # Phase 5: UI 구현
├── PHASE6_INTEGRATION_TEST.md                  # Phase 6: 통합 테스트
│
├── [기타]
├── IMPLEMENTATION_STATUS.md                    # 구현 상태
├── PACKAGING_CODE_BLOCK_FIX.md                 # 패키징 코드 블록 수정
├── PACKAGING_FIX.md                            # 패키징 수정
└── RENDERING_ANALYSIS.md                       # 렌더링 분석
```

## 📚 문서 카테고리

### 1. 설계 문서 (Design Documents)
프로젝트의 아키텍처와 시스템 설계를 다룹니다.

- `RAG_TOPIC_MANAGEMENT_DESIGN.md` - RAG 주제별 문서 관리 시스템 설계
- `CODE_EXECUTION_DESIGN.md` - 코드 실행 시스템 설계
- `RAG_AGENT_REDESIGN.md` - RAG Agent 재설계

### 2. 리팩토링 문서 (Refactoring Documents)
코드 개선 및 리팩토링 작업을 기록합니다.

- `REFACTORING_*.md` - 리팩토링 진행 상황
- `PHASE3_HARDCODING_REFACTORING.md` - 하드코딩 제거 작업
- `마이지니_랭체인_벡터화_리펙토링.md` - 벡터화 리팩토링

### 3. 구현 가이드 (Implementation Guides)
특정 기능 구현을 위한 가이드입니다.

- `MULTI_AGENT_GUIDE.md` - 멀티 에이전트 시스템 구현
- `PANDAS_AGENT_GUIDE.md` - Pandas 에이전트 사용법
- `TOKEN_ACCURACY_GUIDE.md` - 토큰 추적 정확도 개선

### 4. Phase 문서 (Phase Documents)
프로젝트를 단계별로 진행한 기록입니다.

- `PHASE3_*.md` - Phase 3 작업
- `PHASE4_*.md` - Phase 4 작업
- `PHASE5_*.md` - Phase 5 작업
- `PHASE6_*.md` - Phase 6 작업

### 5. 상태 문서 (Status Documents)
현재 구현 상태와 진행 상황을 추적합니다.

- `IMPLEMENTATION_STATUS.md` - 전체 구현 상태
- `RAG_STATUS.md` - RAG 기능 상태
- `TOKEN_TRACKING_COMPLETE.md` - 토큰 추적 완료 상태

## 🎯 문서 작성 규칙

### 파일명 규칙
- 영어로 작성 (예외: 한글 제목이 필요한 경우)
- 대문자와 언더스코어 사용 (예: `RAG_TOPIC_MANAGEMENT_DESIGN.md`)
- 카테고리 접두사 사용 (예: `PHASE4_`, `RAG_`, `TOKEN_`)

### 문서 구조
```markdown
# 제목

## 개요
간단한 설명

## 목표
달성하고자 하는 목표

## 설계/구현
상세 내용

## 체크리스트
- [ ] 작업 항목

## 참고
관련 문서 링크
```

### 문서 메타데이터
각 문서 하단에 다음 정보 포함:
```markdown
---
**작성일**: YYYY-MM-DD
**버전**: X.Y
**상태**: 설계/진행중/완료
**관련 문서**: [링크]
```

## 🔄 문서 업데이트 프로세스

1. **새 기획 시작**: `planning/` 폴더에 새 MD 파일 생성
2. **진행 중**: 문서 상태를 "진행중"으로 표시
3. **완료**: 문서 상태를 "완료"로 변경, 날짜 기록
4. **보관**: 완료된 문서는 그대로 유지 (삭제 금지)

## 📖 문서 읽는 순서

### 신규 개발자
1. `README.md` (프로젝트 루트)
2. `MULTI_AGENT_GUIDE.md`
3. `CODE_EXECUTION_DESIGN.md`
4. `IMPLEMENTATION_STATUS.md`

### RAG 기능 개발
1. `RAG_STATUS.md`
2. `RAG_TOPIC_MANAGEMENT_DESIGN.md`
3. `RAG_AGENT_REDESIGN.md`
4. `PHASE4_RAG_CHAT_PROCESSOR.md`

### 리팩토링 작업
1. `REFACTORING_STATUS.md`
2. `PHASE3_HARDCODING_REFACTORING.md`
3. `마이지니_랭체인_벡터화_리펙토링.md`

## 🔗 관련 리소스

- **프로젝트 README**: `../README.md`
- **개발자 가이드**: `../DEVELOPER.md`
- **아키텍처 문서**: `../Chat_Ai_Architecture.md`
- **최종 보고서**: `../FINAL_REPORT.md`

## 📝 문서 템플릿

새 문서 작성 시 다음 템플릿을 사용하세요:

```markdown
# [문서 제목]

## 개요
이 문서는 [목적]을 위해 작성되었습니다.

## 배경
[왜 이 작업이 필요한가?]

## 목표
- [ ] 목표 1
- [ ] 목표 2

## 설계/구현

### 아키텍처
[구조 설명]

### 주요 컴포넌트
[컴포넌트 설명]

### 데이터 흐름
[흐름 설명]

## 구현 계획

### Phase 1
- [ ] 작업 1
- [ ] 작업 2

### Phase 2
- [ ] 작업 3

## 참고 사항
[추가 정보]

---
**작성일**: YYYY-MM-DD
**버전**: 1.0
**상태**: 설계/진행중/완료
**작성자**: [이름]
```

---

**최종 업데이트**: 2024
**관리자**: Chat AI Agent Team
