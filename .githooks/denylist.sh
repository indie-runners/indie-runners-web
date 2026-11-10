#!/bin/bash
# Refuse a commit whose added lines or message contain a private term (W-111).
# Terms: one per line, fixed strings, any case, in the MAIN checkout's
# exports/ (untracked), found from worktrees via --git-common-dir.
# Usage: denylist.sh             scan the staged diff's added lines and paths
#        denylist.sh --msg FILE  scan a commit message
set -u
common=$(cd "$(git rev-parse --git-common-dir)" && pwd)
terms="$(dirname "$common")/exports/private-terms.txt"
# A missing file, or one with no non-blank term, would load no terms and pass everything.
if ! grep -q '[^[:space:]]' "$terms" 2>/dev/null; then
    echo "denylist: no term file at $terms; refusing. Create it (one term per line)," >&2
    echo "or commit with --no-verify if you mean to skip the check." >&2
    exit 1
fi
if [ "${1:-}" = "--msg" ]; then
    # '#' lines are scanned too (-m/-F keep them); stop at commit -v's scissors line.
    lines=$(awk '/^# -+ >8 -+$/ { exit } { print "commit message\t" NR "\t" $0 }' "$2")
else
    # file<TAB>line<TAB>text for every added line of the staged diff.
    lines=$(git diff --cached --no-color --no-ext-diff -U0 --diff-filter=d | awk '
        /^diff --git / { h = 1; next }
        h && /^\+\+\+ / { f = substr($0, 7); next }
        /^@@/ { h = 0; split($3, a, ","); n = substr(a[1], 2); next }
        /^\+/ { print f "\t" n "\t" substr($0, 2); n++ }')
    # Paths are public too; a pure rename or a binary file has no +++ line, so ask git.
    paths=$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACR | awk '{ print $0 "\tfilename hit\t" $0 }')
    lines=$(printf '%s\n%s' "$lines" "$paths")
fi
# One pass: fixed-string, case-insensitive; blank term lines are ignored.
hits=$(printf '%s\n' "$lines" | awk -v tf="$terms" '
    BEGIN { while ((getline t < tf) > 0) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", t); if (t != "") T[tolower(t)] = 1 } }
    BEGIN { FS = "\t" }
    { body = tolower(substr($0, length($1 $2) + 3))
      for (t in T) if (index(body, t)) print $1 ":" $2 ": " t }')
if [ -n "$hits" ]; then
    echo "denylist: private term found; commit refused:" >&2
    printf '%s\n' "$hits" >&2
    exit 1
fi
