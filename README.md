# Kefcatic

노코드 AI 비서 자동화 플랫폼 — 고양이 비서가 반복 업무를 대신합니다.

## 개요

Kefcatic은 비기술 사용자도 코드 없이 AI 비서를 만들어 외부 서비스(YouTube, Gmail, Google Drive, Slack, Notion)와 연동된 반복 작업을 자동화할 수 있는 플랫폼입니다.

각 비서는 고양이 캐릭터로 표현되며, 9가지 상태(idle → watching → reading → sorting → drafting → waiting_approval → executing → done → error)를 자연어 텍스트와 함께 표시합니다.

### 핵심 원칙

- 비서가 어떤 행동을 하기 전에 사용자가 반드시 확인할 수 있습니다
- 고위험 작업은 절대 자동 실행되지 않습니다
- 모든 실행 이력이 투명하게 기록됩니다

## 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | FastAPI + Python 3.12 |
| ORM / Migration | SQLAlchemy 2.x (async) + Alembic |
| Auth | Google / GitHub OAuth2 + JWT |
| Task Queue | Celery + Redis |
| DB | PostgreSQL 16 (primary), Redis (cache/broker) |
| Frontend | React 19 + Vite + TailwindCSS |
| State | Zustand (전역) + TanStack Query (서버 상태) |
| Forms | react-hook-form |
| Infra | Docker Compose (개발) → Railway/Render or VPS (운영) |

## 프로젝트 구조

```
/
├── backend/
│   └── app/
│       ├── api/          # FastAPI 라우터
│       ├── core/         # config, security, DB deps
│       ├── models/       # SQLAlchemy 모델
│       ├── schemas/      # Pydantic v2 스키마
│       ├── services/     # 비즈니스 로직 (action_engine, llm_service)
│       ├── tasks/        # Celery 태스크
│       └── connectors/   # Connector SDK
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── api/          # API 클라이언트 레이어
│       └── stores/       # Zustand 스토어
├── docker-compose.yml
└── .env.example
```

## 시작하기

### 사전 요구사항

- Docker + Docker Compose
- Google OAuth 앱 클라이언트 ID / Secret

### 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에서 DB, Redis, OAuth, JWT 시크릿 설정
```

### 개발 서버 실행

```bash
docker compose up
```

API 서버: `http://localhost:8000`  
프론트엔드: `http://localhost:5173`

### DB 마이그레이션

```bash
# 최신 마이그레이션 적용
docker compose exec backend alembic upgrade head

# 새 마이그레이션 생성
docker compose exec backend alembic revision --autogenerate -m "설명"
```

### 테스트

```bash
# 백엔드 테스트 (testcontainers 사용 — 실제 PostgreSQL 컨테이너)
docker compose exec backend pytest

# 단일 테스트
docker compose exec backend pytest tests/path/to/test_file.py::test_name -v

# 프론트엔드 테스트
docker compose exec frontend npm run test
```

## 구현 로드맵

| Phase | 명칭 | 핵심 산출물 |
|---|---|---|
| 0 | Foundation | 모노레포 구조, DB 설계, 인프라 셋업 |
| 1 | Core Engine | Connector SDK, Action Engine, Celery 파이프라인 |
| 2 | MVP Product | YouTube 비서 완성, 승인 시스템, 감사 로그 |
| 3 | Platform | 비서 빌더 UI, 템플릿 시스템, 멀티 커넥터 |
| 4 | Marketplace | 커뮤니티 비서 등록/설치, 리뷰, 검수 |
| 5 | Production | 배포, 모니터링, 결제, 멀티 테넌트 |

## Safety Rules

모든 외부 API 호출은 `approval_mode` 정책을 통과해야 합니다.

| 모드 | 동작 |
|---|---|
| `auto` | 즉시 실행 |
| `draft_only` | 초안 저장, API 호출 없음 |
| `require_approval` | 승인 요청 생성 후 대기 |
| `always_manual` | 항상 사람이 직접 처리 |
| `disabled` | 즉시 거부 |

## 라이선스

Private — 미정
