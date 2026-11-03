
import os
import time
import random
from google import genai

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def create_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Configure it before running CodeInsight."
        )

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": 120000},
    )


def answer_question(client, question, search_results):
    """Generate a repository-grounded answer from retrieved code."""

    if not search_results:
        return "I couldn't find relevant code in the scanned repository."

    context_parts = []

    for result in search_results:
        context_parts.append(
            f"File: {result['path']}\n"
            f"Starting line: {result['line_number']}\n"
            f"Code:\n{result.get('context', result.get('line', ''))}"
        )

    code_context = "\n\n---\n\n".join(context_parts)

    prompt = f"""
You are CodeInsight, a codebase analysis assistant.

Answer the user's question using the supplied repository code.
Explain your reasoning clearly and technically.

Rules:
- Ground claims in the supplied code.
- Mention relevant file paths and line numbers.
- Never invent files, functions, or line numbers.
- If the context is insufficient, explicitly say so.
- Explain how relevant components interact when the evidence supports it.

Question:
{question}

Retrieved repository code:
{code_context}
"""

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            answer = response.text

            if not answer:
                raise RuntimeError("Gemini returned an empty response.")

            return answer

        except Exception as error:
            last_error = error
            error_text = str(error).upper()

            is_temporary = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if not is_temporary or attempt == 2:
                break

            delay = (2 ** (attempt + 1)) + random.uniform(0, 1)
            time.sleep(delay)

    raise RuntimeError(
        f"Gemini could not generate an answer after retries. "
        f"Model: {MODEL_NAME}. Last error: {last_error}"
    )
