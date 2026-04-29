# GitPulse

A Python CLI tool that analyzes any GitHub profile and generates detailed statistics, charts, and a self-contained HTML report.

**[Portfolio](https://jimmmy-portfolio.vercel.app)**

---

## Features

- **Language Distribution** — Top 15 languages by percentage of code (byte-weighted)
- **Activity Timeline** — Monthly repository creation patterns over time
- **Top Repositories** — Ranked by stars with metadata table
- **Repository Sizes** — Largest repos visualization
- **Topics Cloud** — Most frequently used tags across all repos
- **HTML Report** — Dark-themed, self-contained report with embedded charts
- **JSON Export** — Raw data export for further analysis
- **Pagination** — Handles profiles with unlimited repositories
- **Token Support** — Optional GitHub token for higher rate limits (60 → 5000 req/hour)

## Example Output

```
reports/octocat/
├── report.html          # Self-contained HTML report
├── data.json            # Raw data export
└── charts/
    ├── languages.png    # Language distribution
    ├── activity.png     # Activity timeline
    ├── stars.png        # Top repos by stars
    └── sizes.png        # Largest repos
```

## Tech Stack

- **Python 3.10+**
- **matplotlib** — Chart generation
- **pandas** — Data analysis
- **GitHub REST API v3**

## Getting Started

### Installation

```bash
git clone https://github.com/jimmy-ngome/GitPulse.git
cd GitPulse
pip install -r requirements.txt
```

### Usage

```bash
# Basic usage
python gitpulse.py <username>

# With GitHub token (recommended for better rate limits)
python gitpulse.py <username> -t ghp_xxxxxxxxxxxx

# Custom output directory
python gitpulse.py <username> -o ./my-reports
```

### CLI Options

```
usage: gitpulse.py [-h] [-t TOKEN] [-o OUTPUT] username

positional arguments:
  username              GitHub username to analyze

options:
  -t, --token TOKEN     GitHub personal access token
  -o, --output OUTPUT   Output directory (default: ./reports)
```

### Example

```bash
python gitpulse.py octocat
```

Generates a full report in `reports/octocat/` with:
- Language breakdown (CSS 77.3%, HTML 22.4%, JavaScript 0.2%)
- 6 public repositories analyzed
- 20,149 total stars tracked
- 4 charts and an interactive HTML report

## License

MIT
