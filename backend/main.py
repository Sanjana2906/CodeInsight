
import requests

from github_reader import (
    HEADERS,
    validate_repo_url,
    discover_files,
    fetch_files,
)
from code_search import search_code
from gemini_service import create_client, answer_question

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

        print("\nRepository loaded! Ask questions about its code.")
        print("Type 'exit' to quit.")

        client = create_client()

        while True:
            question = input("\nYour question: ").strip()

            if question.lower() == "exit":
                print("Goodbye!")
                break

            if not question:
                print("Please enter a question.")
                continue

            # Find code lines related to the question.
            results = search_code(files, question, max_results=6)

            if not results:
                print(
                    "No matching code lines found. "
                    "Try using important names or keywords from the code."
                )
                continue

            print("\nAnalyzing relevant snippets with Gemini...")

            try:
                answer = answer_question(client, question, results)
                print("\nCodeInsight answer:\n")
                print(answer)

            except Exception as error:
                print(f"Gemini request failed: {error}")

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
