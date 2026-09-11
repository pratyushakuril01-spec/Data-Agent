# ⚡ SPECTER.AI — Autonomous Ghost Subscription & Spend Leak Forensic Agent
> **Hunt down phantom recurring charges, unmask stealth price hikes, and recover leaked cash with LangGraph Deep ReAct, E2B Code Interpreter Sandbox, and OpenRouter Multi-Model Routing.**

---

## 🌟 What is SPECTER.AI?
**SPECTER.AI** is an autonomous financial forensic agent designed to eliminate recurring cash leaks on personal and business credit cards:
- **Phantom Recurring Charges**: Forgotten SaaS subscriptions, gym memberships, and streaming accounts draining cash monthly.
- **Stealth / Silent Price Hikes**: Services that silently increase their monthly rates by 20%–50% without affirmative opt-in consent.
- **Trial Rollover Traps**: \$1.00 nominal trial authorizations that silently convert into full-priced annual commitments.

---

## 🏛️ Autonomous ReAct Architecture

```
                     ┌────────────────────────────────┐
                     │   Raw Statement (CSV / PDF)    │
                     └───────────────┬────────────────┘
                                     │
                                     ▼
                     ┌────────────────────────────────┐
                     │   SPECTER LangGraph ReAct      │
                     │  (StateGraph + OpenRouter LLM) │
                     └───────────────┬────────────────┘
                                     │ Thought / Action
                                     ▼
            ┌─────────────────────────────────────────────────┐
            │         E2B Code Interpreter Sandbox            │
            │  • Python/Pandas periodicity analysis           │
            │  • Chronological price hike delta detection     │
            │  • Cryptic merchant descriptor normalization    │
            └────────────────────────┬────────────────────────┘
                                     │ Observation
                                     ▼
                     ┌────────────────────────────────┐
                     │    Forensic Command Center     │
                     │  • Cyberpunk spend charts      │
                     │  • Kill-Switch savings counter │
                     │  • 1-Click FTC cancellation    │
                     │  • Price hike dispute letters  │
                     └────────────────────────────────┘
```

---

## 🚀 Key Features

1. **Multi-Bank Statement Parser**: Auto-ingests exports from Chase, Amex, BofA, Capital One, Citi, and generic banks.
2. **Cryptic Descriptor Unmasker**: Maps lines like `AMZN DIG*2948 866-216-1072 WA` $\rightarrow$ `Amazon Prime`.
3. **E2B Code Interpreter Sandbox**: Executes Python data analysis in an isolated cloud environment.
4. **LangGraph Deep ReAct**: Full step-by-step reasoning trace (`Thought` $\rightarrow$ `Action` $\rightarrow$ `Observation`).
5. **Interactive Kill-Switch**: Mark services for cancellation to see live **Annual Cash Recovered** counter.
6. **FTC "Click-to-Cancel" & State ARL Letter Engine**: Generates ready-to-send dispute emails demanding refunds for unnotified price increases.

---

## 🛠️ Quickstart

### 1. Launch the Server
```bash
streamlit run app.py
```
Open [**http://localhost:8501**](http://localhost:8501) in your browser.

### 2. Configure Keys ([`.env`](file:///c:/Users/lenovo/Desktop/Ghost%20Audit%20Agent/.env))
```env
OPENROUTER_API_KEY=your_key_here
E2B_API_KEY=your_key_here
```

### 3. Headless CLI Run
```bash
python cli.py --statement sample_data/personal_chase_sample.csv --draft-email "Netflix"
```
