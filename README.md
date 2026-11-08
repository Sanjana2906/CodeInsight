# CodeInsight – AI-Powered GitHub Repository Exploration



CodeInsight is a web-based platform that helps developers and students explore unfamiliar GitHub repositories and understand their source code. It combines remote repository retrieval, interactive file browsing, keyword-based code search and AI-powered question answering using Google Gemini.

Instead of manually navigating through multiple files, users can enter a public GitHub repository URL, explore its structure, inspect source code and ask questions about the implementation through a single workspace.

## Live Demo

**Application:** https://codeinsight-app.vercel.app/

**GitHub Repository:** https://github.com/rashmideepaktoragallamath/CodeInsight

## Features

- **Remote GitHub Repository Access:** Analyse public GitHub repositories directly through their URLs, without cloning them locally.
- **Automatic File Discovery:** Explore repository directories and identify eligible source files using Breadth-First Search (BFS).
- **Interactive File Explorer:** Browse folders and files through a dynamic directory structure.
- **Source Code Viewer:** Open files and inspect their contents with language identification and line numbers.
- **Keyword-Based Code Retrieval:** Find code sections relevant to a user's question.
- **AI-Powered Question Answering:** Generate repository-specific explanations using the Google Gemini API.
- **Source References:** Display related file paths and line ranges alongside generated answers.
- **Suggested Questions:** Get example questions based on the retrieved repository files.
- **Unified Workspace:** Browse files, inspect code and ask questions in one interface.

## Application Workflow

1. Enter a public GitHub repository URL.
2. The backend validates the URL and identifies the repository.
3. Repository directories and eligible source files are discovered and retrieved remotely.
4. Retrieved files are displayed in the interactive file explorer.
5. Select a file to inspect its source code.
6. Ask a natural-language question about the repository.
7. The backend searches for relevant code sections using keyword matching.
8. The selected code context is sent to Google Gemini along with the question.
9. The generated explanation and related source references are displayed in the workspace.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, CSS |
| Backend | Python, FastAPI, Uvicorn |
| Repository Retrieval | Requests, BeautifulSoup |
| Directory Exploration | Breadth-First Search (BFS) |
| Code Retrieval | Keyword-Based Matching |
| AI Integration | Google Gemini API |
| SDK | Google Gen AI Python SDK |
| Source Platform | GitHub |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |

## Project Structure

```text
CodeInsight/
│
├── backend/
│   ├── api.py
│   ├── github_reader.py
│   ├── code_search.py
│   └── gemini_service.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following:

- Python 3.10 or later
- Node.js and npm
- Git
- Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/rashmideepaktoragallamath/CodeInsight.git

cd CodeInsight
```

### 2. Backend Setup

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the Python dependencies from the project root:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

The API key must remain private. Do not commit the `.env` file.

Start the backend:

```bash
cd backend
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Backend address:

```text
http://127.0.0.1:8000
```

### 3. Frontend Setup

Open a new terminal from the project root:

```bash
cd frontend
npm install
```

Create a `.env.local` file inside the `frontend` directory:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the application at:

```text
http://localhost:5173
```

## Backend API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Check backend availability |
| POST | `/api/analyze` | Validate and analyse a GitHub repository |
| GET | `/api/files` | Retrieve the repository file list |
| GET | `/api/file` | Retrieve an individual file |
| POST | `/api/ask` | Submit a question and receive an AI-generated answer |

## How Code Retrieval Works

CodeInsight uses keyword-based retrieval rather than embedding-based semantic search.

When a user submits a question, the backend searches the retrieved repository files for relevant code sections. The selected context is then provided to Gemini to generate an explanation.

The answer includes related source references so users can inspect the corresponding files and code.

## Deployment

The application uses separate cloud services for its frontend and backend.

- **Frontend:** Deployed on Vercel.
- **Backend:** Deployed on Render.
- **Frontend configuration:** `VITE_API_URL`.
- **Backend configuration:** `GEMINI_API_KEY`.

The frontend communicates with the FastAPI backend through HTTP requests.

## Limitations

- Supports public GitHub repositories only.
- Uses keyword-based retrieval rather than semantic search.
- Does not currently use vector embeddings or a vector database.
- Repository contents are maintained in backend memory during execution.
- File-count, file-size and content limits apply during repository retrieval.
- AI-generated explanations depend on the relevance of retrieved code and may require manual verification.
- The application depends on the availability of the external Gemini API.

## Future Enhancements

- Semantic code retrieval using embeddings.
- Vector database and hybrid search integration.
- Secure support for private GitHub repositories.
- Syntax-aware code analysis.
- Dependency and call-graph analysis.
- Repository architecture visualisation.
- Persistent storage and session management.
- Improved large-repository processing.
- Automated identification of potential bugs and security issues.

## Team Members

- Sanjana M Bhat
- Rashmi T G
- Ruchita D
- Sahithya A P

**Institution:** RV University  
**Department:** School of Computer Science and Engineering  
**Location:** Bengaluru, Karnataka, India

**Project Guide:** Prof. Priyanka S

## Disclaimer

CodeInsight is an academic project developed to support software repository exploration and code understanding. AI-generated explanations should be verified against the original source code and are not a replacement for manual code review.