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
Qognition watches for code changes across repositories, understands what
changed, and automatically generates and executes tests — all powered by AI.

### The Core Loop
Developer pushes a change
↓
Qognition detects what changed (diff analysis)
↓
AI generates relevant tests (Gemini or Claude)
↓
Tests execute against the live stack
↓
Results reported to terminal + JSON + ReportPortal

---

## 🏗️ Architecture
┌──────────────────────────────────────────────────────┐  
│                    qognition-core                    │  
│                  (Automation Brain)                  │  
│                                                      │  
│  fetch_diff.sh ──► generate_tests.py ──► run_tests.py│  
│       │                  │                   │       │  
│   Git Diff           AI CLI              Playwright  │  
│   Analysis        (Gemini/Claude)      REST Assured  │  
│       │                  │                   │       │  
│  diff_summary       *.spec.ts          ReportPortal  │  
│     .json           *.java              + JSON       │  
└──────┬──────────────────────────────────────┬────────┘  
       │                                      │  
       ▼                                      ▼  
┌─────────────┐                      ┌─────────────────┐  
│qognition-ui │                      │ qognition-api   │  
│   React     │ ◄────── Tests ─────► │  Spring Boot    │  
│  Port 3000  │                      │   Port 8080     │  
└─────────────┘                      └─────────────────┘  

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
git clone https://github.com/YOUR_USERNAME/qognition-ui
git clone https://github.com/YOUR_USERNAME/qognition-api
git clone https://github.com/YOUR_USERNAME/qognition-core
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
# Step 1: Detect what changed
./scripts/fetch_diff.sh feature/my-branch master

# Step 2: Generate tests with AI
python3 scripts/generate_tests.py          # interactive provider selection
python3 scripts/generate_tests.py gemini   # or pass directly
python3 scripts/generate_tests.py claude

# Step 3: Execute tests
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

```bash
# Interactive selection
python3 scripts/generate_tests.py

╔══════════════════════════════════════╗
║       qognition test generator       ║
╚══════════════════════════════════════╝

  Select AI provider:
    [1] gemini     — Google Gemini CLI
    [2] claude     — Anthropic Claude CLI

  Enter number or name (default: gemini):
```

The provider used is recorded in `tests/generated/generation_summary.json`
for traceability.

---

## 📊 Test Results & Reporting

### Terminal Output
╔══════════════════════════════════════╗
║           execution summary          ║
╚══════════════════════════════════════╝
✅ playwright           passed=5 failed=0 (33.1s)
✅ rest-assured         passed=4 failed=0 (11.6s)
Total passed : 9
Total failed : 0
Overall      : ✅ ALL PASSED
📊 ReportPortal → https://your-rp-host/ui/\#project/launches

### JSON Report

Results are saved to `tests/results/test_results.json`:

```json
{
  "timestamp": "2026-04-23T20:55:29Z",
  "branch": "feature/sample-change",
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
      "passed": 4,
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

qognition-core/  
.
├── .claude  
    └── SKILL.md                               # Automation skill definition  
├── scripts  
    ├── fetch_diff.sh                          # Phase 2: diff detection 
    ├── generate_tests.py                      # Phase 3: AI test generation  
    └── run_tests.py                           # Phase 4: execution + reporting  
├── tests
    ├── generated                              # AI generated tests land here 
        ├── diff_summary.json  
        ├── generation_summary.json  
        ├── *.spec.ts                          # Playwright tests  
        └── *.java                             # REST Assured tests  
    └── results   
        └── test_results.json                  # Execution results  
├── api-tests                                  # Maven project for Java tests  
    ├── pom.xml  
    └── src/test   
        ├── java/com/qognition                 # Synced Java test files  
        └── resources   
            └── reportportal.properties  
├── docker-compose.yml                         # Wires UI + API  
├── playwright.config.ts                       # Playwright + RP config  
├── .env.example                               # Credentials template  
└── requirements.txt                           # Python dependencies  

---

## 🎬 Demo Script

Use this flow when presenting Qognition to an audience:

### Act 1 — Setup (2 min)
- Open the 3 repos on GitHub side by side
- Show `docker compose up` starting both services
- Open `http://localhost:3000` — show the React app
- Hit `http://localhost:8080/actuator/health` — show Spring Boot running

### Act 2 — Make a Change (2 min)
- In `qognition-api`, add a new endpoint on a feature branch
- In `qognition-ui`, update a component on the same branch
- Push both changes

### Act 3 — AI Takes Over (3 min)
- Run `fetch_diff.sh` — show the diff JSON detecting both changes
- Run `generate_tests.py` — watch AI write tests in real time
- Open the generated files — show meaningful, realistic tests

### Act 4 — Execution (2 min)
- Run `run_tests.py all` — watch tests execute
- Show pass/fail in terminal
- Open ReportPortal — show the launch with results

### Act 5 — Provider Switch (1 min)
- Delete generated tests
- Run `generate_tests.py claude` instead of gemini
- Show Claude generating equivalent tests
- **Key message**: provider-agnostic, the workflow stays the same

### 💬 Key Talking Points
- "The diff is the spec — AI infers what needs testing from what changed"
- "Tests are generated in seconds, not hours"
- "The QA engineer shifts from writing to reviewing"
- "Provider-agnostic — swap AI models without changing the pipeline"
- "Every run is traceable — JSON + ReportPortal give full audit trail"

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend 404 on endpoints | `docker compose up --build -d` |
| Java compile error | Class name auto-extracted from generated code |
| Gemini timeout | Retry logic handles it — 3 attempts × 300s |
| ReportPortal 405 | Add `/api/v1` to `RP_ENDPOINT` in `.env` |
| ReportPortal project not found | Use lowercase project name |
| `dotenv` not found | Run `source .venv/bin/activate` first |
| Frontend tests failing | Ensure `docker compose up -d` is running |

---

## 🗺️ Roadmap

- [ ] GitHub Actions CI — trigger pipeline on every PR automatically
- [ ] Slack notifications — post results to a channel
- [ ] Test healing — AI fixes failing tests automatically
- [ ] Coverage tracking — track what's tested vs what changed over time
- [ ] Support for more AI providers (OpenAI, Mistral)

---

<div align="center">

Built to demonstrate the future of QA automation 🚀

**qognition-ui** • **qognition-api** • **qognition-core**

</div>
