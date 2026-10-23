
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
    root_url = f"https://github.com/{owner}/{repo}"
    response = session.get(root_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

        # Try several places because GitHub's HTML can vary.
    branch_meta = soup.select_one(
        'meta[name="octolytics-dimension-repository_default_branch"]'
    )
    branch = branch_meta.get("content") if branch_meta else None

    if not branch:
        branch_meta = soup.select_one(
            'meta[name="github-repository-default-branch"]'
        )
        branch = branch_meta.get("content") if branch_meta else None

    if not branch:
        import re
        match = re.search(
            r'"defaultBranch"\s*:\s*"([^"]+)"',
            response.text
        )
        if match:
            branch = match.group(1)

    if not branch:
        raise RuntimeError(
            "Could not detect the default branch. "
            "Try again later or check the repository page."
        )

    pending_dirs = deque([""])
    visited_dirs = set()
    files = set()

    while pending_dirs and len(files) < MAX_FILES:
        current_dir = pending_dirs.popleft()

        if current_dir in visited_dirs:
            continue

        visited_dirs.add(current_dir)

        if current_dir:
            page_url = (
                f"{root_url}/tree/{quote(branch, safe='')}/"
                f"{quote(current_dir, safe='/')}"
            )
        else:
            page_url = root_url

        try:
            response = session.get(page_url, timeout=REQUEST_TIMEOUT)

            if response.status_code == 404:
                continue

            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Could not scan {current_dir or '/'}: {error}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a[href]"):
            href = unquote(link.get("href", ""))
            prefix_tree = f"/{owner}/{repo}/tree/{branch}/"
            prefix_blob = f"/{owner}/{repo}/blob/{branch}/"

            if href.startswith(prefix_tree):
                path = href[len(prefix_tree):].split("?")[0].strip("/")
                if not path:
                    continue

                parts = path.split("/")
                if any(part.lower() in IGNORED_DIRS for part in parts):
                    continue

                if path not in visited_dirs:
                    pending_dirs.append(path)

            elif href.startswith(prefix_blob):
                path = href[len(prefix_blob):].split("?")[0].strip("/")
                if not path:
                    continue

                parts = path.split("/")
                if any(part.lower() in IGNORED_DIRS for part in parts):
                    continue

                if any(path.lower().endswith(ext) for ext in EXTENSIONS):
                    files.add(path)

                    if len(files) >= MAX_FILES:
                        break

        # Be polite to GitHub and avoid hammering directory pages.
        time.sleep(0.2)

    return branch, sorted(files)[:MAX_FILES]


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
