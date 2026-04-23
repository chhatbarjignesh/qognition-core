#!/bin/bash

set -e

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

  echo "──────────────────────────────────────" >&2
  echo "  Repo: $REPO_NAME"                     >&2
  echo "──────────────────────────────────────" >&2

  cd "$REPO_PATH"
  git fetch origin --quiet

  if ! git ls-remote --exit-code --heads origin "$BRANCH" > /dev/null 2>&1; then
    echo "  ⚠️  Branch '$BRANCH' not found in $REPO_NAME — skipping" >&2
    echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"branch_not_found","files":[]}'
    return
  fi

  CHANGED_FILES=$(git diff --name-only "origin/$BASE...origin/$BRANCH" 2>/dev/null || echo "")

  if [ -z "$CHANGED_FILES" ]; then
    echo "  ✅ No changes detected" >&2
    echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"no_changes","files":[]}'
    return
  fi

  echo "" >&2
  echo "  Changed files:" >&2
  echo "$CHANGED_FILES" | while read -r f; do echo "    → $f" >&2; done
  echo "" >&2

  JAVA_FILES=$(echo "$CHANGED_FILES"   | grep '\.java$'                      || true)
  TSX_FILES=$(echo "$CHANGED_FILES"    | grep '\.tsx\?$'                     || true)
  CSS_FILES=$(echo "$CHANGED_FILES"    | grep '\.css$'                       || true)
  CONFIG_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(properties|yml|yaml|env)$' || true)
  TEST_FILES=$(echo "$CHANGED_FILES"   | grep -iE '(test|spec)'              || true)

  [ -n "$JAVA_FILES"   ] && echo "  🟠 Java/Backend changes detected"   >&2
  [ -n "$TSX_FILES"    ] && echo "  🔵 React/Frontend changes detected"  >&2
  [ -n "$CSS_FILES"    ] && echo "  🎨 CSS changes detected"             >&2
  [ -n "$CONFIG_FILES" ] && echo "  ⚙️  Config changes detected"         >&2
  [ -n "$TEST_FILES"   ] && echo "  🧪 Test file changes detected"       >&2
  echo "" >&2

  FILES_JSON=$(echo "$CHANGED_FILES" | awk '{
    ext = $0; sub(/.*\./, "", ext)
    print "{\"path\":\"" $0 "\",\"type\":\"" ext "\"}"
  }' | paste -sd ',' -)

  # Only JSON goes to stdout — terminal output all goes to stderr
  echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"changes_found","files":['"$FILES_JSON"']}'
}

# ── Run analysis on both repos ───────────
UI_JSON=$(analyse_repo  "$UI_REPO"  "qognition-ui")
API_JSON=$(analyse_repo "$API_REPO" "qognition-api")

# ── Write clean JSON output ──────────────
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

echo "──────────────────────────────────────" >&2
echo "  ✅ Summary written to:"               >&2
echo "     $OUTPUT_FILE"                      >&2
echo "──────────────────────────────────────" >&2
echo "" >&2

