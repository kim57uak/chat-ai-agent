# JQL 예제

```jql
assignee = currentUser() AND status changed to ("To Do", "In Progress", "Open") BY currentUser() ON startOfDay()
```

이 JQL은 다음을 의미합니다:
- 현재 사용자가 담당자인 이슈 중에서
- 오늘 현재 사용자가 상태를 "To Do", "In Progress", "Open" 중 하나로 변경한 이슈들을 조회