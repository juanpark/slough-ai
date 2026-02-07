# Slough.ai (슬러프)

> Slack 대화로 의사결정자의 사고를 학습하는 AI

의사결정자의 Slack 대화 기록을 학습하여, 팀원들의 질문에 의사결정자의 사고 방식으로 답변하는 B2B SaaS Slack 봇입니다.

## 프로젝트 개요

**문제:** 의사결정자에게 반복적인 질문이 몰리고, 답변 대기로 업무가 지연됨
**해결:** Slack 대화를 학습하여 의사결정자의 사고 패턴을 반영한 AI 답변을 즉시 제공

### 핵심 기능 (MVP)

| 기능 | 설명 |
|------|------|
| 온보딩 & 학습 | OAuth 설치 → 채널 선택 → 대화 기록 수집 |
| Q&A | 팀원이 DM으로 질문 → AI가 의사결정자 스타일로 답변 |
| 피드백 루프 | 검토 요청 → 의사결정자 피드백 (승인/수정/주의) |
| 안전장치 | AI 면책, 고위험 키워드 감지, 금지 도메인 차단 |
| 규칙 선언 | `/slough-rule`로 명시적 규칙 등록 (학습보다 우선) |
| 주간 리포트 | 매주 월요일 10시 활동 요약 DM |

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.12 |
| 웹 프레임워크 | FastAPI |
| Slack SDK | Slack Bolt for Python |
| LLM | OpenAI GPT-4o (팀원 담당) |
| 임베딩 | OpenAI text-embedding-3-small (팀원 담당) |
| 벡터 DB | Pinecone Serverless (팀원 담당) |
| RDBMS | PostgreSQL |
| 작업 큐 | Celery + Redis |
| 배포 | Railway (web / worker / beat 3-서비스) |

---

## 폴더 구조

```
slough-ai/
├── entrypoint.py                  # SERVICE_TYPE 기반 프로세스 라우팅
├── requirements.txt
├── railway.toml                   # Railway 배포 설정
├── Procfile                       # 프로세스 정의 (web/worker/beat)
│
├── src/
│   ├── app.py                     # Bolt 앱 초기화 + 핸들러 등록 + 진입점
│   ├── config.py                  # 환경변수 (pydantic-settings)
│   ├── web.py                     # FastAPI (헬스체크, OAuth, Bolt HTTP 핸들러)
│   ├── worker.py                  # Celery 앱 인스턴스 + beat 스케줄
│   │
│   ├── handlers/                  # Slack 이벤트/액션/커맨드 핸들러
│   │   ├── events/
│   │   │   ├── message.py         # DM 메시지 수신 → AI 답변
│   │   │   └── uninstall.py       # 앱 삭제 이벤트
│   │   ├── actions/
│   │   │   ├── feedback.py        # 피드백 버튼 (승인/틀림/수정/주의)
│   │   │   ├── onboarding.py      # 온보딩 모달 열기
│   │   │   └── review_request.py  # 검토 요청 버튼
│   │   ├── commands/
│   │   │   ├── rule.py            # /slough-rule (규칙 관리)
│   │   │   ├── stats.py           # /slough-stats (통계)
│   │   │   └── help.py            # /slough-help
│   │   └── views/
│   │       ├── edit_answer.py     # 직접 수정 모달
│   │       └── onboarding.py      # 온보딩 모달 제출 처리
│   │
│   ├── services/
│   │   ├── ai/                    # ★ AI 파이프라인 (아래 상세 설명)
│   │   │   └── __init__.py        # 인터페이스 + 스텁
│   │   ├── slack/
│   │   │   ├── conversations.py   # Slack 대화 기록 가져오기
│   │   │   └── oauth.py           # OAuth 설치 플로우
│   │   ├── db/
│   │   │   ├── connection.py      # SQLAlchemy 엔진/세션
│   │   │   ├── models.py          # ORM 모델 (5개 테이블)
│   │   │   ├── workspaces.py      # 워크스페이스 CRUD
│   │   │   ├── rules.py           # 규칙 CRUD
│   │   │   ├── qa_history.py      # Q&A 기록 CRUD
│   │   │   ├── weekly_stats.py    # 주간 통계
│   │   │   └── ingestion_jobs.py  # 수집 작업 추적
│   │   └── ingestion/
│   │       └── ingest.py          # 수집 오케스트레이터
│   │
│   ├── tasks/                     # Celery 비동기 작업
│   │   ├── ingestion.py           # 백그라운드 데이터 수집
│   │   └── weekly_report.py       # 주간 리포트 발송
│   │
│   └── utils/
│       ├── blocks.py              # Block Kit 메시지 빌더
│       ├── keywords.py            # 고위험 키워드 감지
│       ├── prohibited.py          # 금지 도메인 체크
│       └── logger.py              # 로깅 설정
│
├── migrations/versions/           # Alembic DB 마이그레이션
├── tests/                         # 테스트
├── scripts/                       # 유틸리티 스크립트
└── docs/                          # 상세 문서
```

---

## 아키텍처

```
┌─────────────┐     POST /slack/events      ┌──────────────────────┐
│  Slack API  │ ──────────────────────────→  │  slough-web          │
│             │ ←──────────────────────────  │  (FastAPI + Bolt)    │
└─────────────┘     JSON response           │                      │
                                            │  - 이벤트/커맨드 처리  │
                                            │  - OAuth 설치         │
                                            │  - 헬스체크           │
                                            └──────┬───────────────┘
                                                   │ Celery task
                                                   ▼
┌──────────────┐                           ┌──────────────────────┐
│  PostgreSQL  │ ←────────────────────────→ │  slough-worker       │
│  (워크스페이스, │                           │  (Celery worker)     │
│   규칙, Q&A) │                           │                      │
└──────────────┘                           │  - 데이터 수집         │
                                           │  - AI 파이프라인 호출  │
┌──────────────┐                           └──────────────────────┘
│  Redis       │ ←── 작업 큐 ──→
└──────────────┘                           ┌──────────────────────┐
                                           │  slough-beat         │
┌──────────────┐                           │  (Celery scheduler)  │
│  Pinecone    │ ←── 임베딩 저장/검색 ──→    │                      │
│  (벡터 DB)   │                           │  - 주간 리포트 스케줄  │
└──────────────┘                           └──────────────────────┘
```

**운영 모드:**
- **프로덕션 (Railway):** HTTP 모드 — Slack이 POST /slack/events로 이벤트 전송
- **로컬 개발:** Socket Mode — WebSocket으로 연결 (공개 URL 불필요)

---

## AI 파이프라인 통합 가이드 (팀원용)

### 현재 상태

`src/services/ai/__init__.py`에 **스텁(stub)**이 구현되어 있습니다. 3개의 함수가 정의되어 있으며, 현재는 더미 응답을 반환합니다. 이 파일의 실제 구현을 추가하면 됩니다.

### 구현해야 할 함수 3개

#### 1. `generate_answer()` — 질문 → 답변 생성

```python
async def generate_answer(
    question: str,          # 팀원의 질문 텍스트
    workspace_id: str,      # 워크스페이스 UUID
    asker_id: str,          # 질문자의 Slack user ID
    rules: list[dict],      # 활성 규칙 [{"id": int, "rule_text": str}]
) -> AnswerResult:
    """
    RAG + 페르소나 기반 답변 생성.

    호출 시점: 팀원이 봇에게 DM을 보낼 때
    호출 위치: src/handlers/events/message.py (line 80)

    구현 방향:
    1. question을 임베딩하여 Pinecone에서 유사 대화 검색
    2. rules가 있으면 프롬프트에 규칙을 우선 반영
    3. 의사결정자 페르소나 프롬프트 + 검색된 컨텍스트로 GPT-4o 호출
    4. 금지 도메인이면 is_prohibited=True 반환
    5. 고위험 키워드면 is_high_risk=True 반환

    반환값:
    - answer: 한국어 답변 텍스트
    - is_high_risk: 민감 주제 여부
    - is_prohibited: 금지 도메인 여부
    - sources_used: 참고한 소스 수
    """
```

#### 2. `ingest_messages()` — 대화 수집 → 임베딩 저장

```python
async def ingest_messages(
    workspace_id: str,      # 워크스페이스 UUID
    messages: list[dict],   # [{"text": str, "channel": str, "ts": str, "thread_ts"?: str}]
) -> IngestResult:
    """
    의사결정자의 메시지를 청킹 → 임베딩 → Pinecone 저장.

    호출 시점: 온보딩 완료 후 (Celery 백그라운드 작업)
    호출 위치: src/services/ingestion/ingest.py

    구현 방향:
    1. messages를 의미 단위로 청킹
    2. 각 청크를 text-embedding-3-small로 임베딩
    3. Pinecone에 workspace_id 네임스페이스로 저장
    4. 메타데이터: channel, ts, thread_ts 포함

    반환값:
    - chunks_created: 생성된 청크 수
    - embeddings_stored: 저장된 임베딩 수
    """
```

#### 3. `process_feedback()` — 피드백 반영

```python
async def process_feedback(
    workspace_id: str,              # 워크스페이스 UUID
    question_id: str,               # qa_history의 UUID
    feedback_type: str,             # 'approved' | 'rejected' | 'corrected' | 'caution'
    corrected_answer: str | None,   # 'corrected' 타입일 때만
) -> None:
    """
    의사결정자 피드백을 학습 데이터에 반영.

    호출 시점: 의사결정자가 피드백 버튼 클릭 시
    호출 위치: src/handlers/actions/feedback.py

    구현 방향:
    - approved: 답변 품질 양호 → 해당 컨텍스트 가중치 강화
    - rejected: 답변 부정확 → 해당 컨텍스트 가중치 약화
    - corrected: 수정 답변을 새로운 학습 데이터로 추가
    - caution: 주의 필요 플래그 설정
    """
```

### 데이터 흐름 요약

```
[팀원 DM] → message.py → generate_answer() → [AI 답변 반환]
                              ↓
                    Pinecone 검색 + GPT-4o 생성

[온보딩]   → onboarding.py → Celery task → ingest.py → ingest_messages()
                                                ↓
                                      청킹 → 임베딩 → Pinecone 저장

[피드백]   → feedback.py → process_feedback() → [학습 데이터 갱신]
```

### 파일 추가 가이드

AI 코드는 `src/services/ai/` 디렉토리 안에 작성합니다:

```
src/services/ai/
├── __init__.py          # 인터페이스 (수정 — 스텁을 실제 구현으로 교체)
├── embeddings.py        # OpenAI 임베딩 생성 (새로 작성)
├── vector_search.py     # Pinecone 검색 (새로 작성)
├── generation.py        # GPT-4o 답변 생성 (새로 작성)
├── persona.py           # 페르소나 프롬프트 구성 (새로 작성)
└── chunking.py          # 메시지 청킹 로직 (새로 작성)
```

`__init__.py`의 3개 함수만 올바르게 동작하면 Slack 쪽 코드는 수정할 필요가 없습니다.

### 필요한 환경변수

```env
OPENAI_API_KEY=sk-...              # GPT-4o + 임베딩
PINECONE_API_KEY=...               # Pinecone 벡터 DB
PINECONE_INDEX_NAME=slough-contexts
```

Railway에 이미 설정되어 있습니다. 로컬에서는 `.env` 파일에 추가하세요.

### 규칙 우선순위

`rules` 파라미터에 활성 규칙이 전달됩니다. 프롬프트 구성 시 **규칙이 학습 패턴보다 우선**하도록 설계해야 합니다.

```python
# 예시: 프롬프트 구성
system_prompt = f"""
당신은 의사결정자의 사고 방식을 반영하여 답변합니다.

[필수 규칙 - 반드시 준수]
{chr(10).join(f'- {r["rule_text"]}' for r in rules)}

[학습된 패턴]
{retrieved_context}
"""
```

---

## 로컬 개발 환경 설정

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에 Slack 토큰, DB URL 등 입력

# 4. Docker로 PostgreSQL + Redis 실행
docker-compose up -d

# 5. DB 테이블 생성
alembic upgrade head

# 6. 앱 실행 (Socket Mode)
PYTHONPATH=. python src/app.py

# 7. Celery 워커 (별도 터미널)
PYTHONPATH=. celery -A src.worker worker --loglevel=info --concurrency=2

# 8. Celery Beat (별도 터미널, 주간 리포트 스케줄러)
PYTHONPATH=. celery -A src.worker beat --loglevel=info
```

## 배포 (Railway)

3개 서비스가 같은 코드베이스에서 `SERVICE_TYPE` 환경변수로 분기합니다:

| 서비스 | SERVICE_TYPE | 역할 |
|--------|-------------|------|
| slough-web | `web` | FastAPI + Bolt (HTTP 모드) |
| slough-worker | `worker` | Celery 작업 처리 |
| slough-beat | `beat` | Celery 스케줄러 |

```bash
# 배포
railway up --service slough-web
railway up --service slough-worker
railway up --service slough-beat
```

## DB 스키마

| 테이블 | 설명 |
|--------|------|
| `workspaces` | 설치된 워크스페이스 (admin_id, decision_maker_id, 토큰) |
| `rules` | 의사결정자가 등록한 규칙 (/slough-rule) |
| `qa_history` | 질문/답변 기록 + 피드백 상태 |
| `weekly_stats` | 주간 통계 (자동 집계) |
| `ingestion_jobs` | 데이터 수집 진행 상태 |

임베딩은 PostgreSQL이 아닌 **Pinecone**에 저장됩니다.

## 라이선스

Private - All rights reserved
