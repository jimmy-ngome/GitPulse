# GitPulse

Analyze any GitHub profile and generate a visual report with charts and stats.

![Python](https://img.shields.io/badge/Python-3.10+-3572A5?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## Features

- Fetches all public repos, languages, and activity from the GitHub API
- Calculates language distribution, top repos, activity timeline
- Generates charts (bar charts, timelines) with matplotlib
- Produces a self-contained HTML report with dark theme
- Exports raw data as JSON for further analysis
- Supports GitHub token for higher API rate limits
- Full pagination support (works with any number of repos)

## Quick start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/gitpulse.git
cd gitpulse

# Install dependencies
pip install -r requirements.txt

# Analyze a profile
python gitpulse.py torvalds
```

## Usage

```
usage: gitpulse.py [-h] [-t TOKEN] [-o OUTPUT] username

positional arguments:
  username              GitHub username to analyze

optional arguments:
  -t, --token TOKEN     GitHub personal access token (higher rate limits)
  -o, --output OUTPUT   Output directory (default: ./reports)
```

### Examples

```bash
# Basic usage
python gitpulse.py octocat

# With a GitHub token for more API calls
python gitpulse.py octocat -t ghp_xxxxxxxxxxxx

# Or use an environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
python gitpulse.py octocat

# Custom output directory
python gitpulse.py octocat -o ./my-reports
```

## Output

For each analysis, GitPulse creates a folder in `reports/<username>/` containing:

```
reports/octocat/
  report.html          # Visual HTML report (open in browser)
  data.json            # Raw data for further analysis
  charts/
    languages.png      # Language distribution chart
    activity.png       # Repo creation timeline
    stars.png          # Top repos by stars
    sizes.png          # Largest repos by size
```

## Tech stack

- **Python 3.10+** - Core language
- **matplotlib** - Chart generation
- **pandas** - Data manipulation
- **GitHub REST API** - Data source

## License

MIT
