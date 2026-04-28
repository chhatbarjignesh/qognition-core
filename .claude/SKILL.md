# Qognition Automation Skill

## Overview
Qognition is an AI-powered QA automation POC that demonstrates how modern
testing landscapes are evolving. This skill enables Claude to autonomously:
1. Detect code changes across repositories
2. Generate tests using an AI CLI (Gemini or Claude)
3. Execute tests against a live stack
4. Report results to terminal, JSON and ReportPortal

---

## Repository Structure
qognition-ui/       → React frontend (port 3000)
qognition-api/      → Spring Boot backend (port 8080)
qognition-core/     → This repo — automation brain
.claude/
SKILL.md        → This file
scripts/
fetch_diff.sh   → Phase 2: detect changes
generate_tests.py → Phase 3: generate tests via AI CLI
run_tests.py    → Phase 4: execute + report
tests/
generated/      → AI generated test files land here
results/        → Execution results (JSON)
api-tests/        → Maven project for REST Assured tests
playwright.config.ts → Playwright config
docker-compose.yml   → Wires frontend + backend
.env                 → ReportPortal credentials (never commit)

---

## Environment Setup

### Prerequisites
```bash
node >= 18
java >= 17
maven >= 3.9
python3 >= 3.9
docker + docker compose
npm install -g @google/gemini-cli   # for Gemini
npm install -g @anthropic-ai/claude-cli  # for Claude CLI
```

### First Time Setup
```bash
cd qognition-core

# Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install python-dotenv

# Node dependencies
npm install

# Playwright browsers
npx playwright install --with-deps

# Copy and fill in credentials
cp .env.example .env
```

### .env file
RP_ENDPOINT=https://your-reportportal-host/api/v1
RP_API_KEY=your-api-key
RP_PROJECT=your_project_name
BRANCH=feature/your-branch

---

## Stack

| Layer      | Technology         | Port  |
|------------|--------------------|-------|
| Frontend   | React (CRA + TS)   | 3000  |
| Backend    | Spring Boot + Java | 8080  |
| E2E Tests  | Playwright         | —     |
| API Tests  | REST Assured       | —     |
| Reporting  | ReportPortal       | —     |
| AI Backend | Gemini / Claude CLI| —     |

---

## Running the Full Workflow

### Step 1 — Start the stack
```bash
cd qognition-core
docker compose up -d
sleep 20

# Verify both services are healthy
curl http://localhost:8080/actuator/health
curl http://localhost:3000
```

### Step 2 — Detect changes
```bash
# Compare feature branch vs master across both repos
./scripts/fetch_diff.sh <branch-name> master

# Output: tests/generated/diff_summary.json
```

### Step 3 — Generate tests
```bash
# Interactive — prompts for AI provider
python3 scripts/generate_tests.py

# Or pass provider directly
python3 scripts/generate_tests.py gemini
python3 scripts/generate_tests.py claude

# Output: tests/generated/*.spec.ts and *.java
```

### Step 4 — Execute tests
```bash
# Run all tests
python3 scripts/run_tests.py all

# Run frontend only
python3 scripts/run_tests.py frontend

# Run backend only
python3 scripts/run_tests.py backend

# Output: tests/results/test_results.json
# Output: ReportPortal launch (if configured)
```

### Full pipeline in one go
```bash
./scripts/fetch_diff.sh feature/my-branch master && \
python3 scripts/generate_tests.py gemini && \
python3 scripts/run_tests.py all
```

---

## AI Providers

| Provider | CLI Command | Install |
|----------|-------------|---------|
| Gemini   | `gemini`    | `npm install -g @google/gemini-cli` |
| Claude   | `claude`    | `npm install -g @anthropic-ai/claude-cli` |

Both providers receive the same prompt and produce equivalent output.
Provider used is recorded in `tests/generated/generation_summary.json`.

---

## Test Generation Rules

### Change Classification
| Repo     | File Type              | Test Generated      |
|----------|------------------------|---------------------|
| frontend | .tsx / .ts / .jsx / .js | Playwright E2E      |
| frontend | test / spec in path    | Playwright Unit     |
| backend  | .java                  | REST Assured API    |
| backend  | test in path           | REST Assured Unit   |

### Prompt Strategy
- Frontend: Playwright TypeScript targeting http://localhost:3000
- Backend: REST Assured Java targeting http://localhost:8080
- Only known endpoints are included in backend prompt to prevent hallucination
- Java filename is extracted from generated class name to ensure compilation

### Known Backend Endpoints
GET /actuator/health    → {status: "UP"}
GET /dashboard/summary  → {status, total, message}
GET /pagination         → {page, size, total}

### Known Frontend Routes
/            → Home page with Qognition header + nav
/dashboard   → Dashboard page
/reports     → Reports page
/*           → 404 Not Found page

---

## ReportPortal Integration

### Playwright (Frontend)
- Agent: `@reportportal/agent-js-playwright`
- Config: `playwright.config.ts` reporter section
- Launch name: `qognition-e2e`

### REST Assured (Backend)
- Agent: `agent-java-junit5`
- Config: `api-tests/src/test/resources/reportportal.properties`
- Launch name: `qognition-api`
- Extension: registered via `META-INF/services/org.junit.jupiter.api.extension.Extension`

---

## Output Files

| File | Description |
|------|-------------|
| `tests/generated/diff_summary.json` | Changed files per repo |
| `tests/generated/generation_summary.json` | Which tests were generated + provider used |
| `tests/generated/*.spec.ts` | Playwright E2E tests |
| `tests/generated/*.java` | REST Assured API tests |
| `tests/results/test_results.json` | Execution results with pass/fail counts |
| `tests/results/playwright_results.json` | Raw Playwright JSON report |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Backend 404 on endpoints | Container not rebuilt | `docker compose up --build -d` |
| Java compile error — wrong filename | Class name mismatch | Script auto-extracts class name from generated code |
| Stale Java test files | Old files in Maven dir | `sync_java_tests()` cleans before syncing |
| Gemini timeout | Slow response | Retry logic: 3 attempts, 300s timeout each |
| ReportPortal 405 | Wrong endpoint URL | Must include `/api/v1` in `RP_ENDPOINT` |
| ReportPortal project 404 | Wrong project name case | Use lowercase — e.g. `chhatbarjignesh_personal` |
| `dotenv` module not found | Wrong Python env | Activate venv: `source .venv/bin/activate` |
| Playwright picks up Java files | Wrong extension mapping | Backend always gets `.java`, frontend `.spec.ts` |

---

## POC Demo Flow

This is the recommended order to demonstrate qognition to an audience:

1. Show the 3 repos on GitHub — `qognition-ui`, `qognition-api`, `qognition-core`
2. Make a real change on a feature branch in `qognition-ui` or `qognition-api`
3. Run `fetch_diff.sh` — show the JSON output detecting the change
4. Run `generate_tests.py` — show AI writing tests in real time
5. Run `run_tests.py all` — show tests executing against live stack
6. Open ReportPortal — show results dashboard
7. Switch AI provider (gemini → claude) and regenerate to show multi-tenancy

**Key message**: The QA engineer no longer writes tests — they review and curate them.
The AI observes changes and responds with tests automatically.