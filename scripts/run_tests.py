#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR  = Path(__file__).parent
ROOT_DIR    = SCRIPT_DIR.parent
GENERATED   = ROOT_DIR / "tests/generated"
RESULTS_DIR = ROOT_DIR / "tests/results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RP_ENDPOINT = os.getenv("RP_ENDPOINT", "")
RP_API_KEY  = os.getenv("RP_API_KEY", "")
RP_PROJECT  = os.getenv("RP_PROJECT", "qognition")
BRANCH      = os.getenv("BRANCH", "feature")

def extract_specs(suites):
    specs = []
    for suite in suites:
        specs.extend(suite.get("specs", []))
        specs.extend(extract_specs(suite.get("suites", [])))
    return specs

def sync_java_tests():
    dest = ROOT_DIR / "api-tests/src/test/java/com/qognition"
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.java"):
        old.unlink()
        print(f"  🗑️  Removed stale file: {old.name}")
    for f in GENERATED.glob("*.java"):
        target = dest / f.name
        target.write_text(f.read_text())
        print(f"  📂 Synced {f.name} → api-tests/")

def run_playwright():
    print()
    print("──────────────────────────────────────")
    print("  🎭 Running Playwright (Frontend) Tests")
    print("──────────────────────────────────────")

    specs = list(GENERATED.glob("*.spec.ts"))
    if not specs:
        print("  ⚠️  No .spec.ts files found — skipping")
        return {"framework": "playwright", "status": "skipped", "tests": []}

    env = {
        **os.environ,
        "RP_API_KEY"  : RP_API_KEY,
        "RP_ENDPOINT" : RP_ENDPOINT,
        "RP_PROJECT"  : RP_PROJECT,
        "BRANCH"      : BRANCH,
    }

    start  = time.time()
    result = subprocess.run(
        ["npx", "playwright", "test"],
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True
    )
    duration = round(time.time() - start, 2)

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    results_file = ROOT_DIR / "tests/results/playwright_results.json"
    tests  = []
    passed = failed = 0

    if results_file.exists():
        with open(results_file) as f:
            raw = json.load(f)
        stats  = raw.get("stats", {})
        passed = stats.get("expected", 0)
        failed = stats.get("unexpected", 0)
        for spec in extract_specs(raw.get("suites", [])):
            tests.append({
                "name"    : spec.get("title"),
                "status"  : "passed" if spec.get("ok") else "failed",
                "duration": spec.get("tests", [{}])[0].get("results", [{}])[0].get("duration", 0)
            })

    print(f"  ✅ Passed : {passed}")
    print(f"  ❌ Failed : {failed}")
    print(f"  ⏱️  Duration: {duration}s")

    if RP_ENDPOINT and RP_API_KEY:
        print(f"  📊 ReportPortal → {RP_ENDPOINT}/ui/#{RP_PROJECT}/launches")
    else:
        print("  ⚠️  ReportPortal skipped — RP_ENDPOINT or RP_API_KEY not set in .env")

    return {
        "framework": "playwright",
        "status"   : "passed" if failed == 0 else "failed",
        "passed"   : passed,
        "failed"   : failed,
        "duration" : duration,
        "tests"    : tests
    }

def run_api_tests():
    print()
    print("──────────────────────────────────────")
    print("  ☕ Running REST Assured (Backend) Tests")
    print("──────────────────────────────────────")

    java_files = list(GENERATED.glob("*.java"))
    if not java_files:
        print("  ⚠️  No *.java files found — skipping")
        return {"framework": "rest-assured", "status": "skipped", "tests": []}

    sync_java_tests()

    env = {
        **os.environ,
        "RP_ENDPOINT": RP_ENDPOINT,
        "RP_API_KEY" : RP_API_KEY,
        "RP_PROJECT" : RP_PROJECT,
    }

    start  = time.time()
    result = subprocess.run(
        ["mvn", "test", "-f", "api-tests/pom.xml"],
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True
    )
    duration = round(time.time() - start, 2)

    print(result.stdout[-3000:])
    if result.stderr:
        print(result.stderr[-1000:])

    surefire_dir = ROOT_DIR / "api-tests/target/surefire-reports"
    tests  = []
    passed = failed = 0

    if surefire_dir.exists():
        for xml in surefire_dir.glob("TEST-*.xml"):
            content        = xml.read_text()
            tests_match    = re.search(r'tests="(\d+)"',    content)
            failures_match = re.search(r'failures="(\d+)"', content)
            errors_match   = re.search(r'errors="(\d+)"',   content)
            total_tests    = int(tests_match.group(1))    if tests_match    else 0
            total_fail     = int(failures_match.group(1)) if failures_match else 0
            total_err      = int(errors_match.group(1))   if errors_match   else 0
            f = total_fail + total_err
            p = total_tests - f
            passed += p
            failed += f
            tests.append({
                "name"  : xml.stem,
                "status": "failed" if f > 0 else "passed",
                "passed": p,
                "failed": f
            })

    print(f"  ✅ Passed : {passed}")
    print(f"  ❌ Failed : {failed}")
    print(f"  ⏱️  Duration: {duration}s")

    if RP_ENDPOINT and RP_API_KEY:
        print(f"  📊 ReportPortal → {RP_ENDPOINT}/ui/#{RP_PROJECT}/launches")
    else:
        print("  ⚠️  ReportPortal skipped — RP_ENDPOINT or RP_API_KEY not set in .env")

    return {
        "framework": "rest-assured",
        "status"   : "passed" if failed == 0 else "failed",
        "passed"   : passed,
        "failed"   : failed,
        "duration" : duration,
        "tests"    : tests
    }

def write_results(results):
    output_file = RESULTS_DIR / "test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "branch"   : BRANCH,
            "results"  : results
        }, f, indent=2)
    print()
    print(f"  ✅ Results saved → tests/results/test_results.json")

def print_summary(results):
    print()
    print("╔══════════════════════════════════════╗")
    print("║           execution summary          ║")
    print("╚══════════════════════════════════════╝")
    total_passed = total_failed = 0
    for r in results:
        if r["status"] == "skipped":
            print(f"  ⏭️  {r['framework']:20} skipped")
            continue
        p = r.get("passed", 0)
        f = r.get("failed", 0)
        total_passed += p
        total_failed += f
        icon = "✅" if f == 0 else "❌"
        print(f"  {icon} {r['framework']:20} passed={p} failed={f} ({r.get('duration', 0)}s)")
    print()
    print(f"  Total passed : {total_passed}")
    print(f"  Total failed : {total_failed}")
    print(f"  Overall      : {'✅ ALL PASSED' if total_failed == 0 else '❌ SOME FAILED'}")
    print()
    if RP_ENDPOINT:
        print(f"  📊 ReportPortal → {RP_ENDPOINT}/ui/#{RP_PROJECT}/launches")
    print()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print()
    print("╔══════════════════════════════════════╗")
    print("║        qognition test runner         ║")
    print("╚══════════════════════════════════════╝")
    print()
    print(f"  Mode         : {mode}")
    print(f"  Branch       : {BRANCH}")
    print(f"  ReportPortal : {RP_ENDPOINT or 'not configured'}")
    print()

    results = []

    if mode in ["all", "frontend"]:
        results.append(run_playwright())

    if mode in ["all", "backend"]:
        results.append(run_api_tests())

    if not results:
        print(f"❌ Unknown mode '{mode}'. Use: all | frontend | backend")
        sys.exit(1)

    write_results(results)
    print_summary(results)

    if any(r.get("failed", 0) > 0 for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
