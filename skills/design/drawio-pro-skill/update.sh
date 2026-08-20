#!/usr/bin/env bash
# drawio-skill auto update check — self-throttled to once per 12 hours.
# Silent when up to date, offline, or not a git checkout.
# Prints a one-line notice only when upstream has new commits.

set -u

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/drawio-skill"
STAMP="$CACHE_DIR/last-check"
THROTTLE_MIN=720  # 12 hours

# Skip if we checked within the throttle window.
if [ -f "$STAMP" ] && [ -z "$(find "$STAMP" -mmin +"$THROTTLE_MIN" 2>/dev/null)" ]; then
  exit 0
fi

mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0
# Refresh timestamp up front so offline / non-git installs don't retry every call.
touch "$STAMP" 2>/dev/null || exit 0

git -C "$SKILL_DIR" rev-parse --git-dir >/dev/null 2>&1 || exit 0

BRANCH="$(git -C "$SKILL_DIR" symbolic-ref --short HEAD 2>/dev/null)" || exit 0
UPSTREAM="$(git -C "$SKILL_DIR" rev-parse --abbrev-ref "${BRANCH}@{upstream}" 2>/dev/null)" || exit 0
REMOTE="${UPSTREAM%%/*}"

git -C "$SKILL_DIR" fetch "$REMOTE" --quiet 2>/dev/null || exit 0

LOCAL="$(git -C "$SKILL_DIR" rev-parse HEAD 2>/dev/null)"
REMOTE_HASH="$(git -C "$SKILL_DIR" rev-parse "$UPSTREAM" 2>/dev/null)"
[ -n "$LOCAL" ] && [ -n "$REMOTE_HASH" ] || exit 0

AHEAD="$(git -C "$SKILL_DIR" rev-list --count "$LOCAL..$REMOTE_HASH" 2>/dev/null || echo 0)"
if [ "${AHEAD:-0}" -gt 0 ]; then
  echo "💡 drawio-skill update available ($AHEAD new commit(s)) — run: cd \"$SKILL_DIR\" && git pull"
fi
