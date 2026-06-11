# Kefcatic — 구현 계획서

> **제품:** 노코드 AI 비서 운영 플랫폼 (Kefcatic)  
> **대상:** AI 에이전트 단계별 실행용  
> **최종 목표:** 비서 생성·실행·마켓플레이스 배포 완료  
> **기술 스택 확정:**

```
Backend   : FastAPI + Python 3.12
ORM/Migration : SQLAlchemy 2.x + Alembic
Auth      : FastAPI OAuth2 (Google, GitHub) + JWT session
Task Queue: Celery + Redis
DB        : PostgreSQL (primary), Redis (cache/broker)
Frontend  : React 19 + Vite + TailwindCSS
Connector : Python connector interface (내부 패키지 assistant_connectors)
Desktop   : 별도 프로젝트로 분리 (Phase 5 이후)
Infra     : Docker Compose (개발) → Railway/Render or VPS (배포)
```

---

## 전체 Phase 구조

| Phase | 명칭 | 핵심 산출물 |
|---|---|---|
| 0 | Foundation | 모노레포 구조, DB 설계, 인프라 셋업 |
| 1 | Core Engine | Connector SDK, Action Engine, Celery 파이프라인 |
| 2 | MVP Product | YouTube 비서 완성, 승인 시스템, 감사 로그 |
| 3 | Platform | 비서 빌더 UI, 템플릿 시스템, 멀티 커넥터 |
| 4 | Marketplace | 커뮤니티 비서 등록/설치, 리뷰, 검수 |
| 5 | Production | 배포, 모니터링, 결제, 멀티 테넌트 |

---

## Phase 0 — Foundation

**목표:** 프로젝트 구조 확정, DB 스키마 설계, 개발 환경 완성  
**완료 기준:** `docker compose up`으로 API + DB + Redis + Worker 전부 기동

### 0-1. 디렉터리 구조 초기화

```
/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 라우터
│   │   ├── core/         # config, security, deps
│   │   ├── models/       # SQLAlchemy 모델
│   │   ├── schemas/      # Pydantic 스키마
│   │   ├── services/     # 비즈니스 로직
│   │   ├── tasks/        # Celery 태스크
│   │   └── connectors/   # Connector SDK
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/          # API client
│   │   └── stores/       # Zustand
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
└── .env.example
```

### 0-2. DB 스키마 설계

> **범위:** Phase 0에서는 실행 엔진에 필요한 핵심 테이블만 생성한다.  
> `marketplace_templates`, `template_reviews`는 Phase 4에서 별도 migration으로 추가한다.

#### Phase 0 핵심 테이블 (12개)

```sql
-- 사용자
users
  id UUID PK
  email VARCHAR UNIQUE NOT NULL
  name VARCHAR
  avatar_url VARCHAR
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- 플랫폼 로그인용 OAuth 계정
-- 책임: 이 서비스에 로그인하기 위한 Google/GitHub 인증 정보만 저장
-- connector_credentials와 구분: oauth_accounts는 "누가 로그인했나",
--   connector_credentials는 "비서가 어떤 외부 API를 쓸 수 있나"
oauth_accounts
  id UUID PK
  user_id UUID FK → users.id
  provider VARCHAR        -- 'google', 'github'
  provider_account_id VARCHAR
  access_token TEXT       -- 로그인 세션용, 암호화 저장
  refresh_token TEXT
  expires_at TIMESTAMP
  created_at TIMESTAMP

-- 비서 정의
assistants
  id UUID PK
  user_id UUID FK → users.id
  name VARCHAR NOT NULL
  description TEXT
  role_type VARCHAR        -- 'youtube_moderator', 'gmail_responder', ...
  system_prompt TEXT       -- LLM에 주입되는 비서 역할 지시문
  config JSONB             -- 비서별 커스텀 설정
  is_active BOOLEAN DEFAULT true
  is_template BOOLEAN DEFAULT false
  template_source_id UUID FK → assistants.id  -- 마켓 설치 시 원본
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- 외부 서비스 연결용 OAuth/API 자격증명
-- 책임: 비서가 YouTube, Gmail 등 외부 API를 호출할 때 사용하는 토큰 저장
-- oauth_accounts와 구분: 로그인과 무관, 커넥터 동작에만 사용
-- 하나의 Google 계정으로 로그인(oauth_accounts)하면서
--   동시에 YouTube 커넥터(connector_credentials)로도 연결 가능
connector_credentials
  id UUID PK
  user_id UUID FK → users.id
  connector_type VARCHAR    -- 'youtube', 'gmail', 'notion', ...
  credentials JSONB         -- Fernet 암호화 저장 (access_token, refresh_token, api_key 등)
  scopes TEXT[]             -- 실제 부여된 OAuth scope 목록
  expires_at TIMESTAMP
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- 비서↔커넥터 연결
assistant_connectors
  id UUID PK
  assistant_id UUID FK → assistants.id
  credential_id UUID FK → connector_credentials.id
  connector_type VARCHAR
  granted_permissions TEXT[]   -- ['comments.read', 'comments.reply', ...]
  config JSONB

-- 권한/승인 정책
permission_policies
  id UUID PK
  assistant_id UUID FK → assistants.id
  action_type VARCHAR          -- 'comment.reply', 'comment.hide', ...
  approval_mode VARCHAR        -- 아래 5단계 중 하나
  -- 'auto'           : 자동 실행 허용 (읽기, 분류 등 low-risk)
  -- 'draft_only'     : 초안만 생성, 실행 없음 (사용자가 수동으로 복사해서 사용)
  -- 'require_approval': 실행 전 사용자 승인 필요
  -- 'always_manual'  : 항상 수동 (비서는 제안만, 실행은 사용자가 직접)
  -- 'disabled'       : 이 액션 자체를 비서에게 허용하지 않음
  risk_level VARCHAR           -- 'low', 'medium', 'high'
  is_reversible BOOLEAN

-- 트리거 설정
triggers
  id UUID PK
  assistant_id UUID FK → assistants.id
  trigger_type VARCHAR          -- 'schedule', 'event', 'webhook'
  cron_expression VARCHAR       -- 스케줄 트리거용
  event_type VARCHAR            -- 이벤트 트리거용
  config JSONB
  is_active BOOLEAN DEFAULT true
  next_run_at TIMESTAMP         -- Celery Beat DB scan 방식에서 사용
                                -- Beat가 실행할 때마다 cron 계산 후 갱신

-- 작업 실행 기록
task_runs
  id UUID PK
  assistant_id UUID FK → assistants.id
  trigger_id UUID FK → triggers.id
  status VARCHAR                -- 'pending', 'running', 'waiting_approval', 'completed', 'failed', 'cancelled'
  started_at TIMESTAMP
  completed_at TIMESTAMP
  error_message TEXT
  result_summary JSONB

-- 개별 액션 기록
action_logs
  id UUID PK
  task_run_id UUID FK → task_runs.id
  action_type VARCHAR
  status VARCHAR                -- 'pending_approval', 'approved', 'rejected', 'executed', 'failed', 'rolled_back'
  input_data JSONB
  output_data JSONB
  rollback_data JSONB           -- 롤백에 필요한 원상복구 정보 (reply_id, original_state 등)
                                -- is_reversible=true인 액션에만 채워짐
  external_resource_id VARCHAR  -- 실제 실행 후 외부 서비스에서 생성된 리소스 ID
                                -- 예: YouTube reply ID, Gmail message ID
                                -- 롤백/감사 시 외부 API 호출에 사용
  executed_at TIMESTAMP
  approved_by UUID FK → users.id
  approved_at TIMESTAMP

-- 승인 요청
-- 결정: action_logs와 별도 테이블로 분리
-- 이유: action_log 1건이 여러 번 승인 요청될 수 있음 (거절 후 수정 재요청),
--       승인 히스토리(누가 언제 거절했는지)를 독립적으로 조회할 필요,
--       action_logs가 실행 결과 기록이라면 approval_requests는 의사결정 기록
approval_requests
  id UUID PK
  action_log_id UUID FK → action_logs.id
  requested_at TIMESTAMP
  status VARCHAR                -- 'pending', 'approved', 'rejected'
  reviewed_by UUID FK → users.id
  reviewed_at TIMESTAMP
  reviewer_note TEXT            -- 거절 사유 또는 수정 메모
  modified_input JSONB          -- "수정 후 승인" 시 사용자가 변경한 입력값

-- 비서 메모리
assistant_memories
  id UUID PK
  assistant_id UUID FK → assistants.id
  memory_type VARCHAR           -- 'preference', 'instruction', 'context'
  key VARCHAR
  value TEXT
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- NOTE: marketplace_templates, template_reviews 테이블은
--       Phase 4 시작 시 별도 Alembic migration으로 추가한다.
--       Phase 0에서 생성하지 않는다.
```

### 0-3. 개발 환경 셋업

```yaml
# docker-compose.yml 구성 요소
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: assistant_platform
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev@postgres/assistant_platform
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: dev-secret-key
    depends_on: [postgres, redis]
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment: *backend-env
    depends_on: [postgres, redis]

  beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on: [redis]

  frontend:
    build: ./frontend
    command: npm run dev
    ports: ["5173:5173"]
```

### 0-4. 기본 FastAPI 셋업

```
작업 목록:
□ pyproject.toml 작성 (fastapi, sqlalchemy, alembic, celery, redis, pydantic-settings, httpx, cryptography)
□ app/core/config.py — Settings (pydantic BaseSettings)
□ app/core/database.py — async SQLAlchemy engine + session
□ app/core/security.py — JWT 발급/검증, 토큰 암호화
□ app/main.py — FastAPI app, CORS, 라우터 등록
□ alembic init + env.py 연결
□ 첫 migration 생성 및 적용
□ /health 엔드포인트 확인
```

---

## Phase 1 — Core Engine

**목표:** Connector SDK 인터페이스 정의, Action Engine, Celery 파이프라인 완성  
**완료 기준:** YouTube 커넥터를 통해 댓글을 가져오고 Celery task로 처리 가능

### 1-1. Connector SDK 설계

```python
# backend/app/connectors/base.py

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

class ConnectorItem(BaseModel):
    id: str
    content: Any
    metadata: dict
    created_at: str

class BaseConnector(ABC):
    connector_type: str  # 클래스 변수

    def __init__(self, credentials: dict, config: dict = {}):
        self.credentials = credentials
        self.config = config

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """자격증명 유효성 검사"""

    @abstractmethod
    async def list_items(self, **kwargs) -> list[ConnectorItem]:
        """항목 목록 조회"""

    @abstractmethod
    async def read_item(self, item_id: str) -> ConnectorItem:
        """단일 항목 조회"""

    async def create_item(self, data: dict) -> ConnectorItem:
        raise NotImplementedError

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        raise NotImplementedError

    async def delete_item(self, item_id: str) -> bool:
        raise NotImplementedError

    async def search(self, query: str, **kwargs) -> list[ConnectorItem]:
        raise NotImplementedError


# 커넥터 레지스트리
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {}

def register_connector(cls: type[BaseConnector]):
    CONNECTOR_REGISTRY[cls.connector_type] = cls
    return cls
```

### 1-2. YouTube 커넥터 구현

```
작업 목록:
□ YouTube Data API v3 OAuth2 flow 구현 (Google OAuth)
□ YoutubeConnector(BaseConnector) 구현
  □ list_items() → 채널 댓글 목록 조회
  □ read_item() → 단일 댓글 조회
  □ create_item() → 답글 작성
  □ update_item() → 댓글 수정
  □ delete_item() → 댓글 삭제/숨김
□ API 엔드포인트: GET /api/connectors/youtube/auth-url
□ API 엔드포인트: GET /api/connectors/youtube/callback
□ credential 저장 (암호화) → connector_credentials 테이블
□ 단위 테스트: 목 응답으로 커넥터 동작 검증
```

### 1-3. Action Engine 설계

```python
# backend/app/services/action_engine.py

from enum import Enum
from pydantic import BaseModel
from typing import Callable, Awaitable

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ApprovalMode(str, Enum):
    AUTO = "auto"               # 자동 실행 (low-risk, 읽기/분류 등)
    DRAFT_ONLY = "draft_only"   # 초안만 생성, 실행하지 않음
    REQUIRE_APPROVAL = "require_approval"  # 실행 전 승인 필요
    ALWAYS_MANUAL = "always_manual"        # 비서는 제안만, 실행은 사용자 직접
    DISABLED = "disabled"       # 이 액션 자체를 허용하지 않음

class ActionDefinition(BaseModel):
    action_type: str
    description: str
    input_schema: dict          # JSON Schema
    output_schema: dict
    required_permission: str
    risk_level: RiskLevel
    default_approval_mode: ApprovalMode
    is_reversible: bool

# 액션 정의 레지스트리
ACTION_REGISTRY: dict[str, ActionDefinition] = {}
ACTION_HANDLERS: dict[str, Callable] = {}

# YouTube 액션 정의 예시
YOUTUBE_ACTIONS = [
    ActionDefinition(
        action_type="youtube.comment.list",
        description="채널의 최근 댓글 목록 조회",
        input_schema={"max_results": "integer", "page_token": "string"},
        output_schema={"comments": "array"},
        required_permission="comments.read",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=True,
    ),
    ActionDefinition(
        action_type="youtube.comment.reply",
        description="댓글에 답글 작성",
        input_schema={"comment_id": "string", "text": "string"},
        output_schema={"reply_id": "string"},
        required_permission="comments.reply",
        risk_level=RiskLevel.MEDIUM,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
    ActionDefinition(
        action_type="youtube.comment.hide",
        description="댓글 숨김 처리",
        input_schema={"comment_id": "string"},
        output_schema={"success": "boolean"},
        required_permission="comments.moderate",
        risk_level=RiskLevel.HIGH,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
]
```

### 1-4. Celery 파이프라인 구성

```python
# backend/app/tasks/celery_app.py
# backend/app/tasks/assistant_tasks.py

작업 목록:
□ celery_app 초기화 (broker=Redis, backend=Redis)
□ 핵심 태스크 정의:
  □ run_assistant_task(assistant_id, trigger_id) — 비서 실행 진입점
  □ execute_action(action_log_id) — 승인된 액션 실행
  □ classify_items(task_run_id, items) — LLM 분류 호출
  □ generate_drafts(task_run_id, classified_items) — 답글 초안 생성
  □ send_approval_notification(task_run_id) — 승인 알림 발송
□ Celery Beat 스케줄 처리 방식: DB scan
  - celerybeat_dispatch() 태스크를 고정 주기(1분)로 등록
  - 매 실행 시 triggers 테이블을 조회하여 is_active=true + 다음 실행 시각이 된 트리거를 선별
  - 해당 트리거마다 run_assistant_task.delay() 호출
  - 동적 등록/해제 방식(Redis에 스케줄 직접 삽입)을 사용하지 않는 이유:
    DB가 단일 진실 소스(source of truth)이므로 DB 변경만으로 스케줄이 자동 반영됨
    Worker 재시작 시 스케줄 소실 위험 없음
  - triggers 테이블에 next_run_at TIMESTAMP 컬럼 추가 필요
□ 태스크 상태를 task_runs 테이블에 실시간 업데이트
□ 실패 시 재시도 정책 (max_retries=3, exponential backoff)
```

### 1-5. LLM 서비스 레이어

```python
# backend/app/services/llm_service.py

작업 목록:
□ OpenAI / Anthropic API 클라이언트 추상화
□ classify_comment(comment_text, categories) → category + confidence
□ generate_reply_draft(comment_text, context, style_guide) → draft_text
□ 비용 추적용 token 사용량 로깅
□ 시스템 프롬프트에 비서 role + 메모리 주입
```

### 1-6. API 엔드포인트 (Phase 1)

```
□ POST /api/auth/google — Google OAuth 시작
□ GET  /api/auth/google/callback — OAuth 콜백 처리
□ GET  /api/auth/me — 현재 유저 정보
□ POST /api/auth/logout

□ POST /api/connectors/youtube/connect — YouTube 연결 시작
□ GET  /api/connectors/youtube/callback
□ GET  /api/connectors — 연결된 커넥터 목록

□ POST /api/task-runs/{assistant_id}/trigger — 수동 실행 트리거
□ GET  /api/task-runs/{task_run_id} — 실행 상태 조회
```

---

## Phase 2 — MVP Product (YouTube 비서)

**목표:** YouTube 댓글 관리 비서를 End-to-End로 완성  
**완료 기준:** 실제 YouTube 계정 연결 → 댓글 분류 → 승인 → 게시 전 과정 동작

### 2-1. 승인 시스템 구현

```
작업 목록:
□ 승인 대기 액션 목록 API: GET /api/approvals?status=pending
□ 단건 승인: POST /api/approvals/{action_log_id}/approve
□ 단건 거절: POST /api/approvals/{action_log_id}/reject
□ 일괄 승인: POST /api/approvals/bulk-approve
□ 승인 후 Celery로 실제 실행 트리거
□ 롤백 API: POST /api/approvals/{action_log_id}/rollback
  - is_reversible=true인 경우만 허용
  - YouTube API로 답글 삭제/숨김 해제
```

### 2-2. 감사 로그 API

```
작업 목록:
□ GET /api/audit/task-runs — 실행 이력 목록 (페이징)
□ GET /api/audit/task-runs/{id} — 실행 상세 + 액션 로그 전체
□ GET /api/audit/action-logs — 액션별 이력
□ 각 action_log에 포함:
  - 입력 데이터 (원본 댓글)
  - LLM 분류 결과 + 신뢰도
  - 생성된 초안
  - 승인/거절 여부 + 시각
  - 실제 실행 결과
```

### 2-3. 프론트엔드 — MVP 화면

```
구현 화면 목록:

① 로그인 페이지
  - Google 로그인 버튼
  - 서비스 소개 (최소한)

② 대시보드 (/)
  - 활성 비서 목록
  - 최근 실행 현황 요약
  - 승인 대기 건수 배지

③ YouTube 비서 설정 (/assistants/new)
  - YouTube 계정 연결 버튼
  - 비서 이름 입력
  - 처리할 채널 선택
  - 자동 실행 스케줄 설정 (매일 몇 시)
  - 승인 정책 설정 (답글/숨김/삭제 각각)

④ 승인 인박스 (/approvals)
  - 대기 중인 액션 목록
  - 카드형: 원본 댓글 + 분류 결과 + 초안 답글
  - 승인 / 수정 후 승인 / 거절 버튼
  - 일괄 승인

⑤ 실행 이력 (/history)
  - 실행 목록 (날짜/상태 필터)
  - 실행 클릭 → 처리한 댓글 목록 + 각 액션 결과

⑥ 비서 설정 상세 (/assistants/:id)
  - 현재 설정 확인/수정
  - 연결된 커넥터
  - 권한 정책
  - 메모리 항목 관리
  - 활성화/비활성화

⑦ Cat Room — 고양이 방 (/cat-room)  [Phase 2 최소 버전]
  - 각 비서를 고양이 캐릭터로 표현
  - 고양이 상태 9종: idle / watching / reading / sorting /
    drafting / waiting_approval / executing / done / error
  - 고양이 클릭 → 우측 패널: 비서명, 연결 앱, 현재 작업, 승인 대기, 최근 활동
  - Phase 2에서는 정적 일러스트 + 상태 텍스트만 구현
  - Phase 3에서 애니메이션, 상태 실시간 SSE 연동 추가
```

### 2-4. 실시간 상태 업데이트

```
작업 목록:
□ WebSocket 또는 SSE (Server-Sent Events) 엔드포인트 구현
  GET /api/ws/task-runs/{task_run_id} — 실행 진행상황 스트리밍
□ 프론트엔드에서 실행 중 상태 폴링 or SSE 구독
□ 완료 시 승인 인박스로 자동 이동
```

### 2-5. 알림 시스템

```
작업 목록 (최소 구현):
□ 브라우저 내 토스트 알림
□ 이메일 알림 (승인 대기 발생 시)
  - FastAPI BackgroundTask + SMTP (또는 SendGrid)
□ 향후 확장: 웹훅, Slack 알림 (Phase 3)
```

---

## Phase 3 — Platform

**목표:** 비서 빌더 UI 완성, 멀티 커넥터 지원, 템플릿 시스템  
**완료 기준:** 코드 수정 없이 UI에서 새로운 비서를 만들고 저장 가능

### 3-1. 비서 빌더 — 스텝 폼

```
5단계 스텝 폼:

Step 1: 역할 설정
  - 비서 이름
  - 어떤 일을 맡길지 (자유 입력 or 템플릿 선택)
  - 말투/응답 스타일 선택 (공손함/단호함/친근함)
  - 금지 행동 입력

Step 2: 커넥터 연결
  - 사용 가능한 커넥터 목록
  - 각 커넥터 연결 상태 확인
  - 비서가 접근할 리소스 선택 (채널, 폴더, 받은편지함 등)

Step 3: 실행 조건
  - 스케줄 트리거: cron 표현식 또는 자연어 입력
  - 이벤트 트리거: 새 항목 감지
  - 수동 실행 전용 옵션

Step 4: 권한 설정
  - 각 액션 유형별 승인 모드 설정
  - 자동 실행 허용 임계값 (신뢰도 몇 % 이상이면 자동)

Step 5: 검토 및 저장
  - 설정 요약
  - 테스트 실행 (샘플 데이터로)
  - 저장 및 활성화
```

### 3-2. 추가 커넥터 구현

```
Gmail 커넥터:
□ Gmail API OAuth scope 설정
□ list_items() → 받은편지함 미확인 메일
□ create_item() → 답장 초안 작성
□ update_item() → 레이블 변경 (읽음/중요)

Google Drive 커넥터:
□ Drive API OAuth scope 설정
□ list_items() → 파일 목록
□ read_item() → 파일 내용 읽기 (Google Docs, PDF)
□ create_item() → 문서 생성

공통:
□ 각 커넥터 OAuth flow 추상화 (중복 제거)
□ token 자동 갱신 로직 (refresh_token 처리)
□ 커넥터별 권한 항목 정의 파일
```

### 3-3. 템플릿 시스템

```
작업 목록:
□ AssistantTemplate 모델 정의 (assistants 테이블의 is_template=true 활용)
□ 기본 제공 템플릿 시딩:
  - YouTube 댓글 관리 비서
  - Gmail 문의 정리 비서
  - Google Drive 문서 요약 비서
□ 템플릿에서 비서 생성 API: POST /api/assistants/from-template/{template_id}
  - 사용자 커넥터 연결 단계 안내
  - 기본 설정 복사
□ 내 비서를 템플릿으로 저장: POST /api/assistants/{id}/save-as-template
```

### 3-4. 메모리/컨텍스트 시스템 UI

```
작업 목록:
□ GET /api/assistants/{id}/memories — 메모리 목록
□ POST /api/assistants/{id}/memories — 메모리 추가
□ PUT /api/assistants/{id}/memories/{key} — 메모리 수정
□ DELETE /api/assistants/{id}/memories/{key} — 메모리 삭제
□ 프론트엔드: 메모리 관리 카드 UI
  - 선호 말투, 금지 표현, 중요 컨텍스트 구분
  - LLM 시스템 프롬프트 주입 확인
```

### 3-5. Cat Room — 고도화

```
디자인 원칙 (Kefcatic Design Brief 기준):
- 흑백 선화 또는 단순 2D 실루엣 일러스트
- 게임 UI처럼 보이면 안 됨 — SaaS 생산성 도구 분위기 유지
- 고양이 요소는 장식이 아니라 실제 작업 상태와 1:1 연결
- 과도한 색상 금지 (monochrome-first, 강조색 최소)
- 상태 텍스트는 기술 용어 대신 자연어 사용
  예: "댓글관리냥이 새 댓글을 살펴보고 있어요." (not "status: reading")

작업 목록:
□ 고양이 상태 SSE 실시간 연동
  - task_runs.status 변화 → 고양이 상태 자동 전환
  - GET /api/assistants/{id}/state — 현재 고양이 상태 반환

□ 9종 상태별 일러스트/SVG 에셋 정의
  - idle           → 자는 고양이
  - watching       → 귀를 세우고 지켜보는 고양이
  - reading        → 댓글/문서 더미를 살펴보는 고양이
  - sorting        → 항목을 분류하는 고양이
  - drafting       → 무언가를 쓰는 고양이
  - waiting_approval → 결과물을 물어와서 기다리는 고양이
  - executing      → 일을 처리 중인 고양이
  - done           → 일 끝내고 쉬는 고양이
  - error          → 도움이 필요한 고양이 (기술 용어 없이 표시)

□ 고양이 클릭 → 우측 패널 실시간 갱신
  - 비서 이름, 연결된 앱, 현재 작업 요약
  - 승인 대기 건수 → 클릭 시 /approvals로 이동
  - 최근 활동 로그 3건
  - 일시정지 / 훈련 설정 / 활동 기록 바로가기

□ 상태 카피 자연어 처리
  - role_type + current_state 조합으로 자동 생성
  - 예: youtube_moderator + reading → "댓글을 살펴보고 있어요."
  - 예: gmail_responder + drafting → "답장 초안을 물어왔어요."
```

---

## Phase 4 — Marketplace

**목표:** 커뮤니티 비서 템플릿 등록·검색·설치  
**완료 기준:** 제3자가 템플릿 등록 → 검수 → 다른 유저가 설치하여 사용 가능

### 4-0. DB Migration — Marketplace 테이블 추가

```sql
-- Phase 4 시작 시 신규 Alembic migration 파일 생성

-- 마켓플레이스 템플릿
marketplace_templates
  id UUID PK
  author_id UUID FK → users.id
  name VARCHAR NOT NULL
  description TEXT
  role_type VARCHAR
  required_connectors TEXT[]
  required_permissions TEXT[]   -- approval_mode 포함: 'comment.reply:require_approval'
  default_config JSONB
  version VARCHAR
  install_count INTEGER DEFAULT 0
  avg_rating FLOAT
  status VARCHAR                -- 'pending', 'approved', 'rejected'
  is_official BOOLEAN DEFAULT false
  created_at TIMESTAMP

-- 템플릿 리뷰
template_reviews
  id UUID PK
  template_id UUID FK → marketplace_templates.id
  user_id UUID FK → users.id
  rating INTEGER                -- 1~5
  comment TEXT
  created_at TIMESTAMP
```

### 4-1. 마켓플레이스 백엔드

```
작업 목록:
□ 템플릿 등록 API: POST /api/marketplace/templates
  - 필수 커넥터/권한 명세 검증
  - 초기 상태: pending (검수 대기)
□ 검수 API (관리자 전용): POST /api/marketplace/templates/{id}/approve|reject
□ 템플릿 검색: GET /api/marketplace/templates?q=&connector=&sort=
□ 템플릿 상세: GET /api/marketplace/templates/{id}
□ 설치: POST /api/marketplace/templates/{id}/install
  - marketplace_templates.install_count 증가
  - user의 assistants에 복사 생성 (template_source_id 연결)
□ 리뷰: POST /api/marketplace/templates/{id}/reviews
□ 신고: POST /api/marketplace/templates/{id}/report
```

### 4-2. 마켓플레이스 프론트엔드

```
구현 화면:

① 마켓플레이스 홈 (/marketplace)
  - 추천 템플릿 (공식)
  - 최다 설치
  - 최신 등록
  - 커넥터별 필터

② 템플릿 상세 (/marketplace/:id)
  - 이름/설명/필요 커넥터/권한 목록
  - 설치 수/평점
  - 리뷰 목록
  - 설치 버튼 → 커넥터 연결 체크 → 비서 생성

③ 내 템플릿 등록 (/marketplace/submit)
  - 비서 선택 or 직접 입력
  - 설명/스크린샷 추가
  - 공개 범위 설정
  - 제출
```

### 4-3. 보안 검수 프로세스

```
자동 검증:
□ 요청하는 권한이 액션에서 실제로 사용되는지 확인
□ 외부 URL 호출 여부 감지 (허용된 커넥터 외 차단)
□ 과도한 권한 요청 경고

관리자 수동 검수:
□ 관리자 대시보드: /admin/marketplace
□ pending 목록 → 승인/거절 + 코멘트
□ 신고 접수 목록
□ 공식 배지 부여
```

---

## Phase 5 — Production

**목표:** 실배포, 모니터링, 결제, 멀티테넌트 안정화  
**완료 기준:** 외부 사용자가 실제로 가입하고 비서를 운영 가능한 상태

### 5-1. 배포 인프라

```
선택지 A (초기 빠른 배포):
  - Backend: Railway or Render (FastAPI 컨테이너)
  - Frontend: Vercel or Netlify
  - DB: Railway PostgreSQL or Supabase
  - Redis: Railway Redis or Upstash
  - Worker: Railway (별도 서비스)

선택지 B (직접 제어):
  - VPS (Hetzner/DigitalOcean) + Docker Compose + Nginx
  - Certbot SSL
  - GitHub Actions CI/CD

작업 목록:
□ Dockerfile 프로덕션 최적화 (multi-stage build)
□ 환경변수 secrets 관리 (.env.prod, Railway/Render secret 주입)
□ Nginx reverse proxy 설정 (API /api → backend, / → frontend)
□ GitHub Actions: test → build → deploy 파이프라인
□ DB 백업 자동화 (pg_dump cron)
```

### 5-2. 모니터링/관찰성

```
작업 목록:
□ Sentry 연동 (FastAPI + React 에러 추적)
□ Celery 태스크 실패 알림 (Slack 또는 이메일)
□ 기본 메트릭 수집:
  - 일별 활성 비서 수
  - 태스크 실행 성공률
  - 평균 처리 시간
  - LLM API 비용
□ Flower (Celery 모니터링 대시보드) 내부용 배포
□ Uptime 모니터링 (UptimeRobot 무료 플랜)
```

### 5-3. 보안 강화

```
작업 목록:
□ credential 암호화 재검토
  - Fernet 대칭 암호화 (cryptography 패키지)
  - 암호화 키를 환경변수로 분리 (절대 DB에 저장 금지)
□ Rate limiting (slowapi)
  - 인증 엔드포인트: 5req/min
  - API 전반: 100req/min/user
□ CORS 프로덕션 도메인만 허용
□ JWT 만료 시간 조정 (access: 15분, refresh: 7일)
□ SQL Injection 방지 — SQLAlchemy ORM 사용 확인
□ 민감 데이터 로그에서 제외 (토큰, 이메일 등)
```

### 5-4. 결제 (선택 — 필요 시)

```
Stripe 연동:
□ 플랜 설계:
  - Free: 비서 2개, 월 100 태스크 실행
  - Pro: 비서 10개, 월 2000 태스크 실행
  - Team: 무제한 (+ 팀 멤버 공유)
□ Stripe Checkout 연동
□ Webhook으로 구독 상태 동기화
□ usage_limits 테이블로 플랜별 제한 적용
□ 한도 초과 시 태스크 실행 거부 + 업그레이드 안내
```

### 5-5. 데스크톱 에이전트 (별도 프로젝트 분리)

```
설계 방향:
  - 로컬 파일 접근, 브라우저 자동화가 필요한 경우만 설치
  - 클라우드 백엔드와 WebSocket으로 통신
  - 민감 데이터를 로컬에서만 처리

기술 스택 (추후 결정):
  - Tauri 2.x (Rust + 경량 WebView)
  - 또는 Python daemon + 시스템 트레이 (pystray)

구현 범위 (Phase 5 이후):
  □ 로컬 파일 커넥터
  □ 브라우저 자동화 커넥터 (Playwright)
  □ OS 알림 연동
  □ 클라우드-로컬 동기화
```

---

## 공통 지침 (에이전트 실행 시)

### 코드 컨벤션

```
Python:
- 타입 힌트 필수 (모든 함수 시그니처)
- async/await 일관 사용 (SQLAlchemy async, httpx async)
- Pydantic v2 사용 (model_validate, model_dump)
- 의존성 주입: FastAPI Depends() 패턴
- 예외: HTTPException + 커스텀 AppException

React:
- TypeScript 필수
- Zustand (전역 상태)
- React Query / TanStack Query (서버 상태)
- react-hook-form (폼)
- 컴포넌트: 기능 단위 분리, props 타입 명시
```

### 테스트 전략

```
Backend:
- pytest + pytest-asyncio
- DB: testcontainers-python (PostgreSQL 16 컨테이너)
  - SQLite 사용 금지 — JSONB, UUID, TEXT[] 등 PG 전용 타입 사용으로 호환 불가
  - conftest.py에서 컨테이너 기동 → Alembic migration → 테스트 → teardown
  - 각 테스트는 트랜잭션 롤백으로 격리
- 커넥터: httpx MockTransport로 외부 API 목킹
- 핵심 커버리지: action_engine, approval flow, connector base

Frontend:
- Vitest + React Testing Library
- 핵심: 승인 인박스 인터랙션, 비서 설정 폼
```

### 디자인 시스템 지침 (Kefcatic)

```
기준: Kefcatic Design Brief — monochrome-first SaaS 생산성 도구

Color:
- 배경: White / Gray-50 (#FAFAFA)
- 텍스트: Black (#0A0A0A), Gray-700 (#374151)
- 구분선/보더: Gray-200 (#E5E7EB)
- 강조색: 1개만 허용, 최소 사용 (예: Gray-900 solid button)
- 상태 색상:
  - Active: solid neutral badge (Gray-900 bg, White text)
  - Idle: Gray-200 bg, Gray-500 text
  - Needs review: outlined badge (Gray-900 border)
  - Error: 아이콘 + 텍스트만, 붉은 배경 금지
  - Done: 체크 아이콘 + 텍스트

Typography:
- Display: 절제된 sans-serif (Inter 또는 Geist)
- Body: 가독성 우선, Korean/English 모두 균형 있게
- 과도하게 귀여운 폰트 금지

Icons:
- 단순 line icon, monochrome, 일관된 stroke width
- 고양이 아이콘은 subtle — 아동용 앱처럼 보이면 안 됨

Cat Room 제약:
- 흑백 선화 또는 단순 실루엣
- 게임 UI 금지 (HP바, 레벨, 반짝이 효과 등)
- 비서 상태는 반드시 텍스트로도 병기
- 애니메이션은 부드럽고 절제되게 (CSS transition, 복잡한 애니메이션 금지)

참조 레퍼런스: Notion, Linear, Raycast, Superhuman
```

### 에이전트 실행 순서 체크리스트

```
Phase 0 완료 체크:
  □ docker compose up 전체 서비스 기동 확인
  □ alembic upgrade head 오류 없음
  □ GET /health → 200

Phase 1 완료 체크:
  □ YouTube OAuth flow 완료 후 credential DB 저장 확인
  □ Celery worker에서 테스트 태스크 실행 확인
  □ LLM 댓글 분류 API 단위 테스트 통과

Phase 2 완료 체크:
  □ 실제 YouTube 계정으로 E2E 테스트 통과
  □ 승인 → 실제 YouTube 답글 게시 확인
  □ 롤백(삭제) 동작 확인
  □ 감사 로그 전 과정 기록 확인

Phase 3 완료 체크:
  □ 비서 빌더 5단계 폼으로 새 비서 생성 확인
  □ Gmail 커넥터 E2E 테스트 통과
  □ 템플릿 설치 → 비서 생성 확인
  □ Cat Room — 9종 상태 전환 SSE 실시간 반영 확인
  □ Cat Room — 게임 UI 요소 없음, 모노톤 디자인 준수 확인

Phase 4 완료 체크:
  □ Phase 4 Alembic migration (marketplace_templates, template_reviews) 적용 확인
  □ 템플릿 등록 → 관리자 승인 → 설치 전 과정 확인
  □ 리뷰/평점 저장 및 표시 확인

Phase 5 완료 체크:
  □ 프로덕션 URL에서 가입 → 비서 생성 → 실행 전 과정
  □ Sentry에 에러 수집 확인
  □ GitHub Actions 자동 배포 확인
```

---

## Platform Safety Rules

에이전트가 코드를 작성할 때 반드시 준수해야 하는 안전 규칙.  
기능 구현보다 우선순위가 높다.

```
[SR-01] 외부 API 실행 전 approval_mode 반드시 확인
  - permission_policies에서 해당 action_type의 approval_mode 조회
  - 'disabled'면 action_log 생성 없이 즉시 거부, 오류 반환
  - 'draft_only'면 output_data에 초안만 저장, 외부 API 호출 금지
  - 'require_approval' / 'always_manual'이면 approval_requests 생성 후 중단
  - 'auto'만 외부 API 즉시 호출 허용

[SR-02] external_resource_id 없이 롤백 시도 금지
  - rollback 호출 시 action_logs.external_resource_id NULL 여부 먼저 확인
  - NULL이면 롤백 불가 상태로 처리, 오류 반환 (외부 리소스 생성 전 실패한 경우)

[SR-03] connector_credentials 복호화는 서비스 레이어에서만 허용
  - API 라우터에서 직접 credentials JSONB 접근 금지
  - 반드시 ConnectorCredentialService.get_decrypted()를 통해서만 접근
  - 복호화된 토큰을 로그에 출력 금지

[SR-04] approval_requests는 action_log당 1개만 pending 허용
  - 새 approval_request 생성 전 기존 pending 건 존재 여부 확인
  - 이미 pending이면 새 요청 생성하지 않고 기존 ID 반환

[SR-05] Celery 태스크에서 DB 세션 직접 생성 금지
  - 반드시 get_async_session() 컨텍스트 매니저 사용
  - 태스크 실패 시 세션이 자동 롤백되도록 try/finally 보장

[SR-06] 마켓플레이스 템플릿 설치 시 권한 범위 상속 금지
  - 템플릿의 required_permissions는 기본값일 뿐
  - 설치 시 사용자가 각 action_type별 approval_mode를 재확인하고 저장
  - 템플릿 작성자의 'auto' 설정이 설치 사용자에게 그대로 적용되면 안 됨
```

---

## 의존성 및 Phase 간 선행 조건

```
Phase 0 → Phase 1: DB 스키마 확정 필수
Phase 1 → Phase 2: YouTube 커넥터 + Action Engine 동작 필수
Phase 2 → Phase 3: 승인 시스템 + 감사 로그 완성 필수
Phase 3 → Phase 4: 템플릿 시스템 완성 필수
Phase 4 → Phase 5: 마켓플레이스 기본 동작 확인 필수

병렬 작업 가능:
- Phase 3 커넥터 추가 ↔ Phase 3 빌더 UI (독립적)
- Phase 4 백엔드 ↔ Phase 4 프론트엔드 (API 계약 먼저 확정 후)
- Phase 5 배포 설정 ↔ Phase 5 모니터링 (독립적)
```
