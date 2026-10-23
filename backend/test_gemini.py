
import os
from google import genai

print("1. Checking API key...", flush=True)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

print("2. Connecting to Gemini...", flush=True)
client = genai.Client(api_key=api_key)

code = """
def login(username, password):
    if username == "admin" and password == "123":
        return True
    return False
"""

print("3. Sending code to Gemini...", flush=True)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=f"""
Explain how this function works.
Identify one security weakness and suggest a fix.

Code:
{code}
"""
)

print("\n4. Gemini's response:\n", flush=True)
print(response.text, flush=True)
