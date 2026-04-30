#!/usr/bin/env python3
"""
GitPulse - GitHub Profile Analyzer
Analyze any GitHub user's profile: repos, languages, activity, and more.
Generates charts and an HTML report.
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


GITHUB_API = "https://api.github.com"
COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Java": "#b07219", "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051",
    "Lua": "#000080", "R": "#198CE7", "Scala": "#c22d40",
}


def github_get(endpoint, token=None):
    """Make a GET request to the GitHub API with pagination support."""
    results = []
    url = f"{GITHUB_API}{endpoint}"
    separator = "&" if "?" in url else "?"
    url += f"{separator}per_page=100"

    while url:
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, list):
                    results.extend(data)
                else:
                    return data

                # Parse Link header for pagination
                link_header = resp.headers.get("Link", "")
                url = None
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        url = part.split("<")[1].split(">")[0]
        except HTTPError as e:
            if e.code == 403:
                print("Rate limit reached. Use --token for higher limits.")
                sys.exit(1)
            elif e.code == 404:
                print(f"User not found.")
                sys.exit(1)
            raise

    return results


def fetch_profile(username, token=None):
    """Fetch all data for a GitHub user."""
    print(f"Fetching profile for {username}...")
    user = github_get(f"/users/{username}", token)

    print(f"Fetching repositories...")
    repos = github_get(f"/users/{username}/repos?type=owner&sort=updated", token)

    # Fetch languages for each repo
    print(f"Fetching languages for {len(repos)} repos...")
    for i, repo in enumerate(repos):
        if not repo.get("fork"):
            langs = github_get(f"/repos/{username}/{repo['name']}/languages", token)
            repo["languages_detail"] = langs
        else:
            repo["languages_detail"] = {}
        progress = (i + 1) / len(repos) * 100
        print(f"\r  Progress: {progress:.0f}%", end="", flush=True)
    print()

    return user, repos


def analyze(user, repos):
    """Analyze the fetched data and return stats."""
    own_repos = [r for r in repos if not r.get("fork")]
    forked = [r for r in repos if r.get("fork")]

    # Language stats (by bytes)
    lang_bytes = Counter()
    for repo in own_repos:
        for lang, bytes_count in repo.get("languages_detail", {}).items():
            lang_bytes[lang] += bytes_count

    total_bytes = sum(lang_bytes.values()) or 1
    lang_pct = {lang: (b / total_bytes) * 100 for lang, b in lang_bytes.most_common(15)}

    # Stars and forks
    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    total_forks = sum(r.get("forks_count", 0) for r in own_repos)

    # Top repos by stars
    top_repos = sorted(own_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]

    # Activity timeline (repo creation dates)
    creation_dates = []
    for repo in own_repos:
        created = repo.get("created_at")
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            creation_dates.append(dt)

    # Recent activity (last push dates)
    push_dates = []
    for repo in own_repos:
        pushed = repo.get("pushed_at")
        if pushed:
            dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            push_dates.append(dt)

    # Topics
    all_topics = []
    for repo in own_repos:
        all_topics.extend(repo.get("topics", []))
    topic_counts = Counter(all_topics).most_common(15)

    # Repo sizes
    sizes = {r["name"]: r.get("size", 0) for r in own_repos}
    top_sizes = dict(sorted(sizes.items(), key=lambda x: x[1], reverse=True)[:10])

    return {
        "user": user,
        "total_repos": len(own_repos),
        "total_forks": len(forked),
        "total_stars": total_stars,
        "total_forks_count": total_forks,
        "lang_pct": lang_pct,
        "lang_bytes": dict(lang_bytes.most_common(15)),
        "top_repos": top_repos,
        "creation_dates": sorted(creation_dates),
        "push_dates": sorted(push_dates),
        "topic_counts": topic_counts,
        "top_sizes": top_sizes,
    }


def generate_charts(stats, output_dir):
    """Generate matplotlib charts and save them as PNG."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not installed, skipping charts.")
        return {}

    charts = {}
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(exist_ok=True)

    plt.style.use("dark_background")

    # 1. Language distribution (horizontal bar)
    if stats["lang_pct"]:
        fig, ax = plt.subplots(figsize=(10, 6))
        langs = list(reversed(list(stats["lang_pct"].keys())))
        pcts = list(reversed(list(stats["lang_pct"].values())))
        colors = [COLORS.get(l, "#8b8b8b") for l in langs]
        ax.barh(langs, pcts, color=colors, edgecolor="none", height=0.6)
        ax.set_xlabel("% of code")
        ax.set_title("Languages", fontsize=16, fontweight="bold", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for i, v in enumerate(pcts):
            ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=10)
        plt.tight_layout()
        path = charts_dir / "languages.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        charts["languages"] = path

    # 2. Activity timeline (repo creation over time)
    if stats["creation_dates"]:
        fig, ax = plt.subplots(figsize=(10, 4))
        dates = stats["creation_dates"]
        monthly = Counter()
        for d in dates:
            monthly[d.strftime("%Y-%m")] += 1

        months = sorted(monthly.keys())
        counts = [monthly[m] for m in months]
        month_dates = [datetime.strptime(m, "%Y-%m") for m in months]

        ax.bar(month_dates, counts, width=25, color="#58a6ff", edgecolor="none")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        ax.set_title("Repos created over time", fontsize=16, fontweight="bold", pad=15)
        ax.set_ylabel("Repos")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        path = charts_dir / "activity.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        charts["activity"] = path

    # 3. Top repos by stars
    top = stats["top_repos"][:8]
    if top and any(r.get("stargazers_count", 0) > 0 for r in top):
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [r["name"][:20] for r in reversed(top)]
        stars = [r.get("stargazers_count", 0) for r in reversed(top)]
        ax.barh(names, stars, color="#e3b341", edgecolor="none", height=0.6)
        ax.set_xlabel("Stars")
        ax.set_title("Top repos by stars", fontsize=16, fontweight="bold", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        path = charts_dir / "stars.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        charts["stars"] = path

    # 4. Repo sizes
    if stats["top_sizes"]:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = list(reversed(list(stats["top_sizes"].keys())))
        sizes_kb = list(reversed(list(stats["top_sizes"].values())))
        names_short = [n[:20] for n in names]
        ax.barh(names_short, sizes_kb, color="#7c3aed", edgecolor="none", height=0.6)
        ax.set_xlabel("Size (KB)")
        ax.set_title("Largest repos", fontsize=16, fontweight="bold", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        path = charts_dir / "sizes.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        charts["sizes"] = path

    print(f"Generated {len(charts)} charts.")
    return charts


def generate_html_report(stats, charts, output_dir):
    """Generate an HTML report."""
    user = stats["user"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def chart_img(name):
        if name in charts:
            return f'<img src="charts/{name}.png" alt="{name}" style="max-width:100%;border-radius:8px;">'
        return ""

    # Top repos table
    repo_rows = ""
    for r in stats["top_repos"][:10]:
        lang = r.get("language") or "-"
        desc = (r.get("description") or "")[:80]
        repo_rows += f"""<tr>
            <td><a href="{r['html_url']}" target="_blank">{r['name']}</a></td>
            <td>{desc}</td>
            <td>{lang}</td>
            <td>{r.get('stargazers_count', 0)}</td>
            <td>{r.get('forks_count', 0)}</td>
        </tr>"""

    # Topics
    topics_html = ""
    for topic, count in stats["topic_counts"]:
        topics_html += f'<span class="topic">{topic} ({count})</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitPulse Report - {user.get('login', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #0d1117; color: #e6edf3; line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        h2 {{ font-size: 1.4rem; margin: 2rem 0 1rem; color: #58a6ff; }}
        .subtitle {{ color: #8b949e; margin-bottom: 2rem; }}
        .profile {{ display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem;
                    background: #161b22; border-radius: 12px; margin-bottom: 2rem; }}
        .avatar {{ width: 80px; height: 80px; border-radius: 50%; }}
        .profile-info h2 {{ margin: 0; color: #e6edf3; }}
        .profile-info p {{ color: #8b949e; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                       gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: #161b22; padding: 1.2rem; border-radius: 10px; text-align: center; }}
        .stat-card .number {{ font-size: 2rem; font-weight: bold; color: #58a6ff; }}
        .stat-card .label {{ color: #8b949e; font-size: 0.9rem; }}
        .chart {{ background: #161b22; padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 10px;
                 overflow: hidden; }}
        th, td {{ padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid #21262d; }}
        th {{ background: #1c2128; color: #8b949e; font-weight: 600; }}
        td a {{ color: #58a6ff; text-decoration: none; }}
        td a:hover {{ text-decoration: underline; }}
        .topic {{ display: inline-block; background: #1f3a5f; color: #58a6ff; padding: 4px 12px;
                  border-radius: 20px; margin: 4px; font-size: 0.85rem; }}
        .footer {{ text-align: center; color: #484f58; margin-top: 3rem; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>GitPulse Report</h1>
        <p class="subtitle">Generated on {now}</p>

        <div class="profile">
            <img class="avatar" src="{user.get('avatar_url', '')}" alt="avatar">
            <div class="profile-info">
                <h2>{user.get('name', user.get('login', ''))}</h2>
                <p>@{user.get('login', '')} &middot; {user.get('bio') or 'No bio'}</p>
                <p>{user.get('followers', 0)} followers &middot; {user.get('following', 0)} following</p>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{stats['total_repos']}</div>
                <div class="label">Repositories</div>
            </div>
            <div class="stat-card">
                <div class="number">{stats['total_stars']}</div>
                <div class="label">Total Stars</div>
            </div>
            <div class="stat-card">
                <div class="number">{stats['total_forks_count']}</div>
                <div class="label">Total Forks</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(stats['lang_pct'])}</div>
                <div class="label">Languages</div>
            </div>
        </div>

        <h2>Languages</h2>
        <div class="chart">{chart_img('languages')}</div>

        <h2>Activity</h2>
        <div class="chart">{chart_img('activity')}</div>

        <h2>Top Repositories</h2>
        <table>
            <thead><tr><th>Name</th><th>Description</th><th>Language</th><th>Stars</th><th>Forks</th></tr></thead>
            <tbody>{repo_rows}</tbody>
        </table>

        {"<h2>Topics</h2><div>" + topics_html + "</div>" if topics_html else ""}

        <h2>Repo Sizes</h2>
        <div class="chart">{chart_img('sizes')}</div>

        <div class="footer">
            <p>Generated by <strong>GitPulse</strong> &mdash; github.com/gitpulse</p>
        </div>
    </div>
</body>
</html>"""

    report_path = output_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"Report saved to {report_path}")
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="GitPulse - Analyze any GitHub profile and generate a visual report."
    )
    parser.add_argument("username", nargs="?", help="GitHub username to analyze")
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, for higher rate limits)")
    parser.add_argument("-o", "--output", default="./reports", help="Output directory (default: ./reports)")
    args = parser.parse_args()

    username = args.username
    if not username:
        username = input("Enter a GitHub username: ").strip()
        if not username:
            print("No username provided.")
            sys.exit(1)

    token = args.token or os.environ.get("GITHUB_TOKEN")
    output_dir = Path(args.output) / username
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch
    user, repos = fetch_profile(username, token)

    # Analyze
    print("Analyzing data...")
    stats = analyze(user, repos)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"  {user.get('name', user.get('login', ''))} (@{user.get('login', '')})")
    print(f"  {stats['total_repos']} repos | {stats['total_stars']} stars | {len(stats['lang_pct'])} languages")
    print(f"{'=' * 50}")

    top_langs = list(stats["lang_pct"].items())[:5]
    print("\nTop languages:")
    for lang, pct in top_langs:
        bar = "█" * int(pct / 2)
        print(f"  {lang:<15} {bar} {pct:.1f}%")

    # Charts
    charts = generate_charts(stats, output_dir)

    # HTML report
    report_path = generate_html_report(stats, charts, output_dir)

    # Save raw data
    raw_path = output_dir / "data.json"
    raw_data = {
        "username": user.get("login"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repos": stats["total_repos"],
        "total_stars": stats["total_stars"],
        "languages": stats["lang_pct"],
        "top_repos": [
            {"name": r["name"], "stars": r.get("stargazers_count", 0),
             "language": r.get("language"), "url": r["html_url"]}
            for r in stats["top_repos"]
        ],
    }
    raw_path.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nAll outputs saved to {output_dir}/")
    print(f"Open {report_path} in a browser to view the report.")


if __name__ == "__main__":
    main()
