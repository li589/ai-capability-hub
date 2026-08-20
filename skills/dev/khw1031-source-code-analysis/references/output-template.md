# 분석 결과 노트 템플릿

> note-writer 템플릿을 확장한 소스 코드 분석 전용 템플릿.

## SKILL.md 구조

```markdown
---
name: {project}-analysis
description: >
  {project} 소스 코드 분석 노트. {한줄 설명}.
  {project}, {주요키워드들} 관련 질문 시 참조.
keywords:
  - {project}
  - {keyword1}
  - {keyword2}
related:
  - {관련개념1}
  - {관련개념2}
tags:
  - topic/technology/source-analysis
  - type/analysis
  - status/draft
created: {date}
source-type: code
user-invocable: false
---

# {Project Name} 소스 분석

## 요약

> [!summary]
> {프로젝트가 뭔지 + 핵심 아키텍처 + 왜 분석했는지} 2-3문장.

## 쉬운 설명

> [!tip] 비유로 이해하기
> {비개발자도 이해할 수 있는 비유}

## Project Identity

| 항목 | 값 |
|------|-----|
| 언어 | {lang} |
| 프레임워크 | {framework} |
| 아키텍처 | {pattern} |
| 규모 | ~{N} 파일, {M} 주요 서비스 |
| 엔트리 | `{entrypoint}` |

## 아키텍처

{Mermaid 아키텍처 다이어그램}

### 레이어 설명

| 레이어 | 역할 | 주요 파일 |
|--------|------|----------|
| {layer1} | {역할} | `{files}` |
| {layer2} | {역할} | `{files}` |

## 코어 데이터 플로우

{Mermaid 시퀀스/플로우 다이어그램}

## 핵심 컴포넌트

| 컴포넌트 | 파일 | 책임 | 복잡도 |
|---------|------|------|--------|
| {name} | `{file}` | {한줄} | {낮/중/높} |

상세: [컴포넌트 딥다이브](references/components-detail.md)

## 의존성 맵

| 의존성 | 역할 | 필수 | 대체 후보 |
|--------|------|------|----------|
| {dep} | {역할} | O/X | {대안} |

## 재구축 인사이트

### 추출 가능한 핵심

1. {독립적으로 재구축 가능한 부분}
2. {핵심 알고리즘/로직}

### 제거 가능한 부분

1. {선택적 기능}
2. {과도한 추상화}

### 대체 설계 제안

- {더 단순한 접근}

## 관련 개념

- [[00-notes/category/related1/SKILL]] - {관계 설명}
- [[00-notes/category/related2/SKILL]] - {관계 설명}

## 레퍼런스

- [GitHub]({repo-url})

## 상세 문서

- [파이프라인 상세](references/pipeline-detail.md)
- [컴포넌트 딥다이브](references/components-detail.md)
- [재구축 로드맵](references/rebuild-roadmap.md)
```

---

## references/ 파일 구조

### pipeline-detail.md

상세 데이터 플로우 + 코드 스니펫:

```markdown
# 파이프라인 상세

## 전체 흐름

{상세 Mermaid 다이어그램}

## Step 1: {단계명}

**파일**: `{file}:{line}`
**함수**: `{functionName}()`

{설명}

주요 코드:
\`\`\`typescript
// 핵심 로직 스니펫 (10줄 이내)
\`\`\`

## Step 2: ...
```

### components-detail.md

Component Card 전체 목록:

```markdown
# 컴포넌트 딥다이브

## {ComponentName}

| 항목 | 내용 |
|------|------|
| 파일 | `{path}` ({N}줄) |
| 책임 | {한 문장} |
| 주요 메서드 | `method1()`, `method2()` |
| 의존성 | {서비스들} |
| 상태 | {stateless/stateful} |
| 에러 처리 | {전략} |
| 패턴 | {디자인 패턴} |

### 핵심 로직

{설명 + 코드 스니펫}

### 주의점

{gotchas, edge cases}
```

### rebuild-roadmap.md

독립 재구축 시 로드맵:

```markdown
# 재구축 로드맵

## 목표

{왜 재구축하는지, 어떤 부분을}

## Phase 1: 코어 (MVP)

- [ ] {필수 기능 1}
- [ ] {필수 기능 2}

## Phase 2: 확장

- [ ] {선택 기능 1}
- [ ] {선택 기능 2}

## 기술 선택

| 원본 | 대체 | 이유 |
|------|------|------|
| {original} | {replacement} | {why} |

## 리스크

| 리스크 | 영향 | 완화 |
|--------|------|------|
| {risk} | {impact} | {mitigation} |
```
