
import time
from collections import deque
from urllib.parse import urlparse, unquote, quote

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "CodeInsight/0.1"}

EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".c", ".h", ".cs",
    ".go", ".rs", ".php", ".html", ".css",
    ".md", ".json", ".yaml", ".yml", ".toml",
}

IGNORED_DIRS = {
    "node_modules", "venv", ".venv", "dist",
    "build", "__pycache__", "vendor", ".git",
}

MAX_FILES = 100
MAX_FILE_SIZE = 50_000
MAX_TOTAL_CHARS = 300_000
REQUEST_TIMEOUT = 15


def validate_repo_url(url):
    parsed = urlparse(url.strip())

    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError(
            "Use a URL like https://github.com/owner/repo"
        )

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Repository URL must contain owner and repo.")

    owner, repo = parts[:2]
    repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Missing repository owner or name.")

    return owner, repo



def discover_files(owner, repo, session):
    """Discover repository files using GitHub's Git Trees API."""

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Get repository metadata and default branch
    response = session.get(
        api_url,
        headers=HEADERS,
        timeout=(10, 30)
    )
    response.raise_for_status()

    repo_data = response.json()
    branch = repo_data["default_branch"]

    # Get the complete repository tree recursively
    tree_url = (
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/"
        f"{quote(branch, safe='')}"
    )

    response = session.get(
        tree_url,
        headers=HEADERS,
        params={"recursive": "1"},
        timeout=(10, 45)
    )
    response.raise_for_status()

    tree_data = response.json()

    if tree_data.get("truncated"):
        print("Warning: GitHub truncated the repository tree.")

    files = []

    for item in tree_data.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        parts = path.lower().split("/")

        if any(part in IGNORED_DIRS for part in parts):
            continue

        if any(path.lower().endswith(ext) for ext in EXTENSIONS):
            files.append(path)

        if len(files) >= MAX_FILES:
            break

    return branch, sorted(files)


def fetch_files(owner, repo, branch, paths, session):
    result = {}
    total_chars = 0

    for path in paths:
        if total_chars >= MAX_TOTAL_CHARS:
            break

        url = (
            f"https://raw.githubusercontent.com/{owner}/{repo}/"
            f"{quote(branch, safe='')}/{quote(path, safe='/')}"
        )

        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            content = response.content

            if len(content) > MAX_FILE_SIZE:
                print(f"Skipping large file: {path}")
                continue

            # Skip binary files and decode source text safely.
            if b"\x00" in content:
                continue

            text = response.text
            remaining = MAX_TOTAL_CHARS - total_chars
            text = text[:remaining]

            result[path] = text
            total_chars += len(text)

        except requests.RequestException as error:
            print(f"Skipping {path}: {error}")

        time.sleep(0.1)

    return result
