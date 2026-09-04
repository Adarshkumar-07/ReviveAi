# ReviveAI

> **Recover the right revenue. Automatically. Safely. Measurably.**

ReviveAI is an AI-inspired revenue recovery operations agent for merchants. It detects failed revenue, diagnoses likely causes, estimates recovery probability, proposes an intervention, validates the intervention through deterministic policies, and records an auditable outcome.

## Razorpay AI Buildathon — Track 03: AI Revenue Recovery

### The problem
Failed payments are not all equally recoverable. Blind retries can create customer friction, waste attempts, and still miss high-value opportunities. Merchants need a system that answers three questions:

1. Which revenue is genuinely at risk?
2. What is the safest next intervention?
3. When should the system stop and escalate?

### What ReviveAI does

`DETECT → DIAGNOSE → PREDICT → DECIDE → VALIDATE → RECOVER → MEASURE → AUDIT`

- Revenue-at-risk identification
- Failure-cause diagnosis
- Recovery probability scoring
- Recommended recovery action
- Deterministic financial guardrails
- High-value human approval gate
- Retry/stopping rules
- Batch simulation and business metrics
- Explainable decision panel
- Audit-ready recovery events
- Baseline vs ReviveAI evaluation

## Architecture

```text
Payment / Merchant Events
          |
          v
   Risk & Context Engine
          |
          v
    AI Decision Layer
          |
          v
 Deterministic Policy Engine
     |              |
     v              v
 Auto Action     Human Approval
     |              |
     +-------> Execution Simulator
                    |
                    v
             Outcome + Audit Log
                    |
                    v
              Recovery Metrics
```

### Why the policy engine is separate

The AI layer can recommend an action, but it cannot bypass financial safety rules. Amount thresholds, retry limits, cooldowns, and escalation are deterministic. This keeps the prototype explainable and bounded.

## Demo

Run locally:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

The dashboard runs without paid APIs or API keys and includes deterministic synthetic transaction data. The **Run 500-event simulation** button produces a reproducible evaluation-style demo.

## API

- `GET /api/metrics` — current recovery metrics
- `GET /api/transactions?limit=30` — recovery queue
- `POST /api/simulate` — generate a new batch (`count` 50–5000)
- `POST /api/recover` — evaluate a recovery workflow against policy guardrails

## Evaluation methodology

The prototype compares a simple rule-based baseline with ReviveAI's policy-controlled recovery strategy. The dashboard reports:

- Revenue at risk
- AI-qualified recoverable revenue
- Revenue recovered
- Recovery rate
- Baseline recovery
- Recovery lift
- Autonomous actions
- Human approvals
- Safely stopped opportunities
- Policy violations

The included data is synthetic. Reported recovery amounts are **simulation results**, not production financial performance.

## Safety / limitations

- No real customer money is charged by this repository.
- The demo uses synthetic transaction data.
- Recovery execution is simulated unless separately connected to an authorized test environment.
- AI recommendations are constrained by deterministic policy rules.
- Production deployment would require merchant authorization, secure secrets management, idempotency, rate limits, observability, compliance review, and Razorpay-approved integration patterns.

## Tech stack

- Python / Flask
- Vanilla JavaScript
- HTML / CSS
- Gunicorn for deployment
- No database required for the demo
- No paid API required

## Buildathon positioning

ReviveAI is designed around measurable financial outcomes rather than chatbot activity. Its central KPI is **revenue recovered**, while its safety model makes every automated action bounded, explainable, and auditable.

## License

MIT
