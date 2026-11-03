
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from github_reader import (
    HEADERS,
    validate_repo_url,
    discover_files,
    fetch_files,
)
from code_search import search_code
from gemini_service import create_client, answer_question

app = FastAPI(title="CodeInsight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://codeinsight.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository_data = {}
gemini_client = None


class AnalyzeRequest(BaseModel):
    repo_url: str


class AskRequest(BaseModel):
    question: str


def get_suggestions(files):
    paths = list(files.keys())
    suggestions = []

    if any("readme" in p.lower() for p in paths):
        suggestions.append("Explain the purpose and architecture of this repository.")

    if paths:
        suggestions.append("Identify the main entry points and explain the execution flow.")

    extensions = {p.rsplit(".", 1)[-1].lower() for p in paths if "." in p}

    if extensions & {"py", "js", "ts", "java", "cpp", "go", "rs"}:
        suggestions.append("Explain the most important classes and functions in this codebase.")

    suggestions.append("How are errors and exceptions handled in this repository?")

    return suggestions[:4]


@app.get("/")
def home():
    return {"message": "CodeInsight API is running"}


@app.post("/api/analyze")
def analyze_repository(request: AnalyzeRequest):
    global repository_data

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        owner, repo = validate_repo_url(request.repo_url)
        branch, paths = discover_files(owner, repo, session)
        files = fetch_files(owner, repo, branch, paths, session)

        if not files:
            raise HTTPException(
                status_code=422,
                detail="No eligible source files could be retrieved."
            )

        repository_data = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "files": files,
        }

        return {
            "name": repo,
            "owner": owner,
            "branch": branch,
            "total_files": len(files),
            "files": [
                {
                    "path": path,
                    "language": path.rsplit(".", 1)[-1].lower()
                    if "." in path else "text",
                }
                for path in files
            ],
            "suggestedQuestions": get_suggestions(files),
        }

    except HTTPException:
        raise
    except (ValueError, RuntimeError, requests.RequestException) as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        session.close()


@app.get("/api/files")
def list_files():
    if not repository_data:
        raise HTTPException(status_code=400, detail="Analyze a repository first.")

    return {"files": list(repository_data["files"].keys())}


@app.get("/api/file")
def get_file(path: str):
    if not repository_data:
        raise HTTPException(status_code=400, detail="Analyze a repository first.")

    content = repository_data["files"].get(path)

    if content is None:
        raise HTTPException(status_code=404, detail="File not found.")

    return {"path": path, "content": content}


@app.post("/api/ask")
def ask_question(request: AskRequest):
    global gemini_client

    if not repository_data:
        raise HTTPException(status_code=400, detail="Analyze a repository first.")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        if gemini_client is None:
            gemini_client = create_client()

        results = search_code(
            repository_data["files"],
            request.question,
            max_results=10,
        )

        answer = answer_question(
            gemini_client,
            request.question,
            results,
        )

        return {
            "question": request.question,
            "answer": answer,
            "sources": [
                {
                    "path": result["path"],
                    "startLine": result["line_number"],
                    "endLine": result["line_number"] + 10,
                }
                for result in results
            ],
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
