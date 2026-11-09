#!/usr/bin/env python3
"""List handoffs addressed to the chief of staff that have no reply.

A request is answered when a reply file — `<date>-cos-to-<role>-<slug>.md`
— names the request's filename. That is the whole convention, and it is
deliberately a filename and not a status line: handoffs are read once and
not edited, so the answer has to be a file of its own.

Both spellings of the seat appear in requests (`to-cos`,
`to-chief-of-staff`), so both are matched.

Run from the repo root. Reads docs/handoffs/ only; touches nothing else.
`/cos` uses the full listing; `/triage` uses `--count` for its one-line
nudge.
"""
import sys
from datetime import date
from pathlib import Path

HANDOFFS = Path("docs/handoffs")
REQUEST_MARKERS = ("-to-cos-", "-to-chief-of-staff-")
REPLY_MARKERS = ("-cos-to-", "-chief-of-staff-to-")


def main():
    files = sorted(HANDOFFS.glob("*.md"))
    replies = [f.read_text(encoding="utf-8") for f in files
               if any(m in f.name for m in REPLY_MARKERS)]
    open_requests = [f for f in files
                     if any(m in f.name for m in REQUEST_MARKERS)
                     and not any(f.name in r for r in replies)]

    if "--count" in sys.argv:
        if open_requests:
            oldest = open_requests[0].name[:10]
            print(f"{len(open_requests)} handoff(s) to the chief of staff "
                  f"unanswered, oldest {oldest}")
        else:
            print("0 handoffs to the chief of staff unanswered")
        return

    today = date.today()
    for f in open_requests:
        title = next((line.lstrip("# ").strip()
                      for line in f.read_text(encoding="utf-8").splitlines()
                      if line.startswith("#")), "")
        age = (today - date.fromisoformat(f.name[:10])).days
        print(f"{f}  ({age}d)\n    {title}")
    print(f"\n{len(open_requests)} unanswered")


if __name__ == "__main__":
    main()
