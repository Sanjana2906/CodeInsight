
import re


def search_code(files, query, max_results=10):
    """
    Search retrieved repository files for query keywords.

    Returns matching file paths and line numbers.
    """
    keywords = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query.lower())

    if not keywords:
        return []

    results = []

    for path, content in files.items():
        lines = content.splitlines()

        for line_number, line in enumerate(lines, start=1):
            line_lower = line.lower()

            matches = [
                keyword for keyword in keywords
                if keyword in line_lower
            ]

            if matches:
                results.append({
                    "path": path,
                    "line_number": line_number,
                    "line": line.strip(),
                    "matched_keywords": matches,
                })

                if len(results) >= max_results:
                    return results

    return results
