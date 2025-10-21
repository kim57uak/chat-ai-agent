# Deprecated Files

이 폴더는 리팩토링 과정에서 더 이상 사용하지 않는 파일들을 보관합니다.

## 파일 목록

### fixed_formatter.py
- **이동 날짜**: 2024
- **이유**: 새로운 렌더러 시스템(ui/renderers/)으로 대체됨
- **대체 파일**: 
  - `ui/renderers/content_renderer.py` (통합 진입점)
  - `ui/renderers/code_renderer.py` (코드 블록)
  - `ui/renderers/markdown_renderer.py` (마크다운)
  - `ui/renderers/mermaid_renderer.py` (다이어그램)
  - `ui/renderers/image_renderer.py` (이미지)

## 리팩토링 원칙

1. **SOLID 원칙 준수**: 각 렌더러가 단일 책임을 가짐
2. **Facade 패턴**: ContentRenderer가 통합 인터페이스 제공
3. **확장성**: 새로운 렌더러 추가 용이
4. **유지보수성**: 각 렌더러를 독립적으로 수정 가능

## 주의사항

- 이 폴더의 파일들은 참고용으로만 사용하세요
- 새로운 기능 개발 시 `ui/renderers/` 폴더의 파일들을 사용하세요
- 완전한 리팩토링 완료 후 이 폴더는 삭제될 수 있습니다
