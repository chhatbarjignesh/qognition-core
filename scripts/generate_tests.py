#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
ROOT_DIR    = SCRIPT_DIR.parent
DIFF_FILE   = ROOT_DIR / "tests/generated/diff_summary.json"
OUTPUT_DIR  = ROOT_DIR / "tests/generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = 3
TIMEOUT     = 300

# ── Supported providers ───────────────────
PROVIDERS = {
    "gemini": {
        "cmd"        : ["gemini"],
        "input_mode" : "stdin",
        "description": "Google Gemini CLI"
    },
    "claude": {
        "cmd"        : ["claude"],
        "input_mode" : "stdin",
        "description": "Anthropic Claude CLI"
    }
}

def select_provider():
    """Interactive provider selection if not passed as argument."""
    if len(sys.argv) > 1 and sys.argv[1] in PROVIDERS:
        provider = sys.argv[1]
        print(f"  🤖 Using provider: {PROVIDERS[provider]['description']}")
        return provider

    print("  Select AI provider:")
    for i, (key, val) in enumerate(PROVIDERS.items(), 1):
        print(f"    [{i}] {key:10} — {val['description']}")
    print()

    while True:
        choice = input("  Enter number or name (default: gemini): ").strip().lower()
        if choice == "" or choice == "1":
            return "gemini"
        elif choice == "2":
            return "claude"
        elif choice in PROVIDERS:
            return choice
        else:
            print("  ⚠️  Invalid choice. Enter 1, 2, 'gemini' or 'claude'")

def classify_change(file_entry, repo_type):
    path = file_entry["path"]
    if repo_type == "backend":
        return "unit" if "test" in path.lower() else "api"
    if repo_type == "frontend":
        return "unit" if "test" in path.lower() or "spec" in path.lower() else "e2e"
    return "general"

def build_prompt(repo_name, changed_files, repo_type):
    files_list = "\n".join([f"  - {f['path']} ({f['type']})" for f in changed_files])

    if repo_type == "frontend":
        test_framework = "Playwright"
        language       = "TypeScript"
        example        = "page.goto(), expect(locator).toBeVisible()"
        extra          = "The app runs at http://localhost:3000"
    else:
        test_framework = "REST Assured (Java)"
        language       = "Java"
        example        = "given().when().get('/endpoint').then().statusCode(200)"
        extra          = """The API runs at http://localhost:8080.
Use RestAssured.baseURI = "http://localhost:8080" in @BeforeAll.
Only test these existing endpoints:
  GET /actuator/health     → returns {status: "UP"}
  GET /dashboard/summary   → returns {status, total, message}
  GET /pagination          → returns {page, size, total}
Do not invent endpoints that are not listed above."""

    return f"""You are a QA automation engineer. The following files were changed in the '{repo_name}' repository:

{files_list}

Generate a {test_framework} test in {language} that:
1. Tests the likely functionality affected by these file changes
2. Includes at least one happy path test
3. Includes at least one edge case or negative test
4. Uses realistic test data
5. Has clear test descriptions

{extra}

Only output the raw test code. No explanation, no markdown fences, no preamble.
Example style: {example}"""

def call_ai(prompt, provider):
    config = PROVIDERS[provider]
    cmd    = config["cmd"]

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  🤖 Calling {config['description']} (attempt {attempt}/{MAX_RETRIES})...")
        try:
            result = subprocess.run(
                cmd,
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
            print(f"  ❌ '{cmd[0]}' CLI not found.")
            if provider == "gemini":
                print("     Install: npm install -g @google/gemini-cli")
            elif provider == "claude":
                print("     Install: npm install -g @anthropic-ai/claude-cli")
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

def write_test_file(repo_name, test_type, repo_type, content):
    if repo_type == "backend":
        classname = extract_java_classname(content)
        if classname:
            filename = f"{classname}.java"
            print(f"  📋 Detected Java class: {classname}")
        else:
            filename = f"{repo_name.replace('-', '_')}_{test_type}Test.java"
            print(f"  ⚠️  Could not detect class name, using: {filename}")
    else:
        filename = f"{repo_name.replace('-', '_')}_{test_type}.spec.ts"

    filepath = OUTPUT_DIR / filename
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  ✅ Test written → tests/generated/{filename}")
    return filename

def main():
    print()
    print("╔══════════════════════════════════════╗")
    print("║       qognition test generator       ║")
    print("╚══════════════════════════════════════╝")
    print()

    # ── Provider selection ────────────────
    provider = select_provider()
    print()

    if not DIFF_FILE.exists():
        print(f"❌ diff_summary.json not found at {DIFF_FILE}")
        print("   Run ./scripts/fetch_diff.sh first")
        sys.exit(1)

    with open(DIFF_FILE) as f:
        diff = json.load(f)

    print(f"  Branch    : {diff['branch']}")
    print(f"  Base      : {diff['base']}")
    print(f"  Timestamp : {diff['timestamp']}")
    print(f"  Provider  : {PROVIDERS[provider]['description']}")
    print(f"  Timeout   : {TIMEOUT}s per attempt, {MAX_RETRIES} retries")
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
                filename = write_test_file(repo_name, test_type, repo_type, content)
                generated.append({
                    "repo"     : repo_name,
                    "repo_type": repo_type,
                    "test_type": test_type,
                    "file"     : filename,
                    "provider" : provider
                })
            print()

    summary_file = OUTPUT_DIR / "generation_summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "branch"   : diff["branch"],
            "base"     : diff["base"],
            "provider" : provider,
            "generated": generated
        }, f, indent=2)

    print("──────────────────────────────────────")
    print(f"  ✅ {len(generated)} test file(s) generated")
    print(f"  ✅ Summary → tests/generated/generation_summary.json")
    print("──────────────────────────────────────")
    print()

if __name__ == "__main__":
    main()
