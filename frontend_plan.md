# Kefcatic 디자인 계획서

디자인 기획서를 기반으로 실제 배포까지 고려한 Phase별 계획서를 작성합니다.

---

## Phase 0 — Foundation (1~2주)

실제 구현 전에 반드시 확정해야 하는 기반 작업입니다.

### 0.1 디자인 시스템 구축

**Color Tokens**

```
--color-black: #0A0A0A
--color-white: #FAFAFA
--color-gray-50:  #F5F5F5
--color-gray-100: #E8E8E8
--color-gray-200: #D1D1D1
--color-gray-400: #9A9A9A
--color-gray-600: #5C5C5C
--color-gray-800: #2A2A2A
--color-gray-950: #111111

/* 상태 토큰 — 컬러 최소화 */
--status-active:  #0A0A0A  (solid badge)
--status-idle:    #9A9A9A  (muted)
--status-review:  outlined, #0A0A0A border
--status-error:   #0A0A0A + warning icon (red 배경 금지)
--status-done:    check icon + gray text
```

**Typography Scale**

한/영 동시 고려. Pretendard (Korean) + Inter (English) 조합을 권장합니다.

```
Display:   28px / 700 / -0.5px
Title:     20px / 600 / -0.3px
Body:      14px / 400 / 0px
Caption:   12px / 400 / 0.2px
Label:     12px / 500 / 0.4px (badge, tag)
```

**Spacing System**

4px base unit. 4, 8, 12, 16, 24, 32, 48, 64px

**Border Radius**

```
Card:   8px
Badge:  4px
Button: 6px
Modal:  12px
```

**Elevation / Shadow**

모노톤이므로 shadow 대신 border + background 차이로 레이어 구분.

```
Layer 0 (background):  #F5F5F5
Layer 1 (card):        #FFFFFF, border: 1px #E8E8E8
Layer 2 (modal):       #FFFFFF, border: 1px #D1D1D1, shadow: subtle
```

---

### 0.2 Component Library 정의

**Atoms**
- Button (Primary / Secondary / Ghost / Destructive)
- Badge / StatusBadge
- Input / Textarea
- Checkbox / Toggle
- Icon (line, monochrome, 20px/24px)
- Divider

**Molecules**
- Card (기본 컨테이너)
- AssistantCard (비서 카드)
- ApprovalCard (승인 카드)
- ActivityRow (활동 기록 행)
- ConnectorCard (앱 연결 카드)
- StepIndicator (wizard 진행 표시)
- CatStatusBadge (고양이 상태)

**Organisms**
- Sidebar Navigation
- TopBar
- Cat Room Canvas
- Approval Queue
- Activity Log Table
- Wizard Shell

---

### 0.3 고양이 일러스트 시스템

고양이는 **9가지 상태** 에 대응하는 선화 애셋이 필요합니다.

| 상태 | 일러스트 방향 |
|---|---|
| idle | 웅크리고 눈 감은 고양이 |
| watching | 정면을 바라보는 고양이 |
| reading | 종이 더미를 내려보는 고양이 |
| sorting | 물건을 앞발로 분류하는 고양이 |
| drafting | 연필/펜을 잡고 뭔가 쓰는 고양이 |
| waiting_approval | 물건을 입에 물고 바라보는 고양이 |
| executing | 빠르게 움직이는 고양이 |
| done | 등을 보이고 앉아 쉬는 고양이 |
| error | 귀를 납작하게 하고 주변을 두리번거리는 고양이 |

**스타일 원칙**
- 선 굵기: 1.5~2px 균일
- 세부 묘사 최소화 (디테일보다 실루엣으로 상태 전달)
- 크기별 대응: 24px(icon), 64px(card), 160px(Cat Room)
- 애니메이션: CSS animation 기반, 루프 동작 (호흡, 꼬리 흔들기 정도)

---

## Phase 1 — Core Screens MVP (3~5주)

실제 서비스 가능한 최소 화면 세트.

### 1.1 Dashboard

**레이아웃**

```
┌─────────────────────────────────────┐
│ Sidebar │ TopBar                     │
│         ├─────────────────────────── │
│         │ Summary Cards (4개)        │
│         │ ─────────────────────────  │
│         │ Approvals Preview          │
│         │ ─────────────────────────  │
│         │ Recent Activity            │
└─────────────────────────────────────┘
```

**Summary Cards**

```
[ 오늘 처리된 일: 24 ]  [ 확인할 일: 3 ]
[ 실행 중인 비서: 2 ]   [ 연결 문제: 0 ]
```

숫자가 핵심. 컬러 배지 금지. 상태에 따라 아이콘과 텍스트 weight로만 구분.

**설계 주의사항**
- "확인할 일" 카드는 클릭 시 Approvals 화면으로 즉시 이동
- 연결 문제 존재 시 해당 카드에 warning icon 표시 (빨간 배경 금지)
- 최근 활동은 5개만 노출, "전체 보기" 링크

---

### 1.2 Cat Room

Cat Room은 Kefcatic의 정체성을 보여주는 핵심 화면이지만, **장식이 아니라 실제 상태와 동기화** 되어야 합니다.

**레이아웃**

```
┌─────────────────────────────────────────────┐
│ Sidebar │ [Cat Room]                 [패널]  │
│         │                                   │
│         │   [고양이A]  [고양이B]  [고양이C] │
│         │                                   │
│         │ ───────────────────────────────── │
│         │ Activity Feed (최근 로그 5개)      │
└─────────────────────────────────────────────┘
```

**우측 패널 (고양이 클릭 시)**

```
비서 이름
역할 설명
연결된 앱 (아이콘 나열)
현재 상태 텍스트
─────────────
승인 대기: N개 → [확인하기]
─────────────
[지금 실행] [일시정지] [설정]
```

**구현 고려사항**

Cat Room 배경은 고정 SVG 배경(책상, 방 느낌)에 고양이를 absolute 포지셔닝으로 배치하는 방식이 현실적입니다. 비서가 늘어날수록 자동 배치되어야 하므로 위치 계산 로직이 필요합니다.

---

### 1.3 My Assistants

**레이아웃**

카드 그리드 (2열, 반응형)

**AssistantCard 구조**

```
┌────────────────────────────┐
│ [cat icon] 댓글관리냥      │
│            ● 확인 대기 3개  │
│                            │
│ YouTube 댓글을 살펴보고     │
│ 답글 초안을 만듭니다.      │
│                            │
│ [YouTube 아이콘]           │
│                            │
│ [열기] [훈련] [활동 기록]  │
└────────────────────────────┘
```

상태 표시는 카드 우상단에 StatusBadge 하나로 처리.

---

### 1.4 Create Assistant Wizard

5단계 wizard. 각 단계는 전체 화면을 차지하는 모달 또는 전환 페이지.

**Step 진행 표시**

```
역할 선택 → 앱 연결 → 권한 설정 → 실행 조건 → 최종 확인
   ●──────────○──────────○──────────○──────────○
```

**Step 3 권한 설정 — 핵심 UX**

이 단계가 가장 중요합니다. 사용자가 권한 범위를 명확히 이해해야 신뢰가 생깁니다.

```
각 액션 행:
[액션명]  [설명]  [드롭다운: 자동 / 승인 필요 / 허용 안 함]

예시:
답글 게시     YouTube에 답글을 게시합니다.    [승인 필요 ▼]
댓글 숨김     댓글을 숨깁니다.               [승인 필요 ▼]
댓글 삭제     댓글을 삭제합니다.             [허용 안 함 ▼]
```

삭제·발송 등 되돌리기 불가능한 액션은 기본값을 "승인 필요"로 고정하고 텍스트로 명시.

---

### 1.5 Approvals

**가장 자주 사용되는 화면** 입니다. 마찰을 최소화하는 설계가 필요합니다.

**ApprovalCard 구조**

```
┌──────────────────────────────────────────┐
│ [댓글관리냥]  YouTube · 2분 전           │
│                                          │
│ 원본 댓글                                │
│ "이 영상 설명이 너무 부족한데요?"        │
│                                          │
│ AI 판단                                  │
│ 질문/불만 댓글. 정중한 답변 권장.        │
│                                          │
│ 제안 답글                                │
│ "의견 감사합니다. 다음 영상에서..."      │
│                                          │
│ [수정하기]  [거절]  [승인하고 게시]      │
└──────────────────────────────────────────┘
```

**UX 원칙**
- 원본 / 판단 / 제안 세 블록은 항상 같은 순서로 노출
- 되돌리기 불가능한 작업(게시, 발송)은 버튼에 아이콘 추가
- 대량 승인: 같은 유형의 카드는 "모두 승인" 옵션 제공
- "이 규칙 기억하기": 반복 패턴 학습 트리거

---

### 1.6 Activity Log

필터 + 테이블 구조.

**컬럼**

```
시간 | 비서 | 앱 | 작업 내용 | 판단 근거 | 상태 | 되돌리기
```

- 판단 근거는 기본 접힘(collapse), 클릭 시 펼침
- 되돌리기 가능한 행은 "되돌리기" 버튼 노출
- 필터: 비서별, 앱별, 상태별, 날짜 범위

---

### 1.7 Connectors

**ConnectorCard 구조**

```
┌───────────────────────────────┐
│ [YouTube 로고]  YouTube       │
│                ● 연결됨       │
│                               │
│ 사용 중인 비서: 댓글관리냥    │
│ 권한: 댓글 읽기, 답글 작성    │
│ 마지막 동기화: 10분 전        │
│                               │
│ [재연결]  [연결 해제]         │
└───────────────────────────────┘
```

---

## Phase 2 — Extended Screens (2~3주)

### 2.1 Assistant Detail

My Assistants에서 "열기" 클릭 시 이동하는 상세 화면.

**섹션 구성**
- 상단: 비서 요약 + 빠른 액션
- 탭 구조: 현재 작업 / 승인 대기 / 활동 기록 / 설정

설정 탭에서 훈련 내용, 권한, 스케줄을 수정할 수 있어야 합니다.

---

### 2.2 Marketplace

**레이아웃**

```
[검색] [카테고리 필터]
──────────────────────
공식 비서 템플릿 (가로 스크롤 or 그리드)
──────────────────────
커뮤니티 비서 템플릿 (그리드)
```

**TemplateCard**

```
┌────────────────────────────┐
│ [cat icon]  YouTube 댓글관리냥  │
│             설치 수: 1,240  │
│                            │
│ YouTube 댓글을 분류하고     │
│ 답글 초안을 만듭니다.      │
│                            │
│ 필요 앱: [YouTube 아이콘]  │
│ 필요 권한: 댓글 읽기, 쓰기 │
│                            │
│ [설치하기]                 │
└────────────────────────────┘
```

설치 전 권한 확인 모달은 Create Wizard Step 3과 동일한 UI 재사용.

---

### 2.3 Settings

**섹션**
- 계정 정보
- 보안 (연결된 세션, 2FA)
- 알림 설정 (채널별, 이벤트별)
- API 키 관리
- 로컬 에이전트 설정

---

## Phase 3 — UX Polish & Motion (1~2주)

### 3.1 마이크로 인터랙션

| 상황 | 처리 방식 |
|---|---|
| 비서 승인 처리 | 카드 fade-out + 카운트 감소 |
| 고양이 상태 변경 | 상태 전환 애니메이션 (0.3s ease) |
| 새 승인 알림 | Sidebar badge 증가 + 흔들림 |
| 작업 완료 | check 아이콘 등장 + done 상태 전환 |
| 오류 발생 | error 고양이 + 메시지 (heavy red 금지) |

### 3.2 고양이 애니메이션 상세

CSS animation 기반, 성능 고려.

```
idle:            꼬리 좌우 흔들기 (2s loop)
watching:        눈 깜빡임 (4s loop)
reading:         고개 좌우 미세 움직임 (1.5s loop)
executing:       빠른 이동감 (0.5s loop)
waiting_approval: 물어온 물건 흔들기 (1s loop)
error:           귀 납작 + 주변 두리번거림 (2s loop)
```

### 3.3 반응형 대응

| 브레이크포인트 | 처리 |
|---|---|
| ≥1280px | 기본 레이아웃 (Sidebar 고정) |
| 1024–1279px | Sidebar 축소 (아이콘만) |
| 768–1023px | Sidebar 오버레이 |
| <768px | 모바일 BottomNav + 단열 레이아웃 |

Cat Room은 모바일에서 카드 리스트로 폴백.

---

## Phase 4 — Production Handoff (1주)

### 4.1 Figma 구조

```
Kefcatic/
├── 00_Foundations/
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   └── Icons
├── 01_Components/
│   ├── Atoms
│   ├── Molecules
│   └── Organisms
├── 02_Screens/
│   ├── Dashboard
│   ├── Cat Room
│   ├── Assistants
│   ├── Create Wizard
│   ├── Approvals
│   ├── Activity
│   ├── Connectors
│   ├── Marketplace
│   └── Settings
└── 03_Flows/
    ├── YouTube 비서 생성 플로우
    └── 승인 처리 플로우
```

### 4.2 개발 전달 기준

- 모든 컴포넌트 토큰 기반으로 작성 (하드코딩 금지)
- 상태별 variant 완성 (hover, active, disabled, error)
- 고양이 SVG 애셋 9종 완성
- 한/영 텍스트 모두 실제 copy로 작성 (Lorem ipsum 금지)
- 모든 화면 모바일 variant 포함

---

## 전체 타임라인 요약

| Phase | 내용 | 기간 |
|---|---|---|
| Phase 0 | 디자인 시스템, 컴포넌트, 고양이 애셋 | 1~2주 |
| Phase 1 | 핵심 7개 화면 (Dashboard~Connectors) | 3~5주 |
| Phase 2 | 확장 화면 (Detail, Marketplace, Settings) | 2~3주 |
| Phase 3 | 모션, 반응형, UX 정교화 | 1~2주 |
| Phase 4 | 개발 핸드오프, 애셋 정리 | 1주 |
| **합계** | | **8~13주** |

---

**우선순위 판단 기준**

Phase 0 없이 Phase 1을 시작하면 나중에 전면 수정이 발생합니다. 토큰 시스템과 고양이 애셋은 반드시 먼저 확정하고 진행하는 것이 맞습니다.

가장 빠른 MVP 배포를 원한다면 Phase 0 + Phase 1 (Dashboard, Approvals, Assistants, Create Wizard) 4개 화면으로 먼저 릴리즈하는 방법도 있습니다.
