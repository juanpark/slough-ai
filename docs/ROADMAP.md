# Slough.ai Development Roadmap

## Timeline Overview

**Total MVP Duration: 4-6 weeks** (with AI assistance)

```
Week 1: Foundation          ✅ COMPLETE
Week 2: Data Pipeline       ✅ COMPLETE
Week 3: Core AI Logic       ✅ COMPLETE
Week 4: Feedback System     ✅ COMPLETE
Week 5: Polish & Safety     ✅ COMPLETE
Week 6: Production Ready    ✅ COMPLETE
```

## Phase 1: Foundation (Week 1) - COMPLETE

### Deliverables
- [x] Slack app created in api.slack.com
- [x] Socket Mode enabled (local dev)
- [x] HTTP Mode enabled (production)
- [x] OAuth flow implemented (multi-workspace)
- [x] Bot responds to DMs
- [x] PostgreSQL running (local Docker + AWS RDS)
- [x] Workspace table created
- [x] Onboarding modal (decision-maker selection + channel selection)

## Phase 2: Data Pipeline (Week 2) - COMPLETE

### Deliverables
- [x] All decision-maker channels fetched
- [x] Message history paginated correctly
- [x] Q&A pair preservation (thread replies include parent question)
- [x] Channel context metadata ([#channel-name] prefix)
- [x] Chunking produces ~1000 char segments
- [x] Embeddings stored in pgvector
- [x] Vector search returns relevant results with similarity threshold
- [x] Time-weighted scoring (recent messages prioritized)
- [x] Background ingestion working (Celery)
- [x] Welcome message sent after completion
- [x] Incremental ingestion (`/slough-ingest`)

## Phase 3: Core AI Logic (Week 3) - COMPLETE

### Deliverables
- [x] LangGraph RAG pipeline (check_rules -> check_safety -> retrieve -> generate)
- [x] Persona auto-extraction (GPT-4o-mini, 50 sample messages, Redis cache)
- [x] CEO name injection ("당신은 {name}의 AI 분신입니다")
- [x] Self-identity rules (never say "CEO 정보를 모릅니다")
- [x] 3-layer conversation memory (checkpoint + summary + sliding window)
- [x] Answer priority system (rules > context > persona inference > fallback)
- [x] Korean output tuning
- [x] Block Kit formatting with disclaimer
- [x] Review button attached
- [x] Streaming support

## Phase 4: Feedback System (Week 4) - COMPLETE

### Deliverables
- [x] [검토 요청] creates review record
- [x] Decision-maker receives notification with 4 buttons
- [x] All 4 feedback buttons work (승인/틀림/수정/주의)
- [x] Employee gets feedback notification
- [x] Edit modal opens and submits
- [x] Corrected answers stored as new embeddings
- [x] Button value 2000 char limit handled (fetch answer from DB)

## Phase 5: Polish & Safety (Week 5) - COMPLETE

### Deliverables
- [x] `/slough-rule add` works
- [x] `/slough-rule list` works
- [x] `/slough-rule delete` works
- [x] Rules are applied in answer generation (with precedence)
- [x] High-risk keywords trigger warning
- [x] Prohibited domains handled correctly
- [x] Weekly report generates (Celery Beat)
- [x] Report sent on schedule (Monday 10 AM KST)

## Phase 6: Production Ready (Week 6) - COMPLETE

### Deliverables
- [x] AWS ECS Fargate deployment (3 services: app, worker, beat)
- [x] RDS PostgreSQL + pgvector
- [x] ElastiCache Redis
- [x] CloudFront HTTPS termination
- [x] ALB routing
- [x] CloudWatch logging
- [x] GitHub Actions CI/CD
- [x] CloudFormation infrastructure-as-code
- [x] Multi-workspace Slack app (public distribution)
- [x] App uninstall handling

## Post-MVP Improvements

### Known Issues to Address
- [ ] Completion DM fails for bot decision-makers (`cannot_dm_bot`)
- [ ] Admin should also receive notifications (not just decision-maker)
- [ ] Ingestion deduplication (re-ingestion can create duplicate embeddings)
- [ ] AI answer quality depends on data volume (need more data for better persona)

### Future Features
- [ ] Answer quality metrics and analytics dashboard
- [ ] GPT-4o-mini routing for simple questions (cost optimization)
- [ ] Response caching for frequently asked questions
- [ ] Channel mention support (@bot in channels)
- [ ] Multi-language support
- [ ] User analytics dashboard
- [ ] Slack App Directory submission

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| LLM response quality | Persona extraction, similarity threshold, feedback loop |
| Slack API rate limits | Queue system, backoff strategy, 0.5s delay between pages |
| Data ingestion failures | Retry logic, incremental ingestion, job tracking |
| Response latency | Streaming support, caching strategy |

### Business Risks

| Risk | Mitigation |
|------|------------|
| Low adoption | Clear value proposition, easy onboarding |
| Churn | Feedback loop, continuous improvement |
| Competition | Focus on Korean market, Slack-native |

## Success Metrics

### MVP Success Criteria

| Metric | Target |
|--------|--------|
| Install success rate | > 90% |
| First answer delivery | < 10 seconds |
| Decision-maker satisfaction (beta) | > 4/5 rating |
| Employee satisfaction | > 3.5/5 rating |
| System uptime | > 99% |
