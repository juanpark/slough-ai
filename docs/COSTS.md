# Slough.ai Cost Analysis

## Development Phase Costs (MVP)

### Monthly Development Costs

| Item | Cost | Notes |
|------|------|-------|
| **Slack** | $0 | Free for development & testing workspaces |
| **OpenAI API (GPT-4o)** | ~$30-100/month | During dev/testing (usage-based) |
| **OpenAI Embeddings** | ~$5-15/month | text-embedding-3-small |
| **Database (Dev)** | $0 | Local Docker PostgreSQL + pgvector |
| **Redis (Dev)** | $0 | Local Docker Redis |
| **Domain** | ~$12/year | For OAuth redirect URL |

**Development Total: ~$35-120/month**

### One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| Slack App Directory listing | $0 | Free to list |
| Domain registration | ~$12 | Annual |
| SSL Certificate | $0 | AWS ACM (free with CloudFront/ALB) |

## Production Costs (AWS)

### Variable Costs Per Customer Workspace

#### Initial Onboarding (One-Time)

| Cost Type | Calculation | Estimate |
|-----------|-------------|----------|
| **Slack History Ingestion** | ~50K messages typical | API calls are free |
| **Embedding Generation** | 50K messages x ~100 tokens x $0.02/1M | ~$0.10-1.00 |
| **Persona Extraction** | 1 GPT-4o-mini call (~2K tokens) | ~$0.001 |
| **pgvector Storage** | ~5K vectors per workspace | Included in RDS |

**Total onboarding cost per customer: ~$1-5**

#### Monthly Operating Costs

| Cost Type | Calculation | Estimate |
|-----------|-------------|----------|
| **GPT-4o for Answers** | 500 questions x 2K tokens output x $10/1M | ~$10/month |
| **GPT-4o for Context** | 500 questions x 4K tokens input x $2.50/1M | ~$5/month |
| **GPT-4o-mini (Memory)** | Summarization calls | ~$0.50/month |
| **Embedding Queries** | 500 queries x $0.02/1M | ~$0.01/month |

**Monthly variable cost per customer: ~$15-25**

### Fixed Infrastructure Costs (AWS)

| Service | AWS Product | Monthly Cost |
|---------|-------------|--------------|
| **Compute** | ECS Fargate (3 services, 0.5 vCPU, 1GB each) | ~$45-90 |
| **Database** | RDS PostgreSQL + pgvector (db.t4g.micro) | ~$15-25 |
| **Cache/Queue** | ElastiCache Redis (cache.t4g.micro) | ~$12-20 |
| **Load Balancer** | ALB | ~$16 |
| **CDN** | CloudFront | ~$1-5 |
| **Monitoring** | CloudWatch (basic) | ~$5 |
| **Logging** | CloudWatch Logs | ~$3-5 |
| **Container Registry** | ECR | ~$1 |

**Minimum Production: ~$100-170/month**

Note: pgvector eliminates the need for a separate vector database service. All embeddings are stored in the same RDS instance, reducing costs compared to dedicated vector DB solutions.

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
│  LLM (4o-mini):    $1      $5       $25      $50           │
│  Embeddings:       $1      $5       $25      $50            │
│  ─────────────────────────────────────────                  │
│  TOTAL:            $157    $300     $1,050   $2,000         │
│  Per Customer:     $157    $30      $21      $20            │
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
├── LLM costs:            -$16
├── Embedding costs:      -$1
├── Infrastructure share: -$7  (at 20 customers)
├── Payment processing:   -$1.5 (3%)
└── Gross Margin:         $23.5 (48%)
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

### pgvector vs Dedicated Vector DB

| Factor | pgvector | Dedicated (e.g., Pinecone) |
|--------|----------|---------------------------|
| Monthly cost | $0 (included in RDS) | $0-70+ |
| Operational overhead | Low (same DB) | Medium (separate service) |
| Scale limit | ~1M vectors per table | Higher |
| Features | Basic similarity search | Advanced filtering, metadata |

For MVP and early scaling, pgvector is the more cost-effective choice.

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

## Cost Monitoring

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Cost per question | < $0.04 | > $0.06 |
| LLM cost per customer | < $16/month | > $25/month |
| Infrastructure cost ratio | < 25% of revenue | > 35% |
| Gross margin | > 48% | < 40% |

### Monitoring Tools

- **LLM costs:** OpenAI usage dashboard
- **Infrastructure:** AWS Cost Explorer + billing alerts
- **Overall:** Custom dashboard tracking all costs
