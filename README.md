<div align="center">

# 🧠 Qognition

### AI-Powered QA Automation — The Future of Testing

> *The QA engineer no longer writes tests. They review and curate them.*

[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://reactjs.org)
[![Spring Boot](https://img.shields.io/badge/Backend-Spring%20Boot-6DB33F?logo=springboot)](https://spring.io)
[![Playwright](https://img.shields.io/badge/E2E-Playwright-45ba4b?logo=playwright)](https://playwright.dev)
[![REST Assured](https://img.shields.io/badge/API-REST%20Assured-4A90E2)](https://rest-assured.io)
[![Gemini](https://img.shields.io/badge/AI-Gemini%20CLI-4285F4?logo=google)](https://ai.google.dev)
[![Claude](https://img.shields.io/badge/AI-Claude%20CLI-D97757?logo=anthropic)](https://anthropic.com)
[![ReportPortal](https://img.shields.io/badge/Reports-ReportPortal-9B59B6)](https://reportportal.io)

</div>

---

## 🎯 What is Qognition?

Qognition is a proof-of-concept that demonstrates how the QA automation
landscape is being transformed by AI. Instead of manually writing test cases,
Qognition watches for code changes across repositories, reads the actual diff,
and automatically generates and executes tests — all powered by AI.

### The Core Loop
Developer pushes a change
↓
Qognition reads the actual diff (not just filenames)
↓
AI generates tests based on real code changes
↓
Tests execute — stable suite + newly generated
↓
Results reported to terminal + JSON + ReportPortal

---

## 🏗️ Architecture
```
┌──────────────────────────────────────────────────────┐
│                    qognition-core                    │
│                  (Automation Brain)                  │
│                                                      │
│  fetch_diff.sh ──► generate_tests.py ──► run_tests.py│
│       │                  │                   │       │
│  Actual Diff         AI CLI              Playwright  │
│  + Content        (Gemini/Claude)      REST Assured  │
│       │                  │                   │       │
│  diff_summary       tests/             ReportPortal  │
│     .json          generated/           + JSON       │
│                    stable/                           │
│                    archive/                          │
└──────┬──────────────────────────────────────┬────────┘
       │                                      │
       ▼                                      ▼
┌─────────────┐                     ┌─────────────────┐
│qognition-ui │                     │ qognition-api   │
│   React     │◄────── Tests ──────►│  Spring Boot    │
│  Port 3000  │                     │   Port 8080     │
└─────────────┘                     └─────────────────┘
```

### Repositories

| Repo | Tech | Role |
|------|------|------|
| `qognition-ui` | React + TypeScript | Frontend — subject under test |
| `qognition-api` | Spring Boot + Java | Backend — subject under test |
| `qognition-core` | Python + Shell | Automation brain |

---

## ⚡ Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | >= 18 | [nodejs.org](https://nodejs.org) |
| Java | >= 17 | [adoptium.net](https://adoptium.net) |
| Maven | >= 3.9 | [maven.apache.org](https://maven.apache.org) |
| Python | >= 3.9 | [python.org](https://python.org) |
| Docker | latest | [docker.com](https://docker.com) |
| Gemini CLI | latest | `npm install -g @google/gemini-cli` |
| Claude CLI | latest | `npm install -g @anthropic-ai/claude-cli` |

### 1. Clone all three repos

```bash
git clone https://github.com/chhatbarjignesh/qognition-ui
git clone https://github.com/chhatbarjignesh/qognition-api
git clone https://github.com/chhatbarjignesh/qognition-core
```

### 2. Setup qognition-core

```bash
cd qognition-core

# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install python-dotenv

# Node dependencies + Playwright browsers
npm install
npx playwright install --with-deps

# Configure credentials
cp .env.example .env
# Edit .env with your ReportPortal details
```

### 3. Start the stack

```bash
docker compose up -d
sleep 20

# Verify both services are healthy
curl http://localhost:8080/actuator/health   # → {"status":"UP"}
curl http://localhost:3000                  # → React app
```

---

## 🚀 Running the Full Pipeline

### Option A — Step by step

```bash
# Step 1: Detect what changed (reads actual diff content)
./scripts/fetch_diff.sh feature/my-branch master

# Step 2: Generate tests with AI
python3 scripts/generate_tests.py          # interactive provider selection
python3 scripts/generate_tests.py gemini   # or pass directly
python3 scripts/generate_tests.py claude

# Step 3: Execute tests (stable + generated)
python3 scripts/run_tests.py all           # all tests
python3 scripts/run_tests.py frontend      # Playwright only
python3 scripts/run_tests.py backend       # REST Assured only
```

### Option B — One liner

```bash
./scripts/fetch_diff.sh feature/my-branch master && \
python3 scripts/generate_tests.py gemini && \
python3 scripts/run_tests.py all
```

---

## 🤖 AI Providers

Qognition supports multiple AI providers for test generation.
Switch between them to demonstrate provider-agnostic test generation.

| Provider | CLI | Install |
|----------|-----|---------|
| Google Gemini | `gemini` | `npm install -g @google/gemini-cli` |
| Anthropic Claude | `claude` | `npm install -g @anthropic-ai/claude-cli` |
Interactive selection
python3 scripts/generate_tests.py
╔══════════════════════════════════════╗
║       qognition test generator       ║
╚══════════════════════════════════════╝
Select AI provider:
[1] gemini     — Google Gemini CLI
[2] claude     — Anthropic Claude CLI
Enter number or name (default: gemini):

The provider used is recorded in `tests/generated/generation_summary.json`
for traceability.

---

## 🧠 Diff-Aware Test Generation

Unlike basic filename-based generation, Qognition passes the **actual diff
content** to the AI — line by line changes, new code, modified logic.
Before (filename only):
"src/main/java/.../UserController.java changed"
→ AI guesses what to test
After (diff-aware):

@GetMapping("/users/{id}")
public ResponseEntity<User> getUserById(@PathVariable Long id) { ... }
→ AI generates: getUserById_WhenUserExists_Returns200()
→ AI generates: getUserById_WhenNotFound_Returns404()


This means tests are specific, accurate and reflect real implementation
details — not generic guesses.

---

## 📂 Test Structure

Qognition organises tests into three tiers:
tests/
stable/               ← Curated tests — always run, never deleted
frontend/           ← Verified Playwright tests
backend/            ← Verified REST Assured tests
generated/            ← AI-generated tests from latest run
*.spec.ts           ← Playwright tests
*.java              ← REST Assured tests
diff_summary.json
generation_summary.json
archive/              ← Previous generated runs kept for history
feature_branch_20260428_143022/
feature_branch_20260428_160511/
results/
test_results.json   ← Latest execution results

### How tests move between tiers
AI generates test → lands in tests/generated/
↓
QA engineer reviews it — is it good?
↓
Yes → promote to tests/stable/   ← runs forever
No  → leave or delete
↓
Next run → previous generated/ archived → tests/archive/<timestamp>/

Every run executes **both** stable and generated tests together.

---

## 📊 Test Results & Reporting

### Terminal Output
╔══════════════════════════════════════╗
║           execution summary          ║
╚══════════════════════════════════════╝
✅ playwright           passed=5  failed=0 (33.1s)
✅ rest-assured         passed=10 failed=0 (11.6s)
Total passed : 15
Total failed : 0
Overall      : ✅ ALL PASSED
📊 ReportPortal → https://your-rp-host/ui/#project/launches

### JSON Report

Results saved to `tests/results/test_results.json`:

```json
{
  "timestamp": "2026-04-28T14:30:22Z",
  "branch": "feature/user-endpoint",
  "results": [
    {
      "framework": "playwright",
      "status": "passed",
      "passed": 5,
      "failed": 0,
      "duration": 33.1
    },
    {
      "framework": "rest-assured",
      "status": "passed",
      "passed": 10,
      "failed": 0,
      "duration": 11.6
    }
  ]
}
```

### ReportPortal

Configure `RP_ENDPOINT`, `RP_API_KEY` and `RP_PROJECT` in `.env` to push
results to ReportPortal automatically after every run.

---

## 📁 Project Structure
```
qognition-core/
├── .claude/
│   └── SKILL.md                  ← Automation skill definition
├── scripts/
│   ├── fetch_diff.sh             ← Detects changes + captures actual diff
│   ├── generate_tests.py         ← AI test generation (Gemini or Claude)
│   └── run_tests.py              ← Execution + reporting
├── tests/
│   ├── stable/
│   │   ├── frontend/             ← Curated Playwright tests (always run)
│   │   └── backend/              ← Curated REST Assured tests (always run)
│   ├── generated/                ← Latest AI generated tests
│   │   ├── diff_summary.json     ← What changed + actual diff content
│   │   ├── generation_summary.json
│   │   ├── *.spec.ts
│   │   └── *.java
│   ├── archive/                  ← Previous generated runs
│   └── results/
│       └── test_results.json
├── api-tests/                    ← Maven project for REST Assured
│   ├── pom.xml
│   └── src/test/
│       ├── java/com/qognition/   ← Synced Java tests (stable + generated)
│       └── resources/
│           └── reportportal.properties
├── docker-compose.yml            ← Wires qognition-ui + qognition-api
├── playwright.config.ts          ← Picks up stable + generated .spec.ts
├── .env.example                  ← Credentials template
└── requirements.txt              ← Python dependencies
```

---

## 🎬 Demo Script

Use this flow when presenting Qognition to an audience:

### Act 1 — Setup (2 min)
- Open the 3 repos on GitHub side by side
- Run `docker compose up -d` — show both services starting
- Open `http://localhost:3000` — show the React app with nav
- Hit `http://localhost:8080/actuator/health` — show Spring Boot running

### Act 2 — Make a Real Change (2 min)
- In `qognition-api`, add a new endpoint (e.g. `/users`) on a feature branch
- Push the change to GitHub

### Act 3 — AI Takes Over (3 min)
- Run `fetch_diff.sh` — show the JSON capturing actual diff lines
- Point out: *"It read 49 lines of real Java code — not just the filename"*
- Run `generate_tests.py` — watch AI write tests in real time
- Open the generated file — show it correctly identified all 3 endpoints,
  the static test data (Alice, Bob, Carol), and the case-insensitive logic

### Act 4 — Execution (2 min)
- Run `run_tests.py all` — stable + generated running together
- Show `passed=15 failed=0` in terminal
- Open ReportPortal — show the launch with results

### Act 5 — Provider Switch (1 min)
- Delete generated tests
- Run `generate_tests.py claude` instead of gemini
- Show Claude generating equivalent tests
- **Key message**: provider-agnostic — swap AI models without touching the pipeline

### Act 6 — Promote to Stable (1 min)
- Copy the generated `UserControllerTest.java` to `tests/stable/backend/`
- Explain: *"QA engineer reviews, approves, promotes — now it runs forever"*
- Next run will archive the generated version and always include the stable one

### 💬 Key Talking Points
- *"The diff is the spec — AI reads what changed, not just what file changed"*
- *"Tests are generated in seconds, not hours"*
- *"The QA engineer shifts from writing to reviewing and curating"*
- *"Provider-agnostic — Gemini today, Claude tomorrow, same pipeline"*
- *"Tests grow over time — stable suite gets richer with every feature"*
- *"Every run is traceable — archive shows full history of generated tests"*

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend 404 on endpoints | `docker compose up --build -d` |
| Java compile error | Script auto-extracts class name from generated code |
| Missing package declaration | Script prepends `package com.qognition;` automatically |
| Gemini timeout | Retry logic — 3 attempts × 300s each |
| ReportPortal 405 | Add `/api/v1` to `RP_ENDPOINT` in `.env` |
| ReportPortal project not found | Use lowercase project name |
| `dotenv` not found | Run `source .venv/bin/activate` first |
| Frontend tests failing | Ensure `docker compose up -d` is running |
| Old Java tests still running | `sync_java_tests()` cleans before syncing |

---

## 🗺️ Roadmap

- [ ] GitHub Actions CI — trigger pipeline automatically on every PR
- [ ] Slack notifications — post results to a channel after each run
- [ ] Test healing — AI fixes failing generated tests automatically
- [ ] Coverage tracking — what's tested vs what changed over time
- [ ] More AI providers — OpenAI, Mistral, local models
- [ ] Web dashboard — visualise stable vs generated vs archived tests

---

<div align="center">

Built to demonstrate the future of QA automation 🚀

**[qognition-ui](https://github.com/chhatbarjignesh/qognition-ui)** •
**[qognition-api](https://github.com/chhatbarjignesh/qognition-api)** •
**[qognition-core](https://github.com/chhatbarjignesh/qognition-core)**

</div>