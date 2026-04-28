#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
ROOT_DIR    = SCRIPT_DIR.parent
DIFF_FILE   = ROOT_DIR / "tests/generated/diff_summary.json"

# ── Folder structure ──────────────────────
GENERATED_DIR = ROOT_DIR / "tests/generated"
STABLE_DIR    = ROOT_DIR / "tests/stable"
ARCHIVE_DIR   = ROOT_DIR / "tests/archive"

PROVIDERS = {
    "gemini": {
        "cmd"        : ["gemini"],
        "description": "Google Gemini CLI"
    },
    "claude": {
        "cmd"        : ["claude"],
        "description": "Anthropic Claude CLI"
    }
}

MAX_RETRIES = 3
TIMEOUT     = 300

def select_provider():
    if len(sys.argv) > 1 and sys.argv[1] in PROVIDERS:
        provider = sys.argv[1]
        print(f"  🤖 Provider : {PROVIDERS[provider]['description']}")
        return provider

    print("  Select AI provider:")
    for i, (key, val) in enumerate(PROVIDERS.items(), 1):
        print(f"    [{i}] {key:10} — {val['description']}")
    print()

    while True:
        choice = input("  Enter number or name (default: gemini): ").strip().lower()
        if choice in ("", "1"):
            return "gemini"
        elif choice == "2":
            return "claude"
        elif choice in PROVIDERS:
            return choice
        else:
            print("  ⚠️  Invalid — enter 1, 2, 'gemini' or 'claude'")

def classify_change(file_entry, repo_type):
    path = file_entry["path"]
    if repo_type == "backend":
        return "unit" if "test" in path.lower() else "api"
    if repo_type == "frontend":
        return "unit" if ("test" in path.lower() or "spec" in path.lower()) else "e2e"
    return "general"

def build_prompt(repo_name, changed_files, repo_type):
    """Build a rich prompt that includes actual diff content."""

    if repo_type == "frontend":
        test_framework = "Playwright"
        language       = "TypeScript"
        example        = "page.goto(), expect(locator).toBeVisible()"
        base_url       = "http://localhost:3000"
        extra = f"""The app runs at {base_url}.
Known routes:
  /            → Home page with Qognition header and nav links
  /dashboard   → Dashboard page with heading 'Dashboard'
  /reports     → Reports page
  /*           → 404 Not Found page with text '404'
Only test routes and elements that exist based on the diff above."""

    else:
        test_framework = "REST Assured (Java)"
        language       = "Java"
        example        = "given().when().get('/endpoint').then().statusCode(200)"
        base_url       = "http://localhost:8080"
        extra = f"""The API runs at {base_url}.
Use RestAssured.baseURI = "{base_url}" in @BeforeAll.
Only test endpoints that are explicitly visible in the diff above.
Do not invent endpoints that are not in the changed files."""

    # ── Build rich diff section ───────────
    diff_section = ""
    for f in changed_files:
        path    = f.get("path", "")
        diff    = f.get("diff", "").strip()
        content = f.get("content", "").strip()

        diff_section += f"\n### File: {path}\n"

        if diff:
            # Limit diff size to avoid token overflow
            diff_lines = diff.split('\n')[:80]
            diff_section += "**Diff (what changed):**\n```\n"
            diff_section += '\n'.join(diff_lines)
            diff_section += "\n```\n"

        if content and not diff:
            # New file — show full content (limited)
            content_lines = content.split('\n')[:60]
            diff_section += "**New file content:**\n```\n"
            diff_section += '\n'.join(content_lines)
            diff_section += "\n```\n"

    return f"""You are a QA automation engineer reviewing code changes.

## Repository: {repo_name}
## Changed Files:
{diff_section}

## Your Task:
Generate a {test_framework} test in {language} that:
1. Tests EXACTLY the functionality shown in the diff above
2. Includes at least one happy path test for each changed feature
3. Includes at least one negative or edge case test
4. Uses realistic test data that matches what the code expects
5. Has clear descriptive test names

## Environment:
{extra}

## Output Rules:
- Output ONLY raw {language} code
- No markdown fences, no explanation, no preamble
- Class name must clearly reflect what is being tested
- Example style: {example}"""

def call_ai(prompt, provider):
    config = PROVIDERS[provider]
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  🤖 Calling {config['description']} (attempt {attempt}/{MAX_RETRIES})...")
        try:
            result = subprocess.run(
                config["cmd"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=TIMEOUT
            )
            if result.returncode != 0:
                print(f"  ❌ Error: {result.stderr.strip()}")
            elif result.stdout.strip():
                print(f"  ✅ Response received on attempt {attempt}")
                return result.stdout.strip()
            else:
                print(f"  ⚠️  Empty response on attempt {attempt}")
        except FileNotFoundError:
            print(f"  ❌ '{config['cmd'][0]}' CLI not found.")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout on attempt {attempt} ({TIMEOUT}s)")

        if attempt < MAX_RETRIES:
            wait = attempt * 5
            print(f"  ⏳ Waiting {wait}s before retry...")
            time.sleep(wait)

    print(f"  ❌ All {MAX_RETRIES} attempts failed")
    return None

def extract_java_classname(content):
    match = re.search(r'public\s+class\s+(\w+)', content)
    return match.group(1) if match else None

def archive_previous(run_dir):
    """Move old generated tests to archive before new run."""
    old_files = list(GENERATED_DIR.glob("*.spec.ts")) + \
                list(GENERATED_DIR.glob("*.java"))
    if old_files:
        archive_run = ARCHIVE_DIR / run_dir
        archive_run.mkdir(parents=True, exist_ok=True)
        for f in old_files:
            shutil.move(str(f), str(archive_run / f.name))
        print(f"  📦 Archived {len(old_files)} previous test(s) → tests/archive/{run_dir}/")

def write_test_file(repo_type, content):
    """Write generated test — filename derived from class name or content."""
    if repo_type == "backend":
        classname = extract_java_classname(content)
        if classname:
            filename = f"{classname}.java"
            print(f"  📋 Detected Java class: {classname}")
        else:
            filename = f"GeneratedApiTest_{int(time.time())}.java"
    else:
        # Extract describe block name for TS files
        match = re.search(r"describe\(['\"](.+?)['\"]", content)
        if match:
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', match.group(1))[:40]
            filename  = f"{safe_name}.spec.ts"
        else:
            filename  = f"generated_e2e_{int(time.time())}.spec.ts"

    filepath = GENERATED_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Test written → tests/generated/{filename}")
    return filename

def list_stable_tests():
    """Show what stable tests exist alongside generated ones."""
    stable_fe = list((STABLE_DIR / "frontend").glob("*.spec.ts"))
    stable_be = list((STABLE_DIR / "backend").glob("*.java"))
    if stable_fe or stable_be:
        print()
        print("  📚 Stable tests (always run):")
        for f in stable_fe:
            print(f"    → tests/stable/frontend/{f.name}")
        for f in stable_be:
            print(f"    → tests/stable/backend/{f.name}")

def main():
    print()
    print("╔══════════════════════════════════════╗")
    print("║       qognition test generator       ║")
    print("╚══════════════════════════════════════╝")
    print()

    provider = select_provider()
    print()

    if not DIFF_FILE.exists():
        print(f"❌ diff_summary.json not found")
        print("   Run ./scripts/fetch_diff.sh first")
        sys.exit(1)

    with open(DIFF_FILE) as f:
        diff = json.load(f)

    # ── Archive previous generated tests ──
    run_label = f"{diff['branch'].replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_previous(run_label)

    print(f"  Branch    : {diff['branch']}")
    print(f"  Base      : {diff['base']}")
    print(f"  Timestamp : {diff['timestamp']}")
    print(f"  Provider  : {PROVIDERS[provider]['description']}")
    print(f"  Timeout   : {TIMEOUT}s × {MAX_RETRIES} retries")
    print()

    generated = []

    for repo in diff["repos"]:
        repo_name = repo["repo"]
        status    = repo["status"]
        files     = repo["files"]

        print(f"──────────────────────────────────────")
        print(f"  Repo: {repo_name}")
        print(f"──────────────────────────────────────")

        if status in ["no_changes", "branch_not_found"]:
            print(f"  ⚠️  Skipping — {status}")
            print()
            continue

        repo_type  = "frontend" if "ui" in repo_name else "backend"
        test_types = set(classify_change(f, repo_type) for f in files)

        for test_type in test_types:
            print(f"  📋 Generating {test_type} test for {repo_name} ({repo_type})...")
            prompt  = build_prompt(repo_name, files, repo_type)
            content = call_ai(prompt, provider)

            if content:
                filename = write_test_file(repo_type, content)
                generated.append({
                    "repo"     : repo_name,
                    "repo_type": repo_type,
                    "test_type": test_type,
                    "file"     : filename,
                    "provider" : provider,
                    "archived_to": f"tests/archive/{run_label}/"
                })
            print()

    list_stable_tests()

    # ── Save summary ──────────────────────
    summary = {
        "run_label" : run_label,
        "branch"    : diff["branch"],
        "base"      : diff["base"],
        "provider"  : provider,
        "generated" : generated,
        "stable"    : {
            "frontend": [f.name for f in (STABLE_DIR / "frontend").glob("*.spec.ts")],
            "backend" : [f.name for f in (STABLE_DIR / "backend").glob("*.java")]
        }
    }
    summary_file = GENERATED_DIR / "generation_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("──────────────────────────────────────")
    print(f"  ✅ {len(generated)} test(s) generated")
    print(f"  📦 Previous tests archived → tests/archive/{run_label}/")
    print(f"  📄 Summary → tests/generated/generation_summary.json")
    print("──────────────────────────────────────")
    print()

if __name__ == "__main__":
    main()
