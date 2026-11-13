#!/usr/bin/env python3
"""The Working board: the one place ideas, drive-bys, checks and handoffs live.

Org Project "Working" (indie-runners #2), private, draft items only
(Paulo, 2026-11-13). This file is identical in web, scraper and infra;
change it in all three or in none. Run from inside a checkout: the repo
is read from `origin`, so a role sees and promotes its own Inbox only.

  board.py list live-checks [--bodies]   auditor: Kind Check, Status Live
  board.py list triage [--bodies]        PM: Raw/Shaped ideas, New drive-bys,
                                         handoffs to the PM, and orphans
  board.py list inbox ROLE [--bodies]    handoffs Sent to ROLE (CoS, Developer, ...)
  board.py list all [--bodies]           everything in this Inbox
  board.py show ITEM                     one item, body in full
  board.py add --kind K --title T --body-file F
               [--inbox R] [--status S] [--from ROLE --to ROLE] [--number N]
  board.py set ITEM [--kind K] [--status S] [--inbox R] [--from ROLE]
               [--to ROLE] [--body-file F] [--issue X]
  board.py promote ITEM --title PUBLIC-TITLE --body-file PUBLIC.md [--label L ...]
  board.py promote ITEM --ticket T-###
  board.py selftest

ITEM is an item id (PVTI_...) or an exact title in this Inbox.
`add --kind Check` numbers the title itself: `Check <next> — <title>`,
numbered per Inbox (web and scraper each keep their own sequence).
`--number N` keeps a migrated check's number; a number already on the
board for that Inbox is refused.

Promotion never converts the draft. It creates a new issue from a public
rewrite (title too: the draft's title is not reused), so the draft keeps
its private evidence, and records the issue
URL (or the ticket id, in a repo whose tickets are still files) in the
Issue field. The repo comes from the Inbox field, never from a prompt,
and an item whose Inbox is not this checkout's repo is refused.

The board answers a read sent just after a write from a slightly older
copy (seen 2026-11-13: an item absent for a few seconds after its create,
present after its delete). Writes go by id and are unaffected; re-read
before concluding a write did not land.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile

OWNER, NUMBER = "indie-runners", "2"
REPOS = ("web", "scraper", "infra")
ROLES = ("Paulo", "PM", "Developer", "Auditor", "CoS", "Analyst")
# Status is one GitHub field; which options belong to which Kind is held here.
STATUSES = {
    "Idea": ("Raw", "Shaped", "Promoted", "Dropped"),
    "Drive-by": ("New", "Ticketed", "Dropped"),
    "Check": ("Live", "Retired"),
    "Handoff": ("Sent", "Absorbed"),
}
FIRST = {"Idea": "Raw", "Drive-by": "New", "Check": "Live", "Handoff": "Sent"}
# The last number in each repo's frozen ROUTED_CHECKS.md. Retired checks are
# not migrated, so the board alone could hand out a retired number again.
CHECK_FLOOR = {"web": 59, "scraper": 95, "infra": 0}  # infra: verify at its pass
PROMOTED = {"Idea": "Promoted", "Drive-by": "Ticketed"}
# shortcut: only web's tickets are issues; add a repo here when its
# tickets-are-issues pass lands, until then promotion records a ticket id.
ISSUE_REPOS = ("web",)


def sh(*args, stdin=None):
    r = subprocess.run(args, capture_output=True, text=True, input=stdin)
    if r.returncode:
        sys.exit(f"{' '.join(args[:4])} ...: {r.stderr.strip()}")
    return r.stdout


def gql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        if k.endswith("_file"):  # file contents, so a long body never rides in argv
            args += ["-F", f"{k[:-5]}=@{v}"]
        else:
            args += ["-f", f"{k}={v}"]
    return json.loads(sh(*args))["data"]


def own_repo():
    url = sh("git", "remote", "get-url", "origin").strip()
    m = re.search(r"indie-runners-(web|scraper|infra)(?:\.git)?$", url)
    if not m:
        sys.exit(f"origin {url} is not web, scraper or infra")
    return m.group(1)


def project():
    meta = json.loads(sh("gh", "project", "view", NUMBER, "--owner", OWNER,
                         "--format", "json"))
    fields = json.loads(sh("gh", "project", "field-list", NUMBER, "--owner",
                           OWNER, "--format", "json", "-L", "100"))["fields"]
    return meta["id"], {f["name"]: f for f in fields}


def items():
    d = json.loads(sh("gh", "project", "item-list", NUMBER, "--owner", OWNER,
                      "--format", "json", "-L", "5000"))
    if len(d["items"]) != d["totalCount"]:
        sys.exit(f"read {len(d['items'])} of {d['totalCount']} items; refusing "
                 "to answer from a partial board")
    return d["items"]


# --- pure logic, covered by selftest ---------------------------------------

def view(name, all_items, repo, role=None):
    mine = [i for i in all_items if i.get("inbox") == repo]
    # a half-made item is missing a field; it surfaces in the triage of its
    # Inbox, or of every repo when the Inbox itself is what is missing
    orphan = [i for i in all_items if i.get("inbox") in (repo, None)
              and not (i.get("kind") and i.get("inbox") and i.get("status"))]
    if name == "live-checks":
        return [i for i in mine if i.get("kind") == "Check" and i.get("status") == "Live"]
    if name == "inbox":
        if role not in ROLES:
            sys.exit(f"list inbox needs a role: {', '.join(ROLES)}")
        return [i for i in mine if i.get("kind") == "Handoff"
                and i.get("to") == role and i.get("status") == "Sent"]
    if name == "triage":
        rows = [i for i in mine if i.get("status") in ("Raw", "Shaped", "New")
                or (i.get("kind") == "Handoff" and i.get("to") == "PM"
                    and i.get("status") == "Sent")]
        return rows + [i for i in orphan if i not in rows]
    if name == "all":
        return mine
    sys.exit(f"no view {name}")


def check_numbers(all_items, repo):
    return [int(m.group(1)) for i in all_items
            if i.get("kind") == "Check" and i.get("inbox") == repo
            and (m := re.match(r"Check (\d+)\b", i.get("title", "")))]


def next_check(all_items, repo):
    return max(check_numbers(all_items, repo) + [CHECK_FLOOR[repo]]) + 1


def check_status(kind, status):
    if kind not in STATUSES:
        sys.exit(f"Kind is {kind or 'empty'}; set --kind first")
    if status not in STATUSES[kind]:
        sys.exit(f"{status} is not a {kind} status: {', '.join(STATUSES[kind])}")


def promotion_target(item, repo):
    """The repo an item may be promoted into, or why not. Guard 1 and 2."""
    if item.get("content", {}).get("type") != "DraftIssue":
        return None, "not a draft"
    inbox = item.get("inbox")
    if not inbox:
        return None, "Inbox is empty; set it, do not guess it"
    if inbox != repo:
        return None, (f"Inbox is {inbox}, this checkout is {repo}: "
                      f"{inbox}'s PM promotes it")
    if item.get("kind") not in PROMOTED:
        return None, f"a {item.get('kind')} is not promoted"
    if item.get("status") not in ("Raw", "Shaped", "New"):
        return None, f"status is {item.get('status')}"
    return inbox, None


# --- board writes ------------------------------------------------------------

def set_field(pid, fields, item_id, name, value):
    f = fields[name]
    if "options" in f:
        opt = [o["id"] for o in f["options"] if o["name"] == value]
        if not opt:
            sys.exit(f"{name} has no option {value}")
        val = '{singleSelectOptionId: $v}'
        v = opt[0]
    else:
        val, v = '{text: $v}', value
    gql("mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){updateProjectV2ItemFieldValue("
        f"input:{{projectId:$p,itemId:$i,fieldId:$f,value:{val}}}){{clientMutationId}}}}",
        p=pid, i=item_id, f=f["id"], v=v)


def find(ref, all_items, repo):
    hits = [i for i in all_items if i["id"] == ref] or \
           [i for i in all_items if i.get("title") == ref and i.get("inbox") == repo]
    if len(hits) != 1:
        sys.exit(f"{len(hits)} items match {ref!r}; use the PVTI_ id")
    return hits[0]


def set_body(item, body_file, title=None):
    di = gql("query($i:ID!){node(id:$i){...on ProjectV2Item{content{"
             "...on DraftIssue{id}}}}}", i=item["id"])["node"]["content"]["id"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as t:
        t.write(title or item["title"])  # the API refuses a body edit without its title
        t.flush()
        gql("mutation($d:ID!,$t:String!,$b:String!){updateProjectV2DraftIssue("
            "input:{draftIssueId:$d,title:$t,body:$b}){clientMutationId}}",
            d=di, t_file=t.name, b_file=body_file)


def print_items(rows, bodies):
    for i in rows:
        tags = " / ".join(filter(None, (i.get("kind"), i.get("status"), i.get("inbox"),
                                        i.get("from") and f"{i['from']}→{i.get('to')}",
                                        i.get("issue"))))
        print(f"{i['id']}  {i['title']}\n    {tags or 'NO FIELDS SET'}")
        if bodies:
            print("\n" + i.get("content", {}).get("body", "") + "\n" + "-" * 72)
    print(f"\n{len(rows)} item(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("view"); p.add_argument("role", nargs="?")
    p.add_argument("--bodies", action="store_true")
    p = sub.add_parser("show"); p.add_argument("item")
    p = sub.add_parser("add")
    p.add_argument("--kind", required=True, choices=STATUSES)
    p.add_argument("--title", required=True); p.add_argument("--body-file", required=True)
    p.add_argument("--inbox", choices=REPOS); p.add_argument("--status")
    p.add_argument("--from", dest="frm", choices=ROLES); p.add_argument("--to", choices=ROLES)
    p.add_argument("--number", type=int)
    p = sub.add_parser("set"); p.add_argument("item")
    p.add_argument("--kind", choices=STATUSES); p.add_argument("--status")
    p.add_argument("--inbox", choices=REPOS)
    p.add_argument("--from", dest="frm", choices=ROLES); p.add_argument("--to", choices=ROLES)
    p.add_argument("--body-file"); p.add_argument("--issue")
    p = sub.add_parser("promote"); p.add_argument("item")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--body-file"); g.add_argument("--ticket")
    p.add_argument("--title"); p.add_argument("--label", action="append", default=[])
    sub.add_parser("selftest")
    a = ap.parse_args()

    if a.cmd == "selftest":
        return selftest()
    repo = own_repo()

    if a.cmd == "list":
        return print_items(view(a.view, items(), repo, a.role), a.bodies)
    if a.cmd == "show":
        return print_items([find(a.item, items(), repo)], True)

    pid, fields = project()
    if a.cmd == "add":
        status = a.status or FIRST[a.kind]
        check_status(a.kind, status)
        if a.kind == "Handoff" and not (a.frm and a.to):
            sys.exit("a Handoff needs --from and --to")
        title = a.title
        if a.number and a.kind != "Check":
            sys.exit("--number is for a Check")
        if a.kind == "Check":
            board = items()
            n = a.number or next_check(board, a.inbox or repo)
            if n in check_numbers(board, a.inbox or repo):
                sys.exit(f"Check {n} is already on the board for {a.inbox or repo}")
            title = f"Check {n} — {title}"
        with tempfile.NamedTemporaryFile("w", suffix=".txt") as t:
            t.write(title); t.flush()
            item = gql("mutation($p:ID!,$t:String!,$b:String!){addProjectV2DraftIssue("
                       "input:{projectId:$p,title:$t,body:$b}){projectItem{id}}}",
                       p=pid, t_file=t.name, b_file=a.body_file)
        iid = item["addProjectV2DraftIssue"]["projectItem"]["id"]
        for name, value in (("Kind", a.kind), ("Inbox", a.inbox or repo),
                            ("Status", status), ("From", a.frm), ("To", a.to)):
            if value:
                set_field(pid, fields, iid, name, value)
        print(f"{iid}  {title}")
        return

    item = find(a.item, items(), repo)
    if a.cmd == "set":
        if a.kind:
            set_field(pid, fields, item["id"], "Kind", a.kind)
        if a.status:
            check_status(a.kind or item.get("kind"), a.status)
            set_field(pid, fields, item["id"], "Status", a.status)
        for name, value in (("From", a.frm), ("To", a.to)):
            if value:
                set_field(pid, fields, item["id"], name, value)
        if a.inbox:
            set_field(pid, fields, item["id"], "Inbox", a.inbox)
        if a.issue:
            set_field(pid, fields, item["id"], "Issue", a.issue)
        if a.body_file:
            set_body(item, a.body_file)
        print(f"{item['id']}  updated")
        return

    # promote
    target, why = promotion_target(item, repo)
    if why:
        sys.exit(f"not promoted: {why}")
    if a.ticket:
        link = a.ticket
    elif target not in ISSUE_REPOS:
        sys.exit(f"{target}'s tickets are still files: write the ticket, then "
                 f"promote with --ticket T-###")
    elif not a.title:
        sys.exit("--title: the issue gets a public title, never the draft's")
    else:
        args = ["gh", "issue", "create", "-R", f"{OWNER}/indie-runners-{target}",
                "--title", a.title, "--body-file", a.body_file]
        for label in a.label:
            args += ["--label", label]
        link = sh(*args).strip().splitlines()[-1]
        print(f"created {link}", flush=True)  # before the field writes: a rerun must not make a second
    set_field(pid, fields, item["id"], "Issue", link)
    set_field(pid, fields, item["id"], "Status", PROMOTED[item["kind"]])
    print(f"{item['id']}  {PROMOTED[item['kind']]} as {link}")


def selftest():
    d = {"type": "DraftIssue"}
    board = [
        {"id": "1", "title": "Check 95 — a", "kind": "Check", "status": "Live", "inbox": "scraper", "content": d},
        {"id": "2", "title": "Check 57 — b", "kind": "Check", "status": "Retired", "inbox": "web", "content": d},
        {"id": "3", "title": "idea", "kind": "Idea", "status": "Raw", "inbox": "web", "content": d},
        {"id": "4", "title": "ask", "kind": "Handoff", "status": "Sent", "inbox": "web", "to": "CoS", "content": d},
        {"id": "5", "title": "half made", "content": d},
        {"id": "6", "title": "to pm", "kind": "Handoff", "status": "Sent", "inbox": "web", "to": "PM", "content": d},
    ]
    ids = lambda rows: [r["id"] for r in rows]
    assert ids(view("live-checks", board, "scraper")) == ["1"]
    assert ids(view("live-checks", board, "web")) == []
    assert ids(view("inbox", board, "web", "CoS")) == ["4"]
    assert ids(view("inbox", board, "web", "PM")) == ["6"]
    assert ids(view("inbox", board, "web", "Developer")) == []
    assert check_numbers(board, "scraper") == [95]
    assert ids(view("triage", board, "web")) == ["3", "6", "5"], ids(view("triage", board, "web"))
    assert next_check(board, "scraper") == 96 and next_check(board, "web") == 60
    assert next_check(board, "infra") == 1
    assert next_check([], "scraper") == 96 and next_check([], "web") == 60
    assert promotion_target(board[2], "web") == ("web", None)
    assert promotion_target(board[2], "scraper")[1].startswith("Inbox is web")
    assert promotion_target(board[4], "web")[1].startswith("Inbox is empty")
    assert promotion_target(board[0], "scraper")[1] == "a Check is not promoted"
    assert promotion_target({**board[2], "content": {"type": "Issue"}}, "web")[1] == "not a draft"
    for kind, status in ((None, "Live"), ("Check", "Raw")):
        try:
            check_status(kind, status)
            raise AssertionError(f"{kind}/{status} accepted")
        except SystemExit:
            pass
    print("selftest ok")


if __name__ == "__main__":
    main()
