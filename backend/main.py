
import requests

from github_reader import (
    HEADERS,
    validate_repo_url,
    discover_files,
    fetch_files,
)
from code_search import search_code


def main():
    repo_url = input("Enter a public GitHub repository URL: ").strip()

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        owner, repo = validate_repo_url(repo_url)

        print(f"\nScanning {owner}/{repo}...")
        branch, paths = discover_files(owner, repo, session)

        print(f"Default branch: {branch}")
        print(f"Eligible files discovered: {len(paths)}")

        files = fetch_files(
            owner, repo, branch, paths, session
        )

        print(f"Files retrieved: {len(files)}")
        print(f"Total characters: {sum(map(len, files.values()))}")
        print("\nRepository loaded! You can now search its code.")

        while True:
            query = input(
                "\nAsk about the code (or type 'exit' to quit): "
            ).strip()

            if query.lower() == "exit":
                print("Goodbye!")
                break

            if not query:
                print("Please enter a question or keyword.")
                continue

            results = search_code(files, query, max_results=10)

            if not results:
                print("No matching code lines found.")
                continue

            print("\nMatching code:")
            for result in results:
                print(
                    f"\n{result['path']}:{result['line_number']}"
                )
                print(f"  {result['line']}")

    except (
        ValueError,
        RuntimeError,
        requests.RequestException,
    ) as error:
        print(f"Error: {error}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
