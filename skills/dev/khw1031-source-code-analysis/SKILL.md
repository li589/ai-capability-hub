---
name: source-code-analysis
description: |
  소프트웨어 프로젝트의 소스 코드를 체계적으로 분석합니다. 프로젝트 경로를 입력하면 아키텍처, 데이터 흐름, 설계 패턴, 의존성을 단계별로 파악합니다. 소스 분석, 코드 분석, 리버스 엔지니어링, 아키텍처 분석, 코드베이스 파악 요청 시 활성화.
argument-hint: "[프로젝트 경로]"
install_source: official
install_method: download
skill_id: official_f7gOvtUS
enabled_at: 1787232768780
version: 1.0.0
name_zh: Source分析
---

# 소스 코드 분석

소프트웨어 프로젝트를 Outside-In으로 체계적 분석하는 스킬.

## 핵심 원칙

1. **Outside-In** — 메타데이터/의존성 먼저 → 구조 → 내부 로직 순서
2. **Follow the Data** — 입력→출력 메인 데이터 파이프라인을 추적
3. **Ask Before Diving** — Phase 2 완료 후 반드시 사용자에게 집중 영역 확인 `// !!!`

## 모드 선택

| 모드 | 소요 | Phase | 용도 |
|------|------|-------|------|
| Quick Scan | 5-10분 | 1-2 | 프로젝트 개요 파악 |
| Standard | 20-30분 | 1-5 | 재구축/기여 준비 |
| Full Audit | 60분+ | 1-7 | 보안/품질 감사 포함 |

기본: Standard. 사용자가 별도 지정하지 않으면 Standard 적용.

## 7 Phase 워크플로우

### Phase 1: Surface Scan

프로젝트 메타데이터, 의존성, 엔트리포인트, 빌드 시스템 파악.

```
읽을 파일: package.json, tsconfig.json, Cargo.toml, pyproject.toml, go.mod, Dockerfile 등
```

**산출물**: Project Identity Card (언어, 프레임워크, 빌드, 규모, 엔트리포인트)

Phase별 상세 체크리스트: [phase-checklists.md](references/phase-checklists.md)

### Phase 2: Architecture Mapping

디렉토리→모듈 그래프, 설계 패턴, DI 구조 파악.

```
1. 디렉토리 트리 스캔 (src/ 기준 2단계)
2. 주요 모듈/레이어 식별
3. DI/IoC 패턴 확인
4. Mermaid 아키텍처 다이어그램 생성
```

**산출물**: Architecture Diagram (Mermaid) + 레이어 설명

> **// !!! Phase 2 완료 후 STOP** — 사용자에게 집중 영역 선택을 요청한다.
> "아키텍처를 파악했습니다. 어떤 영역을 깊이 분석할까요?"
> 선택지 제시: 코어 파이프라인 / 특정 모듈 / 외부 연동 / 보안

### Phase 3: Core Pipeline Tracing

메인 데이터 흐름 추적 (입력→처리→출력).

```
1. 엔트리포인트에서 시작
2. 요청/데이터가 흐르는 경로 추적
3. 미들웨어, 서비스, DB 호출 순서 매핑
4. Mermaid 시퀀스/플로우 다이어그램 생성
```

**병렬 분석**: 파이프라인이 여러 갈래면 Explore 서브에이전트를 분기별로 투입.

| 에이전트 | 역할 |
|---------|------|
| A | 메인 파이프라인 (가장 빈번한 경로) |
| B | 보조 파이프라인 또는 특수 처리 |
| C | 에러/폴백 경로 |

**산출물**: Core Data Flow Diagram (Mermaid)

### Phase 4: Deep Dive

핵심 컴포넌트를 상세 분석.

```
각 컴포넌트별:
- 책임 (단일 문장)
- 주요 메서드/함수 시그니처
- 상태 관리 방식
- 에러 처리 전략
- 설계 패턴 (Strategy, Factory, Observer 등)
```

**산출물**: Component Cards (테이블)

### Phase 5: Dependencies & Integration

외부 서비스, 3rd party 라이브러리 매핑.

```
분류:
- 필수 vs 선택
- 대체 가능 vs 불가
- 유료 vs 무료
- 자체 구축 가능 여부
```

**산출물**: Dependency Map + 대체 방안 (재구축 시)

### Phase 6: Security & Quality (Full Audit만)

안티패턴, 취약점, 기술 부채 스캔.

```
- OWASP Top 10 체크
- 하드코딩된 시크릿
- SQL/명령어 인젝션 가능성
- 인증/인가 로직 검증
- 기술 부채 패턴 (TODO, FIXME, 복잡도)
```

**산출물**: Security & Quality Report

### Phase 7: Output Generation

분석 결과를 학습 노트로 생성.

```
note-writer 스킬 연동:
1. 분석 결과를 note-writer 템플릿에 매핑
2. 00-notes/technology/{project-name}-analysis/ 에 생성
3. references/ 하위에 상세 문서 분리
4. 관련 기존 노트와 wikilink 연결
```

노트 구조: [output-template.md](references/output-template.md)

## 교차 스킬 연동

| 상황 | 연동 스킬 |
|------|----------|
| 복잡한 아키텍처 분해 | `decompose-recompose` |
| 설계 가정 검증 | `first-principles` |
| 최종 노트 생성 | `note-writer` |

## 언어별 참조

언어/프레임워크별 분석 휴리스틱: [language-patterns.md](references/language-patterns.md)
