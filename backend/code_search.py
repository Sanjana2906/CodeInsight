
import re

STOP_WORDS = {
    "how", "does", "do", "the", "a", "an", "is", "are",
    "what", "where", "when", "why", "work", "works",
    "explain", "show", "me", "in", "of", "for", "to",
    "and", "or", "this", "that", "class", "function",
}


def search_code(files, query, max_results=10):
    """
    Find relevant code snippets, prioritizing matching filenames
    and class/function definitions.
    """
    keywords = [
        word for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query.lower())
        if word not in STOP_WORDS and len(word) > 1
    ]

    if not keywords:
        return []

    candidates = []

    for path, content in files.items():
        lines = content.splitlines()
        path_lower = path.lower()
        file_score = sum(
            5 for keyword in keywords if keyword in path_lower
        )

        for index, line in enumerate(lines):
            line_lower = line.lower()
            matches = [
                keyword for keyword in keywords
                if keyword in line_lower
            ]

            if not matches:
                continue

            score = file_score + len(matches)

            # Strongly prioritize class and function definitions.
            if re.search(r"\bclass\s+session\b", line_lower):
                score += 100

            if any(
                re.search(r"\b" + re.escape(keyword) + r"\b", line_lower)
                for keyword in keywords
            ):
                score += 2

            # Include surrounding code so the result has context.
            start = max(0, index - 5)
            end = min(len(lines), index + 6)

            snippet = "\n".join(
                f"{number + 1}: {lines[number]}"
                for number in range(start, end)
            )

            candidates.append({
                "path": path,
                "line_number": index + 1,
                "line": snippet,
                "matched_keywords": matches,
                "score": score,
            })

    # Most relevant matches first instead of repository order.
    candidates.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    # Avoid returning multiple overlapping snippets from one location.
    results = []
    seen_locations = set()

    for candidate in candidates:
        location = (
            candidate["path"],
            candidate["line_number"] // 10,
        )

        if location in seen_locations:
            continue

        seen_locations.add(location)
        results.append(candidate)

        if len(results) >= max_results:
            break

    return results
