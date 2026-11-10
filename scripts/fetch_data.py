"""Pull contribution and featured-repo data from the GitHub GraphQL API.

Writes data/contributions.json and data/repos.json for render_readme_cards.py.
Needs a token in GITHUB_TOKEN (the Action passes its own); standard library only.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGIN = "Roushan-2104"
FEATURED = ["Shammy-Notch-For-Windows"]
# Left out of the language ring and "now building": this profile repo and coursework.
SKIP = {"Roushan-2104", "B125103", "B125103-DAA", "Sem1_Assignments", "Project_Sem1"}

ALL_REPOS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        primaryLanguage { name }
        defaultBranchRef { target { ... on Commit {
          history(first: 10) { nodes { messageHeadline committedDate author { user { login } } } }
        } } }
      }
    }
  }
}
"""

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

REPO_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name description url homepageUrl stargazerCount forkCount pushedAt
    primaryLanguage { name color }
    releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount nodes { tagName }
    }
    defaultBranchRef { target { ... on Commit { history { totalCount } } } }
  }
}
"""


def gql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN (locally: GITHUB_TOKEN=$(gh auth token))")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "readme-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]


def main() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cal = gql(QUERY, {"login": LOGIN})["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        {"date": d["date"], "count": d["contributionCount"]}
        for w in cal["weeks"] for d in w["contributionDays"]
    ]
    contributions = {"fetched": now, "total": cal["totalContributions"], "days": days}

    repos = {}
    for name in FEATURED:
        r = gql(REPO_QUERY, {"owner": LOGIN, "name": name})["repository"]
        rel = r["releases"]
        repos[name] = {
            "name": r["name"],
            "description": r["description"] or "",
            "url": r["url"],
            "homepage": r["homepageUrl"] or "",
            "stars": r["stargazerCount"],
            "forks": r["forkCount"],
            "pushed": r["pushedAt"],
            "language": (r["primaryLanguage"] or {}).get("name", ""),
            "language_color": (r["primaryLanguage"] or {}).get("color") or "#888888",
            "releases": rel["totalCount"],
            "latest": rel["nodes"][0]["tagName"] if rel["nodes"] else "",
            "commits": r["defaultBranchRef"]["target"]["history"]["totalCount"],
        }

    # Every owned, non-fork repo, newest push first, for the language ring and "now building".
    owned, cursor = [], None
    while True:
        page = gql(ALL_REPOS_QUERY, {"login": LOGIN, "after": cursor})["user"]["repositories"]
        owned += [r for r in page["nodes"] if r["name"] not in SKIP]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    counts = {}
    for r in owned:
        lang = (r["primaryLanguage"] or {}).get("name")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    languages = {"repos": len(owned), "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1]))}

    # Latest commit that you wrote yourself (bots that commit data, like internship-alerts, are skipped).
    building = {}
    for r in owned:
        target = (r["defaultBranchRef"] or {}).get("target") or {}
        for c in (target.get("history") or {}).get("nodes", []):
            if (c["author"].get("user") or {}).get("login") == LOGIN:
                if not building or c["committedDate"] > building["date"]:
                    building = {"repo": r["name"], "message": c["messageHeadline"], "date": c["committedDate"]}
                break

    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    (out / "contributions.json").write_text(json.dumps(contributions, indent=1) + "\n", encoding="utf-8")
    (out / "repos.json").write_text(json.dumps(repos, indent=1) + "\n", encoding="utf-8")
    (out / "languages.json").write_text(json.dumps(languages, indent=1) + "\n", encoding="utf-8")
    (out / "building.json").write_text(json.dumps(building, indent=1) + "\n", encoding="utf-8")
    print(f"{contributions['total']} contributions over {len(days)} days; repos: {', '.join(repos)}; "
          f"{languages['repos']} repos counted; now building: {building.get('repo')}")


if __name__ == "__main__":
    main()
