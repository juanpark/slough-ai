# Slough.ai Development Roadmap

## Timeline Overview

**Total MVP Duration: 4-6 weeks** (with AI assistance)

```
Week 1: Foundation
Week 2: Data Pipeline
Week 3: Core AI Logic
Week 4: Feedback System
Week 5: Polish & Safety
Week 6: Production Ready
```

## Phase 1: Foundation (Week 1)

### Goals
- Slack app created and installable
- Basic message handling working
- Database set up

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | Create Slack workspace & app | App ID, tokens generated |
| | Set up Python project | Project structure, requirements.txt |
| | Configure Socket Mode | Local dev environment working |
| **Day 2** | Implement OAuth flow | Decision-maker can install bot |
| | Store tokens in DB | Workspace record created |
| **Day 3** | Set up PostgreSQL | Local Docker, schema migrated |
| | Set up Pinecone index | Vector DB index created |
| **Day 4** | Basic DM handler | Bot receives messages |
| | Echo response | Bot replies to DMs |
| **Day 5** | Testing & debugging | All Day 1-4 features stable |

### Checklist
- [ ] Slack app created in api.slack.com
- [ ] Socket Mode enabled
- [ ] OAuth flow implemented
- [ ] Bot responds to DMs
- [ ] PostgreSQL running locally
- [ ] Workspace table created

## Phase 2: Data Pipeline (Week 2)

### Goals
- Ingest decision-maker's Slack history
- Generate and store embeddings
- Vector search working

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | List decision-maker's channels | conversations.list working |
| | Paginated history fetch | conversations.history with cursor |
| **Day 2** | Filter decision-maker messages | Extract decision-maker-only messages |
| | Handle threads | Include thread context |
| **Day 3** | Chunking logic | Messages split into ~500 token chunks |
| | OpenAI embedding calls | Embeddings generated |
| **Day 4** | Store in Pinecone | Embeddings upserted with metadata |
| | Build search function | Vector similarity query working |
| **Day 5** | Background job queue | Ingestion runs async via Celery |
| | Progress tracking | Onboarding status tracked |

### Checklist
- [ ] All decision-maker channels fetched
- [ ] Message history paginated correctly
- [ ] Chunking produces reasonable segments
- [ ] Embeddings stored in Pinecone
- [ ] Vector search returns relevant results
- [ ] Background ingestion working
- [ ] Welcome message sent after completion

## Phase 3: Core AI Logic (Week 3)

### Goals
- RAG retrieval working
- Decision-maker persona prompting
- Formatted responses

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | RAG retrieval | Fetch top-k relevant chunks |
| | Reranking/filtering | Remove duplicates, boost recency |
| **Day 2** | Decision-maker persona prompt | System prompt designed |
| | OpenAI GPT-4o integration | Answer generation working |
| **Day 3** | Korean output tuning | Natural Korean responses |
| | Response quality testing | Answers match decision-maker style |
| **Day 4** | Block Kit formatting | Messages have proper structure |
| | Add disclaimer | Warning text included |
| | Add review button | [검토 요청] button working |
| **Day 5** | Response time optimization | < 10 second responses |
| | Error handling | Graceful failures |

### Checklist
- [ ] RAG retrieves relevant context
- [ ] Decision-maker persona prompt crafted
- [ ] Answers are in natural Korean
- [ ] Block Kit formatting correct
- [ ] Disclaimer always present
- [ ] Review button attached
- [ ] Response time < 10 seconds

## Phase 4: Feedback System (Week 4)

### Goals
- Review request flow complete
- Decision-maker feedback buttons working
- Learning data stored

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | Review request action | Button click captured |
| | QA record creation | Question/answer saved |
| **Day 2** | Decision-maker notification | Review request DM sent |
| | Feedback buttons | All 4 buttons rendered |
| **Day 3** | "문제 없음" handler | Positive feedback saved |
| | "틀림" handler | Negative feedback saved |
| | Employee notifications | Status messages sent |
| **Day 4** | "직접 수정" modal | Modal opens, captures edit |
| | Corrected answer delivery | Employee receives correction |
| **Day 5** | "주의 필요" handler | Caution flag saved |
| | Feedback integration | Learning data affects future answers |

### Checklist
- [ ] [검토 요청] creates review record
- [ ] Decision-maker receives notification
- [ ] All 4 feedback buttons work
- [ ] Employee gets feedback notification
- [ ] Edit modal opens and submits
- [ ] Learning data stored correctly

## Phase 5: Polish & Safety (Week 5)

### Goals
- Rule system working
- High-risk detection
- Weekly reminder

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | `/rule add` command | Rules saved to DB |
| | `/rule list` command | Rules displayed |
| | `/rule delete` command | Rules removed |
| **Day 2** | Rule matching logic | Rules checked before answering |
| | Rule actions | Rule triggers appropriate action |
| **Day 3** | High-risk keyword list | Korean keywords defined |
| | Keyword detection | Warning added when detected |
| | Prohibited domain handling | Explicit refusal for out-of-scope topics |
| **Day 4** | Weekly stats aggregation | Stats calculated correctly |
| | Scheduler setup (Celery Beat) | Cron job for Monday 10 AM |
| | Report message | Formatted report sent |
| **Day 5** | Edge case handling | Unusual inputs handled |
| | Error recovery | System recovers from failures |

### Checklist
- [ ] `/rule add` works
- [ ] `/rule list` works
- [ ] `/rule delete` works
- [ ] Rules are applied in answer generation (with precedence over learned patterns)
- [ ] High-risk keywords trigger warning
- [ ] Prohibited domains handled correctly
- [ ] Weekly report generates
- [ ] Report sent on schedule

## Phase 6: Production Ready (Week 6)

### Goals
- Production deployment
- Monitoring set up
- Beta launch ready

### Day-by-Day

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1** | Environment configuration | Staging & production envs |
| | Secrets management | Secure token storage |
| **Day 2** | Production database (RDS) | Cloud DB provisioned |
| | Deployment pipeline (ECS Fargate) | CI/CD configured |
| **Day 3** | Error tracking | Sentry integration |
| | Logging | Structured logging (structlog) |
| **Day 4** | Load testing | System handles expected load |
| | Security review | No obvious vulnerabilities |
| **Day 5** | Documentation review | README, setup guide complete |
| | Beta user preparation | First customers identified |

### Checklist
- [ ] Staging environment working
- [ ] Production environment working
- [ ] CI/CD deploying correctly
- [ ] Monitoring active
- [ ] Error tracking working
- [ ] Security review passed
- [ ] Documentation complete
- [ ] Ready for beta users

## Post-MVP Features (Future)

### Phase 7: Improvements (Week 7-8)
- Feedback mode (decision-maker reviews all conversations)
- Answer quality metrics
- User analytics dashboard

### Phase 8: Scale (Week 9-12)
- Multi-workspace efficiency
- Cost optimization
- Slack App Directory submission

### Phase 9: Growth (Month 3+)
- Channel mention support
- Team hierarchy support
- Integration with other tools

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| LLM response quality | Extensive prompt testing, feedback loop |
| Slack API rate limits | Queue system, backoff strategy |
| Data ingestion failures | Retry logic, partial completion |
| Response latency | Caching, model selection |

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

## Using This Roadmap with Claude CLI

When working with Claude CLI:

1. Reference this roadmap for current phase context
2. Check off completed items as you go
3. Update estimates based on actual progress
4. Document blockers and solutions

```bash
# Example: Starting Phase 1 Day 1
claude "I'm starting Phase 1 Day 1 of the Slough.ai roadmap.
Help me create the Slack app and set up the Python project."
```
