#!/bin/bash

# ─────────────────────────────────────────
# qognition-core: fetch_diff.sh
# Compares a feature branch vs master
# across qognition-ui and qognition-api
# ─────────────────────────────────────────

set -e

# ── Config ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
UI_REPO="$ROOT_DIR/../qognition-ui"
API_REPO="$ROOT_DIR/../qognition-api"
OUTPUT_DIR="$ROOT_DIR/tests/generated"
OUTPUT_FILE="$OUTPUT_DIR/diff_summary.json"
BRANCH="${1:-feature/sample-change}"
BASE="${2:-master}"

mkdir -p "$OUTPUT_DIR"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        qognition diff detector       ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Branch : $BRANCH"
echo "  Base   : $BASE"
echo ""

# ── Helper: analyse diff in a repo ──────
analyse_repo() {
  local REPO_PATH="$1"
  local REPO_NAME="$2"

  echo "──────────────────────────────────────"
  echo "  Repo: $REPO_NAME"
  echo "──────────────────────────────────────"

  cd "$REPO_PATH"

  # Fetch latest
  git fetch origin --quiet

  # Check branch exists
  if ! git ls-remote --exit-code --heads origin "$BRANCH" > /dev/null 2>&1; then
    echo "  ⚠️  Branch '$BRANCH' not found in $REPO_NAME — skipping"
    echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"branch_not_found","files":[]}' 
    return
  fi

  # Get changed files
  CHANGED_FILES=$(git diff --name-only "origin/$BASE...origin/$BRANCH" 2>/dev/null || echo "")

  if [ -z "$CHANGED_FILES" ]; then
    echo "  ✅ No changes detected"
    echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"no_changes","files":[]}'
    return
  fi

  echo ""
  echo "  Changed files:"
  echo "$CHANGED_FILES" | while read -r f; do echo "    → $f"; done
  echo ""

  # Classify each file
  JAVA_FILES=$(echo "$CHANGED_FILES" | grep '\.java$' || true)
  TSX_FILES=$(echo "$CHANGED_FILES"  | grep '\.tsx\?$' || true)
  CSS_FILES=$(echo "$CHANGED_FILES"  | grep '\.css$' || true)
  CONFIG_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(properties|yml|yaml|env)$' || true)
  TEST_FILES=$(echo "$CHANGED_FILES"  | grep -iE '(test|spec)' || true)

  # Print classification
  [ -n "$JAVA_FILES"   ] && echo "  🟠 Java/Backend changes detected"
  [ -n "$TSX_FILES"    ] && echo "  🔵 React/Frontend changes detected"
  [ -n "$CSS_FILES"    ] && echo "  🎨 CSS changes detected"
  [ -n "$CONFIG_FILES" ] && echo "  ⚙️  Config changes detected"
  [ -n "$TEST_FILES"   ] && echo "  🧪 Test file changes detected"
  echo ""

  # Build JSON file list
  FILES_JSON=$(echo "$CHANGED_FILES" | awk '{
    split($0, parts, "/")
    ext = $0; sub(/.*\./, "", ext)
    print "{\"path\":\"" $0 "\",\"type\":\"" ext "\"}"
  }' | paste -sd ',' -)

  echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"changes_found","files":['"$FILES_JSON"']}'
}

# ── Run analysis on both repos ───────────
UI_JSON=$(analyse_repo  "$UI_REPO"  "qognition-ui")
API_JSON=$(analyse_repo "$API_REPO" "qognition-api")

# ── Write combined JSON output ───────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$OUTPUT_FILE" <<JSON
{
  "timestamp": "$TIMESTAMP",
  "branch": "$BRANCH",
  "base": "$BASE",
  "repos": [
    $UI_JSON,
    $API_JSON
  ]
}
JSON

echo "──────────────────────────────────────"
echo "  ✅ Summary written to:"
echo "     $OUTPUT_FILE"
echo "──────────────────────────────────────"
echo ""

