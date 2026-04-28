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

  # ── Classification ───────────────────────
  JAVA_FILES=$(echo "$CHANGED_FILES"   | grep '\.java$'                         || true)
  TSX_FILES=$(echo "$CHANGED_FILES"    | grep -E '\.tsx?$'                      || true)
  CSS_FILES=$(echo "$CHANGED_FILES"    | grep '\.css$'                          || true)
  CONFIG_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(properties|yml|yaml|env)$' || true)
  TEST_FILES=$(echo "$CHANGED_FILES"   | grep -iE '(test|spec)'                 || true)

  [ -n "$JAVA_FILES"   ] && echo "  🟠 Java/Backend changes"   >&2
  [ -n "$TSX_FILES"    ] && echo "  🔵 React/Frontend changes"  >&2
  [ -n "$CSS_FILES"    ] && echo "  🎨 CSS changes"             >&2
  [ -n "$CONFIG_FILES" ] && echo "  ⚙️  Config changes"         >&2
  [ -n "$TEST_FILES"   ] && echo "  🧪 Test file changes"       >&2
  echo "" >&2

  # ── Capture actual diff content per file ─
  FILES_JSON=""
  FIRST=true

  while IFS= read -r FILEPATH; do
    [ -z "$FILEPATH" ] && continue

    ext="${FILEPATH##*.}"

    # Get the actual diff for this file
    DIFF_CONTENT=$(git diff "origin/$BASE...origin/$BRANCH" -- "$FILEPATH" 2>/dev/null || echo "")

    # Get full file content from feature branch
    FILE_CONTENT=$(git show "origin/$BRANCH:$FILEPATH" 2>/dev/null || echo "")

    # Escape for JSON — replace special chars
    DIFF_ESCAPED=$(echo "$DIFF_CONTENT" | python3 -c "
import sys, json
content = sys.stdin.read()
print(json.dumps(content))
" 2>/dev/null || echo '""')

    FILE_ESCAPED=$(echo "$FILE_CONTENT" | python3 -c "
import sys, json
content = sys.stdin.read()
print(json.dumps(content))
" 2>/dev/null || echo '""')

    FILE_JSON='{"path":"'"$FILEPATH"'","type":"'"$ext"'","diff":'"$DIFF_ESCAPED"',"content":'"$FILE_ESCAPED"'}'

    if [ "$FIRST" = true ]; then
      FILES_JSON="$FILE_JSON"
      FIRST=false
    else
      FILES_JSON="$FILES_JSON,$FILE_JSON"
    fi

    echo "  📄 Captured diff for: $FILEPATH" >&2

  done <<< "$CHANGED_FILES"

  echo '{"repo":"'"$REPO_NAME"'","branch":"'"$BRANCH"'","status":"changes_found","files":['"$FILES_JSON"']}'
}

UI_JSON=$(analyse_repo  "$UI_REPO"  "qognition-ui")
API_JSON=$(analyse_repo "$API_REPO" "qognition-api")

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

