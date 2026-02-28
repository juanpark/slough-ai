# Slough.ai Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        SLACK WORKSPACE                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐     ┌──────────┐     ┌──────────────────────┐    │
│  │ Team     │ DM  │ Slough   │     │  Decision-Maker      │    │
│  │ Members  │────▶│   Bot    │────▶│   - Review requests  │    │
│  │          │◀────│          │◀────│   - Feedback         │    │
│  └──────────┘     └────┬─────┘     │   - /slough-rule     │    │
│                        │           │   - /slough-ingest   │    │
│                        │           └──────────────────────┘    │
└────────────────────────┼───────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AWS CLOUD INFRASTRUCTURE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌──────┐     ┌────────────────────────────┐   │
│  │CloudFront│────▶│ ALB  │────▶│  ECS Fargate               │   │
│  │ (HTTPS)  │     └──────┘     │  ┌─────┐┌──────┐┌──────┐  │   │
│  └──────────┘                  │  │ app ││worker││ beat │  │   │
│                                │  └─────┘└──────┘└──────┘  │   │
│                                └────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   LLM API   │  │   RDS       │  │   ElastiCache           │  │
│  │  (OpenAI    │  │ PostgreSQL  │  │   Redis                 │  │
│  │   GPT-4o)   │  │ + pgvector  │  │  - Celery broker/backend│  │
│  └─────────────┘  │ - Workspaces│  │  - Persona cache        │  │
│                   │ - Rules/QA  │  │  - Rule cache           │  │
│                   │ - Embeddings│  │  - Dedup keys           │  │
│                   └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  CloudWatch │  │    ECR      │                               │
│  │  (Logging)  │  │ (Container) │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Core Flow

### 1. Installation Flow

```
Decision-maker visits /slack/install
        │
        ▼
┌─────────────────┐
│   OAuth Flow    │
│  (Bot + User    │
│   Token)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store tokens   │
│  in database    │
│  (admin_id =    │
│   installer)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Onboarding     │
│  Modal          │
│  - Select DM    │
│  - Select chans │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Background:    │
│  Ingest Slack   │
│  history        │
│  + Extract      │
│  persona        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Send welcome   │
│  DM to decision │
│  maker          │
└─────────────────┘
```

### 2. Question-Answer Flow (LangGraph)

```
Employee sends DM
        │
        ▼
┌─────────────────┐
│  check_rules    │──── Match? ──▶ Execute rule action → END
│                 │     (rules take precedence)
└────────┬────────┘
         │ No match
         ▼
┌─────────────────┐
│  check_safety   │──── Prohibited? ──▶ refuse_answer → END
│                 │
│                 │──── High-risk? ──▶ Set flag (continue)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   retrieve      │──── pgvector search (threshold=0.5)
│                 │     + time-weighted scoring
│                 │     + cosine similarity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   generate      │──── Build persona prompt:
│                 │     1. CEO name + self-identity rules
│                 │     2. Persona profile (from Redis)
│                 │     3. Rules (from DB)
│                 │     4. Retrieved context (from pgvector)
│                 │     5. 3-layer memory (trim + summarize)
│                 │     → GPT-4o generation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Send Response   │──── Include [검토 요청] button
│ with Block Kit  │     + disclaimer + high-risk warning
└─────────────────┘
```

### 3. Feedback Loop Flow

```
Employee clicks [검토 요청]
        │
        ▼
┌─────────────────┐
│  Create review  │
│  request record │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DM to decision │──── Include: question, AI answer,
│  maker w/buttons│     [✅][❌][✏️][⚠️] buttons
└────────┬────────┘
         │
         ▼
   Decision-maker clicks button
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
 ✅문제없음  ❌틀림   ✏️직접수정  ⚠️주의필요
    │         │         │          │
    ▼         ▼         ▼          ▼
 Positive   Negative   Ground    Caution
 Example    Example    Truth     Flag
    │         │         │          │
    └────┬────┴─────────┴──────────┘
         │
         ▼
┌─────────────────┐
│ Notify employee │
│ of feedback     │
└─────────────────┘
```

### 4. Incremental Learning Flow

```
Admin runs /slough-ingest
        │
        ▼
┌─────────────────┐
│ Permission check│──── Not admin/DM? ──▶ Deny
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check last      │
│ ingestion time  │──── Get oldest= from last completed job
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fetch NEW msgs  │──── Only messages after oldest timestamp
│ from channels   │     (avoids duplicates)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Chunk & embed   │──── Store in pgvector
│ new messages    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Re-extract      │──── GPT-4o-mini analyzes updated corpus
│ persona         │     → cache in Redis
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notify DM       │
└─────────────────┘
```

## Data Pipeline

### Data Ingestion (Initial + Incremental)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Slack History                                              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                                │
│  │ Extract │ ─── conversations.list                        │
│  │         │ ─── conversations.history (paginated)         │
│  └────┬────┘                                                │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                                │
│  │ Filter  │ ─── Decision-maker messages only              │
│  │         │ ─── Include thread context (Q&A pairs)        │
│  │         │ ─── Prefix channel name [#channel]            │
│  └────┬────┘                                                │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                                │
│  │  Chunk  │ ─── ~1000 char chunks                         │
│  └────┬────┘                                                │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                                │
│  │  Embed  │ ─── OpenAI text-embedding-3-small             │
│  │         │ ─── 1536 dimensions                           │
│  └────┬────┘                                                │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                                │
│  │  Store  │ ─── pgvector (PostgreSQL)                     │
│  │         │ ─── With metadata (channel, timestamp)        │
│  └────┬────┘                                                │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────┐                                           │
│  │  Persona     │ ─── GPT-4o-mini analyzes 50 samples      │
│  │  Extraction  │ ─── Cache profile in Redis               │
│  └──────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### RAG Retrieval Strategy

```
User Question
     │
     ▼
┌──────────────┐
│ Embed Query  │ ─── text-embedding-3-small
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Vector Search│ ─── Top-5 similar chunks
│  (pgvector)  │ ─── Cosine similarity > 0.5 threshold
│              │ ─── Time-weighted scoring:
│              │     score = similarity * (1/(1+0.1*ln(age+1)))
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Build Context│ ─── Combine retrieved chunks
│              │ ─── Add to persona prompt
└──────────────┘
```

## Database Schema

### Entity Relationship

```
┌─────────────────────┐
│   workspaces        │
├─────────────────────┤
│ id (PK, UUID)       │
│ slack_team_id       │
│ slack_team_name     │
│ admin_id            │
│ decision_maker_id   │
│ bot_token           │
│ user_token          │
│ installed_at        │
│ onboarding_completed│
└─────────────────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│  rules   │ │qa_history│ │  embeddings  │
├──────────┤ ├──────────┤ ├──────────────┤
│ id (PK)  │ │ id (UUID)│ │ id (UUID)    │
│ ws_id(FK)│ │ ws_id(FK)│ │ ws_id (FK)   │
│ rule_text│ │ asker_id │ │ content      │
│ is_active│ │ question │ │ embedding    │
│ created  │ │ answer   │ │   (vector    │
└──────────┘ │ feedback │ │    1536)     │
             │ corrected│ │ channel_id   │
             └──────────┘ │ message_ts   │
                          │ created_at   │
                          └──────────────┘

┌──────────────┐  ┌─────────────────┐
│ weekly_stats │  │ ingestion_jobs  │
├──────────────┤  ├─────────────────┤
│ id (PK)      │  │ id (UUID)       │
│ ws_id (FK)   │  │ ws_id (FK)      │
│ week_start   │  │ status          │
│ total_qs     │  │ channels_total  │
│ reviews      │  │ channels_done   │
│ feedback     │  │ msgs_processed  │
└──────────────┘  │ started_at      │
                  │ completed_at    │
                  └─────────────────┘
```

All data including vector embeddings is stored in PostgreSQL with pgvector extension.

## Component Architecture

### Application Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Events    │  │   Actions   │  │     Commands        │ │
│  │  Handlers   │  │  Handlers   │  │     Handlers        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      SERVICE LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Slack   │  │    AI    │  │Ingestion │  │  Redis     │ │
│  │ Service  │  │ Pipeline │  │ Service  │  │  Client    │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     DATA ACCESS LAYER                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │Workspace │  │  Rules   │  │    QA    │  │ Embeddings │ │
│  │   Repo   │  │   Repo   │  │   Repo   │  │    Repo    │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE LAYER                      │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────────────┐   │
│  │  PostgreSQL  │  │  Redis   │  │   External APIs     │   │
│  │  + pgvector  │  │(ElastiC) │  │ (OpenAI, Slack)     │   │
│  └──────────────┘  └──────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Redis Cache Layout

| DB | Purpose | Key Pattern |
|----|---------|-------------|
| DB0 | Celery Broker (task queue) | - |
| DB1 | Celery Backend (task results) | - |
| DB2 | App Cache | `persona:{workspace_id}`, `dm_name:{workspace_id}`, `rule:{keyword}`, `dedup:{event_id}` |

## Security Considerations

### Token Storage
- All Slack tokens stored in RDS (encrypted at rest)
- Use environment variables for API keys (ECS task definitions)
- Never log tokens

### Data Privacy
- Decision-maker data accessible only within their workspace (workspace_id isolation)
- Employee questions stored with workspace isolation
- Support data deletion on uninstall

### API Security
- Verify Slack request signatures
- Rate limiting on LLM calls
- Input sanitization before LLM prompts
- CloudFront HTTPS termination
