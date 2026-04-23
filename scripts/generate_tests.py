#!/usr/bin/env python3

import json
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
TIMEOUT     = 300  # 5 minutes

def classify_change(file_entry):
    path  = file_entry["path"]
    ftype = file_entry["type"]
    if ftype in ["tsx", "ts", "jsx", "js"] and "test" not in path.lower():
        return "e2e"
    elif ftype == "java" and "test" not in path.lower():
        return "api"
    elif ftype in ["properties", "yml", "yaml"]:
        return "config"
    elif "test" in path.lower() or "spec" in path.lower():
        return "unit"
    else:
        return "general"

def build_prompt(repo_name, changed_files, repo_type):
    files_list = "\n".join([f"  - {f['path']} ({f['type']})" for f in changed_files])
    if repo_type == "frontend":
        test_framework = "Playwright"
        language       = "TypeScript"
        example        = "page.goto(), expect(locator).toBeVisible()"
    else:
        test_framework = "REST Assured (Java)"
        language       = "Java"
        example        = "given().when().get('/endpoint').then().statusCode(200)"

    return f"""You are a QA automation engineer. The following files were changed in the '{repo_name}' repository:

{files_list}

Generate a {test_framework} test in {language} that:
1. Tests the likely functionality affected by these file changes
2. Includes at least one happy path test
3. Includes at least one edge case or negative test
4. Uses realistic test data
5. Has clear test descriptions

Only output the raw test code. No explanation, no markdown fences, no preamble.
Example style: {example}"""

def call_gemini(prompt):
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  🤖 Calling Gemini CLI (attempt {attempt}/{MAX_RETRIES})...")
        try:
            result = subprocess.run(
                ["gemini"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=TIMEOUT
            )
            if result.returncode != 0:
                print(f"  ❌ Gemini error: {result.stderr.strip()}")
            elif result.stdout.strip():
                print(f"  ✅ Gemini responded on attempt {attempt}")
                return result.stdout.strip()
            else:
                print(f"  ⚠️  Empty response on attempt {attempt}")

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout on attempt {attempt} ({TIMEOUT}s)")

        if attempt < MAX_RETRIES:
            wait = attempt * 5
            print(f"  ⏳ Waiting {wait}s before retry...")
            time.sleep(wait)

    print(f"  ❌ All {MAX_RETRIES} attempts failed")
    return None

def write_test_file(repo_name, test_type, content):
    ext_map = {
        "e2e"    : "spec.ts",
        "api"    : "Test.java",
        "config" : "spec.ts",
        "unit"   : "spec.ts",
        "general": "spec.ts",
    }
    ext      = ext_map.get(test_type, "spec.ts")
    filename = f"{repo_name.replace('-', '_')}_{test_type}.{ext}"
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

    if not DIFF_FILE.exists():
        print(f"❌ diff_summary.json not found at {DIFF_FILE}")
        print("   Run ./scripts/fetch_diff.sh first")
        sys.exit(1)

    with open(DIFF_FILE) as f:
        diff = json.load(f)

    print(f"  Branch    : {diff['branch']}")
    print(f"  Base      : {diff['base']}")
    print(f"  Timestamp : {diff['timestamp']}")
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
        test_types = set(classify_change(f) for f in files)

        for test_type in test_types:
            print(f"  📋 Generating {test_type} test for {repo_name}...")
            prompt  = build_prompt(repo_name, files, repo_type)
            content = call_gemini(prompt)

            if content:
                filename = write_test_file(repo_name, test_type, content)
                generated.append({
                    "repo"     : repo_name,
                    "test_type": test_type,
                    "file"     : filename
                })
            print()

    summary_file = OUTPUT_DIR / "generation_summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "branch"   : diff["branch"],
            "base"     : diff["base"],
            "generated": generated
        }, f, indent=2)

    print("──────────────────────────────────────")
    print(f"  ✅ {len(generated)} test file(s) generated")
    print(f"  ✅ Summary → tests/generated/generation_summary.json")
    print("──────────────────────────────────────")
    print()

if __name__ == "__main__":
    main()
