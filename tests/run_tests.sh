#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RELEASE_SCRIPT="$REPO_ROOT/.github/scripts/release_version.py"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
  local test_name="$1"
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -n "Running $test_name... "
  
  local temp_dir
  temp_dir=$(mktemp -d)
  
  if (cd "$temp_dir" && "$test_name" "$temp_dir"); then
    echo "✓ PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo "✗ FAILED"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
  rm -rf "$temp_dir"
}

test_release_version_patch() {
  local dir="$1"
  git init -b main "$dir" >/dev/null 2>&1 || git init "$dir" >/dev/null 2>&1
  git -C "$dir" config user.name "Test User"
  git -C "$dir" config user.email "test@example.com"
  
  cat << 'EOF' > "$dir/CHANGELOG.md"
# Changelog
## [unreleased]
### Added
- Feature 1
EOF
  git -C "$dir" add CHANGELOG.md
  git -C "$dir" commit -m "initial commit" >/dev/null 2>&1
  git -C "$dir" tag "v1.0.0"

  python3 "$RELEASE_SCRIPT" patch >/dev/null 2>&1
  
  # Verify changelog has 1.0.1
  grep -q "## \[1.0.1\]" "$dir/CHANGELOG.md"
}

test_snapshot_version_calculation() {
  local dir="$1"
  git init -b main "$dir" >/dev/null 2>&1 || git init "$dir" >/dev/null 2>&1
  git -C "$dir" config user.name "Test User"
  git -C "$dir" config user.email "test@example.com"
  
  cat << 'EOF' > "$dir/CHANGELOG.md"
# Changelog
## [unreleased]
EOF
  git -C "$dir" add CHANGELOG.md
  git -C "$dir" commit -m "initial commit" >/dev/null 2>&1
  git -C "$dir" tag "v2.1.0"

  # Snapshot on feature branch
  local output
  output=$(python3 "$RELEASE_SCRIPT" snapshot --branch "feature/awesome-tool")
  echo "$output" | grep -q "2.1.1-feature-awesome-tool.1"
}

test_dry_run_leaves_changelog_intact() {
  local dir="$1"
  git init -b main "$dir" >/dev/null 2>&1 || git init "$dir" >/dev/null 2>&1
  git -C "$dir" config user.name "Test User"
  git -C "$dir" config user.email "test@example.com"
  
  cat << 'EOF' > "$dir/CHANGELOG.md"
# Changelog
## [unreleased]
### Added
- Unreleased feature
EOF
  git -C "$dir" add CHANGELOG.md
  git -C "$dir" commit -m "initial commit" >/dev/null 2>&1
  git -C "$dir" tag "v1.0.0"

  python3 "$RELEASE_SCRIPT" minor --dry-run >/dev/null 2>&1
  
  # Ensure changelog was not altered
  grep -q "## \[unreleased\]" "$dir/CHANGELOG.md"
  ! grep -q "## \[1.1.0\]" "$dir/CHANGELOG.md"
}

echo "=== Running github-workflows Test Suite ==="
run_test test_release_version_patch
run_test test_snapshot_version_calculation
run_test test_dry_run_leaves_changelog_intact

echo ""
echo "Total:  $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ "$FAILED_TESTS" -gt 0 ]; then
  exit 1
fi
