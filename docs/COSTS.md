# Slough.ai Cost Analysis

## Development Phase Costs (MVP)

### Monthly Development Costs

| Item | Cost | Notes |
|------|------|-------|
| **Slack** | $0 | Free for development & testing workspaces |
| **OpenAI API (GPT-4o)** | ~$30-100/month | During dev/testing (usage-based) |
| **OpenAI Embeddings** | ~$5-15/month | text-embedding-3-small |
| **Pinecone** | $0 | Free tier (up to 100K vectors) |
| **Database (Dev)** | $0 | Local Docker PostgreSQL |
| **Redis (Dev)** | $0 | Local Docker Redis |
| **Domain** | ~$12/year | For OAuth redirect URL |

**Development Total: ~$35-120/month**

### One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| Slack App Directory listing | $0 | Free to list |
| Domain registration | ~$12 | Annual |
| SSL Certificate | $0 | AWS ACM (free with ALB) |

## Production Costs (AWS)

### Variable Costs Per Customer Workspace

#### Initial Onboarding (One-Time)

| Cost Type | Calculation | Estimate |
|-----------|-------------|----------|
| **Slack History Ingestion** | ~50K messages typical | API calls are free |
| **Embedding Generation** | 50K messages × ~100 tokens × $0.02/1M | ~$0.10-1.00 |
| **Initial Pinecone Upserts** | ~5K vectors per workspace | Included in plan |

**Total onboarding cost per customer: ~$1-5**

#### Monthly Operating Costs

| Cost Type | Calculation | Estimate |
|-----------|-------------|----------|
| **GPT-4o for Answers** | 500 questions × 2K tokens output × $10/1M | ~$10/month |
| **GPT-4o for Context** | 500 questions × 4K tokens input × $2.50/1M | ~$5/month |
| **Embedding Queries** | 500 queries × $0.02/1M | ~$0.01/month |
| **Pinecone Reads** | 500 queries | Included in plan |

**Monthly variable cost per customer: ~$15-25**

### Fixed Infrastructure Costs (AWS)

| Service | AWS Product | Monthly Cost |
|---------|-------------|--------------|
| **Compute** | ECS Fargate (0.5 vCPU, 1GB) | ~$15-30 |
| **Database** | RDS PostgreSQL (db.t4g.micro) | ~$15-25 |
| **Cache/Queue** | ElastiCache Redis (cache.t4g.micro) | ~$12-20 |
| **Vector Store** | Pinecone Serverless (Starter) | $0 (free tier) |
| | Pinecone Serverless (Standard) | ~$70 |
| **Load Balancer** | ALB | ~$16 |
| **Secrets** | Secrets Manager | ~$2 |
| **Monitoring** | CloudWatch (basic) | ~$5 |
| **Logging** | CloudWatch Logs | ~$3-5 |

**Minimum Production (free Pinecone): ~$70/month**
**Recommended Production (paid Pinecone): ~$140-170/month**

## Cost Projection Model

### Scaling Economics

```
┌─────────────────────────────────────────────────────────────┐
│                  MONTHLY COST PROJECTION                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Customers:        1       10       50       100            │
│  ─────────────────────────────────────────                  │
│  AWS Infra:        $140    $140     $250     $400           │
│  LLM (GPT-4o):     $15     $150     $750     $1,500        │
│  Embeddings:       $1      $5       $25      $50            │
│  Pinecone:         $0      $70      $70      $70            │
│  ─────────────────────────────────────────                  │
│  TOTAL:            $156    $365     $1,095   $2,020         │
│  Per Customer:     $156    $36.5    $21.9    $20.2          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Break-Even Analysis

| Pricing | Break-Even Customers | Notes |
|---------|---------------------|-------|
| $29/month | 6-7 customers | Tight margin |
| $49/month | 3-4 customers | Healthy margin |
| $99/month | 2 customers | Good margin, premium positioning |
| $199/month | 1 customer | Enterprise pricing |

## Pricing Strategy Recommendations

### Suggested Pricing Tiers

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| **Starter** | $49/month | 50 users, 500 questions/month | Small startups |
| **Growth** | $99/month | 100 users, 2000 questions/month | Growing teams |
| **Enterprise** | Custom | Unlimited, SLA, dedicated support | Large companies |

### Margin Analysis (at $49/month)

```
Revenue per customer:      $49
├── LLM costs:            -$15
├── Embedding costs:      -$1
├── Infrastructure share: -$7  (at 20 customers)
├── Payment processing:   -$1.5 (3%)
└── Gross Margin:         $24.5 (50%)
```

## Cost Optimization Strategies

### LLM Cost Reduction

| Strategy | Potential Savings | Trade-off |
|----------|------------------|-----------|
| Response caching | 20-40% | May serve stale answers |
| Shorter context windows | 30-50% | Reduced answer quality |
| Use GPT-4o-mini for simple Qs | 50-70% | Requires classification |
| Batch embedding generation | 10-20% | Delayed processing |

### AWS Infrastructure Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Use Fargate Spot for workers | 50-70% | Interruption risk for async tasks |
| RDS reserved instances (1yr) | 30-40% | Upfront commitment |
| ElastiCache reserved nodes | 30-40% | Upfront commitment |
| Right-size after load testing | 10-30% | Monitor before committing |

## API Pricing Reference (as of 2025)

### OpenAI GPT-4o

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4o | $2.50 | $10 |
| GPT-4o-mini | $0.15 | $0.60 |

### OpenAI Embeddings

| Model | Price (per 1M tokens) |
|-------|----------------------|
| text-embedding-3-small | $0.02 |
| text-embedding-3-large | $0.13 |

### Pinecone Serverless

| Tier | Monthly Cost | Vectors |
|------|-------------|---------|
| Free (Starter) | $0 | Up to 100K |
| Standard | ~$70 | 1M+ |

## Financial Projections (Year 1)

### Conservative Scenario

```
Month 1-3:   Development, 0 paying customers    = -$400
Month 4-6:   Launch, 5 customers × $49         = +$65/month
Month 7-9:   Growth, 15 customers × $49        = +$435/month
Month 10-12: Scale, 30 customers × $49         = +$970/month

Year 1 Total Revenue: ~$8,000
Year 1 Total Costs:   ~$5,500
Year 1 Profit:        ~$2,500
```

### Optimistic Scenario

```
Month 1-2:   Development                        = -$250
Month 3-6:   Launch, 10 customers × $49        = +$190/month
Month 7-9:   Growth, 40 customers × $49        = +$1,360/month
Month 10-12: Scale, 80 customers × $49         = +$3,120/month

Year 1 Total Revenue: ~$25,000
Year 1 Total Costs:   ~$10,000
Year 1 Profit:        ~$15,000
```

## Cost Monitoring

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Cost per question | < $0.04 | > $0.06 |
| LLM cost per customer | < $15/month | > $25/month |
| Infrastructure cost ratio | < 25% of revenue | > 35% |
| Gross margin | > 50% | < 40% |

### Monitoring Tools

- **LLM costs:** OpenAI usage dashboard
- **Infrastructure:** AWS Cost Explorer + billing alerts
- **Pinecone:** Pinecone console metrics
- **Overall:** Custom dashboard tracking all costs
