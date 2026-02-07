# Slough.ai MVP Feature Specification

> Source: Slough.ai MVP 상세 기능 명세서 & 서비스 설명 문서

## 1. Overview

### 1.1 MVP Scope

- **Single Mode:** "Auto Mode" only (no mode switching)
- **Core Interaction:** 1:1 DM between team members and bot
- **Feedback Loop:** Team members can request decision-maker review on specific answers
- **Excluded Features:** Channel mentions, decision-maker dashboard, automatic mode switching

### 1.2 Core Value Proposition

Slough.ai learns from the decision-maker's entire Slack conversation history and provides answers reflecting the decision-maker's thinking style. The core problem isn't question volume — it's that decision-maker reasoning isn't reusable within organizational structures.

**Key Differentiators:**
- No document upload, interviews, or prompt design required
- No setup/tuning hurdles
- Slack install + full channel learning consent = immediate use
- Raw data (entire Slack conversation) learning
- One company = One dedicated AI

**Tagline:** "슬러프는 당신의 생각과 논리로 또 다른 당신을 만듭니다"

**Core Statement:** "저는 의사결정자의 Slack 대화를 학습하여, 의사결정자의 사고 방식을 반영한 답변을 제공합니다."

### 1.3 Three-Stage Process

1. **Learning** — Analyzes all Slack conversations in channels the decision-maker authorizes
2. **Persona Development** — Develops a company-specific persona reflecting the leader's thinking
3. **Response Delivery** — Employees query Slough.ai in Slack; it provides answers reflecting the decision-maker's reasoning

## 2. User Roles

| Role | Definition | Permissions |
|------|------------|-------------|
| **의사결정자 (Admin/Decision-Maker)** | Installs bot, subject of persona learning | Install bot, grant data access, review answers, provide feedback, declare rules |
| **팀원 (User/Employee)** | General user who asks questions | Ask questions via DM, request decision-maker review |

## 3. Feature Specifications

### F-01: Onboarding & Data Learning

**User Story:** Decision-maker installs the bot easily, and the bot safely collects all Slack conversation data needed for persona learning.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-01.1 | Bot Installation | Decision-maker finds 'Slough.ai' in Slack App Directory, clicks 'Add to Slack'. OAuth consent screen appears. |
| FR-01.2 | Permission Consent | OAuth screen clearly states bot will use decision-maker's User Token to access data. |
| FR-01.3 | Initial Data Collection | Upon permission grant, system uses issued User Token to collect message history from all authorized channels for learning. |
| FR-01.4 | Onboarding Complete Notification | When data collection and initial learning complete, bot sends welcome DM: "✅ 초기 학습이 완료되었습니다. 이제 팀원들이 저에게 질문하여 의사결정자의 판단을 요청할 수 있습니다." |

### F-02: Q&A (Team Member)

**User Story:** Team members ask questions via DM with the bot and receive AI-generated answers immediately.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-02.1 | Question | Team member sends 1:1 DM question to bot via App Home > Messages tab. |
| FR-02.2 | AI Answer Generation | System analyzes question intent and generates answer based on learned decision-maker persona data. |
| FR-02.3 | Answer Delivery | Generated answer sent immediately to team member's DM. |
| FR-02.4 | Answer Message Structure | Body: AI-generated answer text / Warning: "⚠️ AI가 생성한 응답이며, 오류가 있을 수 있습니다." / Action Button: [🔍 검토 요청] |

### F-03: Feedback Loop (Review Request)

**User Story:** When team members find AI answers uncertain or important, they press 'Review Request' to send to decision-maker for confirmation.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-03.1 | Review Request | Team member clicks [🔍 검토 요청] button on answer message. |
| FR-03.2 | Decision-Maker Notification | Immediately upon click, bot sends review request notification to decision-maker's DM. Content: requester, original question, AI answer, feedback buttons. Buttons: [✅ 문제 없음], [❌ 틀림], [✏️ 직접 수정], [⚠️ 판단 시 주의 필요] |
| FR-03.3 | Feedback (No Problem) | Decision-maker clicks [✅ 문제 없음]: AI answer considered correct. System saves (question, answer) pair as positive learning data. Notifies original requester: "✅ 확인이 완료되었습니다." |
| FR-03.4 | Feedback (Wrong) | Decision-maker clicks [❌ 틀림]: AI answer considered completely wrong. System saves answer as negative learning data. Notifies requester: "❌ 해당 답변이 틀렸다고 판단되었습니다. 직접 문의해 주세요." |
| FR-03.5 | Feedback (Direct Edit) | Decision-maker clicks [✏️ 직접 수정]: Modal opens for answer editing. Upon submission, system saves (question, corrected answer) as ground truth. Delivers corrected answer to requester: "✅ 내용을 수정하여 전달했습니다." |
| FR-03.6 | Feedback (Use Caution) | Decision-maker clicks [⚠️ 판단 시 주의 필요]: AI answer partially correct but needs caution. System saves (question, answer, caution flag) and learns to generate more careful answers for similar questions. Notifies requester: "⚠️ 이 답변은 신중하게 판단하라는 의견입니다." |

### F-04: Safety Measures

**User Story:** Users recognize AI limitations, and system provides appropriate warnings for potentially risky topics to minimize risk.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-04.1 | AI Disclaimer | All AI answer messages must include at bottom: "⚠️ AI가 생성한 응답이며, 오류가 있을 수 있습니다." |
| FR-04.2 | High-Risk Keyword Detection | System maintains predefined high-risk keyword list (e.g., 계약, 해고, 투자, 법적, 소송, 퇴사, 연봉). When question contains these keywords, add warning to answer: "⚠️ [주의] 이 주제는 민감하므로, 직접 확인하시는 것을 권장합니다." |

### F-04.3: Prohibited Domains

The following topics are explicitly out of scope for AI responses:
- Legal determinations and final decision-making
- Contracts, terminations, investments, litigation
- Compensation and resignation decisions
- Interpersonal/non-business advice

### F-05: Decision-Maker Rule Declaration

**User Story:** Decision-maker wants to set explicit 'rules' for AI to follow or behave differently in specific situations, directly controlling AI behavior. Rules take precedence over learned patterns.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-05.1 | Rule Declaration | Decision-maker uses slash command `/rule` in DM with bot. Command: `/rule add "[rule content]"`. Example: `/rule add "100만원 이상의 지출은 무조건 나에게 확인"` |
| FR-05.2 | Rule Management | `/rule list`: View all currently set rules. `/rule delete [ID]`: Delete specific rule. |
| FR-05.3 | Rule Application | When generating answers, AI first checks question against registered rules. If rule condition matches, execute rule-defined action with highest priority instead of persona-based answer. |

### F-06: Weekly Reminder

**User Story:** Decision-maker receives weekly bot activity summary to easily understand AI performance and team question trends.

| ID | Requirement | Details |
|----|-------------|---------|
| FR-06.1 | Periodic Delivery | System automatically generates and sends weekly report to decision-maker's DM every Monday at 10 AM. |
| FR-06.2 | Report Content | Aggregates last 7 days (Mon-Sun) data: Total questions, Review requests, feedback completed. |
| FR-06.3 | Report Message | Summary text based on numerical data, plus action button [검토 요청 내역 보기]. |

## 4. UI Specifications

### 4.1 Team Member → Bot DM (Q&A)

**Normal AI Answer:**
```
버그 수정 B를 먼저 진행하세요.

이유:
1. 현재 고객 불만이 접수된 상태입니다.
2. 신규 기능은 다음 스프린트에 포함해도 일정에 문제 없습니다.
──────────────────
⚠️ AI가 생성한 응답이며, 오류가 있을 수 있습니다.

[🔍 검토 요청]
```

**High-Risk Keyword Detected:**
```
해당 계약 조건은 진행해도 괜찮습니다.
──────────────────
⚠️ AI가 생성한 응답이며, 오류가 있을 수 있습니다.
⚠️ [주의] 이 주제는 민감하므로, 직접 확인하시는 것을 권장합니다.

[🔍 검토 요청]
```

### 4.2 Decision-Maker DM (Review Request Notification)

```
🔔 김개발님이 검토를 요청했습니다

❓ 질문:
신규 기능 A와 버그 수정 B 중에 뭘 먼저 해야 할까요?

🤖 AI 응답:
"버그 수정 B를 먼저 진행하세요. 이유: 1. 현재 고객 불만이 접수된 상태..."

[✅ 문제 없음] [❌ 틀림] [✏️ 직접 수정] [⚠️ 판단 시 주의 필요]
```

### 4.3 Decision-Maker DM (Rule List)

```
📜 현재 적용 중인 법칙 목록입니다.

[ID: 1]: "100만원 이상의 지출은 무조건 나에게 확인"
[ID: 2]: "모든 채용 관련 질문은 인사팀장에게 먼저 전달"

(삭제하시려면 /rule delete [ID]를 입력하세요)
```

### 4.4 Decision-Maker DM (Weekly Reminder)

```
📊 주간 Slough.ai 리포트 (2026.01.25 ~ 2026.01.31)

- 총 질문 수: 47건
- 검토 요청 수: 5건
- 피드백 완료: 4건

이번 주에는 주로 신규 기능 개발 우선순위에 대한 질문이 많았습니다.

[검토 요청 내역 보기]
```

## 5. Non-Functional Requirements

| Item | Requirement |
|------|-------------|
| Response Speed | AI answer within 10 seconds of team member question |
| Data Security | User Token and all message data encrypted at rest (important as corporate content) |
| Scalability | Support up to 100 users per workspace |
| Data Retention | Learning data and QA records retained minimum 6 months |

## 6. Decision Boundaries (Critical Constraints)

**❌ Bot does NOT make final decisions**
**❌ Bot does NOT assume legal/financial responsibility**
**⭕ Answers are always for reference only**

### Disclaimer Statement
> "이 답변은 참고용이며, 법적·재무적·운영상 책임을 대체하지 않습니다."

### Prohibited Domains
- Legal determinations, final decision-making
- Contracts, terminations, investments, litigation, compensation, resignations
- Interpersonal/non-business advice
- Perfect judgment is not the objective

## 7. Service Identity Statement

**Core Statement (for App Home, first DM, first question):**
> "저는 의사결정자의 Slack 대화를 학습하여, 의사결정자의 사고 방식을 반영한 답변을 제공합니다."

**Intent:**
- Clearly communicates persona replication value without exaggeration
- Clear differentiation without legal/ethical risk
- Clear scope for developers

## 8. Target Audience

### Suitable For
- Teams with substantial Slack activity and rich conversation history
- Organizations with clear decision-making frameworks
- Smaller organizational structures
- Startups requiring thought-alignment between executives and staff

### Not Suitable For
- Very large organizations
- Low-Slack-usage teams
- Environments requiring legal/financial AI liability
