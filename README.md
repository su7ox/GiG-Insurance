# GigInsurance — AI-Powered Parametric Income Insurance for Gig Workers

> **Persona:** Grocery & Q-Commerce Delivery Partners (Zepto / Blinkit)
> **Interface:** WhatsApp — no app download required



## 🔍 Problem Statement

India's Q-Commerce delivery partners (Zepto, Blinkit etc.) are the backbone of the hyperlocal delivery economy. These gig workers operate in high-frequency, outdoor environments and are uniquely vulnerable to external disruptions — extreme weather, flooding, and curfews/Section 144 orders — that directly cut into their daily earnings.

**Key pain points:**
- Gig workers can lose **20–30% of monthly income** during disruption events
- No existing income safety net is tailored to their week-to-week earning cycle
- Traditional insurance products are too slow, too complex, and don't cover income loss parametrically
- Workers bear the full financial burden with zero compensation when they cannot work through no fault of their own

> **Coverage Scope:** This platform exclusively covers **Loss of Income**. It does NOT cover health, life, accidents, vehicle repairs, or medical bills.

---

## 💡 Our Solution

**GigInsurance** is an AI-enabled, fully automated parametric income insurance platform built exclusively for Q-Commerce delivery partners. It:

- Operates entirely over **WhatsApp** — no app download, no login screens, no custom UI. Workers register, file claims, and receive payouts all through a familiar chat interface.
- Operates on a transparent B2B2C **"Weekly Premium Model"** where gig platforms cover a fixed Base Fee, while workers pay a dynamic, risk-adjusted premium calculated by an **XGBoost AI model** based on their specific zone's environmental risk factors.
- Workers simply describe **what happened and when** in plain text — an **Agentic AI Claim Processor** takes it from there, autonomously deciding which tools to call (weather APIs, shift records, policy rules, fraud history) to verify and approve the claim.
- **Utilizes an internal Multi-RAG pipeline** as agent tools — retrieving dynamic policy rules and historical context mid-reasoning, not as a static pre-fetch.
- **Deploys Generative AI** to synthesize complex math and policy terms into clear, localized **"Smart Receipts"** so workers understand exactly why a payout was approved or denied.
- Uses strict database indexing and platform-verified data to prevent fraud at the source, ensuring **zero AI hallucinations** on financial decisions.

---

## 👤 Persona & Scenarios

**Primary Persona:** Rahul, a Zepto delivery partner in Noida
- Works 8–10 hours/day, 6 days/week
- Earns approximately ₹600–₹900/day
- Operates across 3–4 delivery zones in his area

### Scenario A — Heavy Rain Event
> Rahul sends a WhatsApp message: *"It was raining heavily, couldn't deliver from 2PM to 4PM."* The Claim Agent classifies the disruption as Heavy Rain, calls the weather API (85mm recorded ✅), verifies his active shift via platform telemetry ✅, fetches the Tier-1 policy threshold via RAG (>50mm ✅), runs the payout math, and replies with a localized Smart Receipt confirming ₹280 credited to his wallet — all within minutes, directly in chat.

### Scenario B — Curfew / Section 144
> Rahul sends a WhatsApp message: *"Police stopped all movement near my area around 6PM, had to stop working."* The Claim Agent identifies this as a Curfew/Section 144 event, queries the government news feed to confirm the order ✅, verifies Rahul was logged in at 6PM ✅, and replies in Hindi with a Smart Receipt detailing the payout proportional to his remaining shift hours.

---

## 🔄 Application Workflow

```
Worker sends WhatsApp message to GigInsurance Bot
(text, voice note, button tap, or list selection — in any language)
       │
       ▼
WhatsApp API (Meta / Twilio) → FastAPI Webhook Receiver
       │
  [New user?]
       │
      YES ──► Conversational Onboarding Flow
       │          ├─ Bot sends Interactive Buttons → Platform Selection
       │          ├─ Bot prompts → Partner ID input → validated vs mock DB
       │          └─ Bot requests linked phone number → OTP issued over chat → verified → session bound
       │
      NO  ──► Session validated
       │          └─ Deleting/clearing the chat = automatic logout
       │             (returning worker must re-verify phone number + OTP before regaining access)
       │
       ▼
Worker describes disruption in plain text, voice, or via quick-reply buttons/lists
(cause + approximate time — that's it)
       │
       ▼
🤖 Agentic AI Claim Processor (LangGraph)
  │
  ├── Step 1: Classify disruption type from natural language
  │
  ├── Step 2: Autonomously call relevant tools —
  │      ├─ verify_active_shift()       → Platform Telemetry
  │      ├─ check_weather_api()         → Rainfall / Temp / AQI
  │      ├─ check_government_feed()     → Curfew alerts
  │      ├─ query_policy_rag()          → Policy RAG (threshold rules)
  │      ├─ check_fraud_history()       → Historical Context RAG
  │      └─ flag_for_manual_review()    → Escalation (if anomaly)
  │
  ├── Step 3: Tabular ML Engine (deterministic math)
  │      ├─ XGBoost (payout calculation)
  │      └─ Isolation Forest (anomaly scoring)
  │
  └── Step 4: Final decision — Approved / Denied / Escalated
       │
       ▼
LLM Synthesis → Localized Smart Receipt (text, worker's language)
       │
       ▼
Instant Wallet Credit (Razorpay / UPI)
       │
       ▼
Smart Receipt delivered as WhatsApp message
```

---

## 💰 Weekly Premium Model

Our pricing system dynamically calculates a weekly insurance premium based on real-world risk factors. Unlike flat-fee models, GigShield uses AI-driven risk scoring to ensure fair, location-aware pricing.

### Core Formula

```
Weekly Premium = Base Fee + [Σ (Pᵢ × Max Payout × Sᵢ)] × (1 + M)
```

| Variable | Description |
|----------|-------------|
| `Pᵢ` | Probability of disruption event *i* (from AI model) |
| `Sᵢ` | Severity weight of event *i* |
| `Max Payout` | Maximum daily payout cap — ₹500 |
| `M` | Solvency margin — 10% |
| `Base Fee` | ₹20/week, covered by the platform (B2B2C) |

### Premium Tiers

| Risk Level | Risk Score (R) | Estimated Weekly Premium |
|------------|---------------|--------------------------|
| Low Risk | 0.1 – 0.3 | ₹30 – ₹60 |
| Medium Risk | 0.4 – 0.6 | ₹80 – ₹120 |
| High Risk | 0.7 – 1.0 | ₹120+ |

### B2B2C Cost Split

- **Platform (Zepto / Blinkit):** Pays base fee (~₹20/week/worker) — ensures operational sustainability
- **Worker:** Pays only the risk-adjusted premium on top — keeps pricing affordable

---

## ⚡ Parametric Triggers

Workers simply describe what happened and roughly when. The **Claim Agent classifies the disruption type** from their natural language input and autonomously calls the relevant data source to verify it. Supported trigger types:

| Trigger Type | Event | Data Source |
|---|---|---|
| 🌧️ Environmental | Heavy Rain (>50mm/6hr) | Weather API |
| 🌊 Environmental | Flood / Waterlogging | Government / Geospatial API |
| 🌡️ Environmental | Extreme Heat (>45°C) | Weather API |
| 😷 Environmental | Severe AQI (>300) | Pollution Monitoring API |
| 🌀 Environmental | Cyclone / Storm Warning | IMD API |
| 🚫 Social | Curfew / Section 144 | News / Government Feed |

Each trigger is validated against:
- Worker's active GPS zone
- Platform-confirmed login/shift activity
- Cross-referenced disruption duration

---

## 🤖 AI/ML Integration

The core of GigInsurance is an **Agentic AI Claim Processor** built on LangGraph. The agent receives the worker's plain-text description and autonomously reasons through verification — calling only the tools relevant to that specific disruption type, in the right order, without any hardcoded branching logic.

### 1. The Claim Agent (LangGraph)

The agent is given a fixed toolkit and decides at runtime which tools to invoke based on the disruption described.

**Agent Tools:**

| Tool | Purpose |
|---|---|
| `verify_active_shift()` | Confirms worker was logged in during the claimed window via platform telemetry |
| `check_weather_api()` | Fetches rainfall/temp/AQI for the worker's zone and time window |
| `check_government_feed()` | Checks news/government feeds for curfew orders |
| `query_policy_rag()` | RAG search over master insurance contracts to fetch the exact payout threshold for the worker's tier and vehicle type |
| `check_fraud_history()` | RAG search over past claim logs to detect semantic patterns, duplicate behaviour, or anomalous timing |
| `calculate_payout()` | Deterministic math — XGBoost + SLF + PHR formula |
| `flag_for_manual_review()` | Escalates to human reviewer if Isolation Forest anomaly score spikes |

**Key property:** A rain claim never calls `check_government_feed()`. A curfew claim never calls `check_weather_api()`. The agent selects only what's needed — making it efficient and auditable.

### 2. The RAG Pipelines (Agent Knowledge Tools)

RAG is used as **on-demand agent tools**, not static pre-fetches. This means retrieval happens mid-reasoning, with the worker's full claim context already available.

- **Policy RAG:** Vector search over chunked insurance contract PDFs. Filtered by worker tier, vehicle type, and disruption category — returns the exact threshold rule the agent needs to make its decision.
- **Historical Context RAG:** Semantic search over past claim text logs and support chats. Detects recurring patterns, duplicate claim language, or suspicious timing that pure anomaly detection (Isolation Forest) would miss.

### 3. The Tabular ML Engine (Deterministic Math)

All financial calculations are fully deterministic — the agent never lets the LLM guess a number.

- **XGBoost Risk Scoring:** Calculates dynamic weekly premium from historical tabular data (rainfall, temperature, traffic, zone history).
- **Fraud Detection (Isolation Forest):** Flags statistical anomalies — sudden claim density spikes, zone mismatches, or timing outliers — triggering the `flag_for_manual_review()` tool.
- **System Load Factor (SLF):** Scales payouts during mass disruptions to maintain financial solvency.

### 4. The LLM Synthesis Layer (The Communicator)

Once the agent completes verification and the math is finalized, the LLM's only job is communication — never decision-making.

- **Context Packet:** All agent tool outputs (policy rule retrieved, sensor readings, shift verification result, payout math) are injected into a single system prompt.
- **Localized Smart Receipt:** The LLM generates a conversational, structured receipt in the worker's language (Hindi, Marathi, Telugu) explaining exactly what was verified, what threshold was met, and how the final number was calculated.

---

## 🔐 Fraud Prevention

### Problem → Solution Matrix

| Fraud Vector | Detection Mechanism |
|---|---|
| GPS Spoofing / Fake Location | Zone matching via Platform API — not device GPS |
| Fake Shift Hours | Only platform-recorded activity counts — no manual input |
| Last-Minute Policy Purchase | **48–72 hour waiting period** before policy activates |
| Coordinated Mass Fraud | Anomaly detection flags unusual claim clusters |
| Duplicate Claims | De-duplication at the database layer (PostgreSQL constraints) |
| Unauthorized Zone Claims | Worker zone must match disruption zone exactly |

### System Load Factor (SLF)

During large-scale disruptions where many workers claim simultaneously, a **System Load Factor** smoothly scales individual payouts to maintain solvency:

```
SLF = 1 / (1 + α × C)
```

Where `C` = claim density (0–1) and `α` ≈ 0.5.

This prevents financial instability while remaining fair — no sudden or arbitrary cuts.

---

## 💸 Payout Engine

### Step-by-Step Calculation

**Step 1 — Protected Hourly Rate (PHR)**
```
PHR = (Premium / Risk Score) × k     [k ≈ 0.4]
```
Normalizes payout fairness across high-risk and low-risk zones.

**Step 2 — Effective Hours**
```
Effective Hours = Shift Window ∩ Disruption Window
```
Only hours where the worker's shift overlapped with the disruption count.

**Step 3 — Apply System Load Factor**
```
Adjusted Rate = PHR × SLF
```

**Step 4 — Final Payout**
```
Final Payout = min(Adjusted Rate × Effective Hours, ₹500)
```

**Payment Channel:** Razorpay (Test Mode) / UPI Simulator — credited to worker's in-app wallet within minutes of trigger verification.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Interface** | WhatsApp API (Meta / Twilio) | Worker-facing chat interface — onboarding, claims, receipts, alerts |
| **Webhook Server** | FastAPI (Python) | Receives WhatsApp messages, orchestrates the agent pipeline |
| **Agentic AI** | LangGraph + LangChain | Claim Agent — autonomous tool orchestration and reasoning |
| **AI / ML** | Python, XGBoost, Scikit-learn | Risk scoring, anomaly detection, payout calculation |
| **RAG / Vector DB** | ChromaDB + LangChain | Policy RAG and Historical Context RAG as agent tools |
| **Database** | PostgreSQL | Policies, payouts, worker sessions — structured financial records |
| **Cloud** | AWS / GCP | Backend hosting, scalable webhook deployment |
| **Weather Data** | OpenWeatherMap API / IMD (mock) | Rainfall, temperature, AQI for parametric verification |
| **Platform Data** | Zepto / Blinkit API (mock/simulated) | Worker verification, zone, shift data |
| **Payments** | Razorpay (Test Mode) / UPI Simulator | Instant payout to worker's linked wallet |
| **Auth** | WhatsApp session + OTP over chat | No JWT needed — session bound to WhatsApp account; deleting the chat resets the session and forces phone + OTP re-verification |
| **Notifications** | Native WhatsApp messages | Replaces Firebase push notifications entirely |
| **Admin Dashboard** | Web (React) | Insurer/ops-facing — loss ratios, manual review queue, analytics |

---

## 📱 Interface Choice — Why WhatsApp

**We replaced the dedicated mobile app entirely with a WhatsApp Bot** for the following reasons:

- **Zero install friction** — gig workers already have WhatsApp. No app store, no permissions, no onboarding drop-off.
- **Native voice input** — WhatsApp handles voice notes natively in Hindi, Marathi, and Telugu. No custom speech-to-text UI needed.
- **Native multilingual input** — workers type in their own language and WhatsApp handles it. No custom i18n components required.
- **Native notifications** — WhatsApp messages replace custom push notification infrastructure entirely.
- **Session security built-in** — deleting or clearing the chat thread functions as an automatic logout. On return, the backend resets the worker's session state and requires phone number + OTP re-verification before granting access again.
- **Dashboard replaced by conversation** — instead of charts, workers ask *"What is my active policy?"* or *"Show my claim history"* and receive a clean text summary instantly.

> **Admin / Insurer Dashboard** remains a separate web interface for analytics, loss ratios, and manual review queues — this is ops-facing, not worker-facing.

---

## 📅 Development Plan

### Phase 1 — Ideation & Foundation 
- [x] Persona definition and scenario mapping
- [x] Weekly premium model design
- [x] Parametric trigger selection and justification
- [x] Tech stack finalization
- [x] README and repository setup

### Phase 2 — Automation & Protection
- [ ] Worker registration and onboarding flow
- [ ] Insurance policy creation with weekly pricing
- [ ] Dynamic premium calculation engine (XGBoost model)
- [ ] Claims management module
- [ ] 3–5 automated disruption trigger integrations (mock APIs)
- [ ] Zero-touch claim initiation prototype

### Phase 3 — Scale & Optimise
- [ ] Advanced fraud detection (GPS spoofing, coordinated claims)
- [ ] Instant payout simulation (Razorpay test mode / UPI)
- [ ] Worker dashboard: earnings protected, active coverage
- [ ] Insurer/admin dashboard: loss ratios, predictive analytics


---

> *"We verify real work, prevent fake claims, and ensure fair payouts — even during large-scale disruptions."*

---
