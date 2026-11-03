import { useRef } from "react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  GitFork, Search, GitBranch, ChevronDown, ChevronRight,
  FileCode2, Folder, FolderOpen, MessageSquare, Send,
  Settings, PanelLeftClose, Sparkles, CircleDot, Code2,
  Clock3, Plus, Terminal, ArrowRight, ShieldCheck,
  LoaderCircle,
} from "lucide-react";
import "./App.css";

const API = import.meta.env.VITE_API_URL;

type RepositoryFile = {
  path: string;
  language: string;
  content?: string;
};

type SourceReference = {
  path: string;
  startLine: number;
  endLine: number;
};

type ChatResponse = {
  question: string;
  answer: string;
  sources: SourceReference[];
};

type TreeNode = {
  name: string;
  path: string;
  isFolder: boolean;
  children: TreeNode[];
};

function getLanguage(path: string): string {
  const extension = path.split(".").pop()?.toLowerCase();
  const languages: Record<string, string> = {
    py: "Python", js: "JavaScript", jsx: "JavaScript React",
    ts: "TypeScript", tsx: "TypeScript React", java: "Java",
    cpp: "C++", c: "C", cs: "C#", go: "Go", rs: "Rust",
    php: "PHP", html: "HTML", css: "CSS", json: "JSON",
    md: "Markdown", sql: "SQL", sh: "Shell", yml: "YAML",
    yaml: "YAML", toml: "TOML",
  };
  return languages[extension || ""] || "Text";
}

function buildTree(files: RepositoryFile[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split("/");
    let current = root;
    let currentPath = "";

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      const isFolder = index < parts.length - 1;

      let node = current.find(
        item => item.name === part && item.isFolder === isFolder
      );

      if (!node) {
        node = {
          name: part,
          path: currentPath,
          isFolder,
          children: [],
        };
        current.push(node);
      }

      if (isFolder) current = node.children;
    });
  }

  return root.sort((a, b) => {
    if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repository, setRepository] = useState("");
  const [branch, setBranch] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const workspaceRef = useRef<HTMLElement>(null);
  const [explorerWidth, setExplorerWidth] = useState(240);
  const [analysisWidth, setAnalysisWidth] = useState(420);
  const [repositoryFiles, setRepositoryFiles] = useState<RepositoryFile[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [activeLine, setActiveLine] = useState<number | null>(null);
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [expandedFolders, setExpandedFolders] =
    useState<Set<string>>(new Set());

  const [question, setQuestion] = useState("");
  const [responses, setResponses] = useState<ChatResponse[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [fileSearch, setFileSearch] = useState("");
  const [asking, setAsking] = useState(false);

  async function analyzeRepository() {
    const url = repoUrl.trim();

    if (!/^https:\/\/github\.com\/[^/\s]+\/[^/\s?#]+(?:\.git)?\/?$/.test(url)) {
      setError("Enter a valid public GitHub repository URL.");
      return;
    }

    setError("");
    setLoading(true);
    setResponses([]);
    setRepositoryFiles([]);
    setActiveFile(null);

    try {
      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Repository analysis failed.");
      }

      setRepository(`${data.owner}/${data.name}`);
      setBranch(data.branch);

      const files: RepositoryFile[] = data.files.map(
        (file: { path: string; language?: string }) => ({
          path: file.path,
          language: file.language || getLanguage(file.path),
        })
      );

      setRepositoryFiles(files);
      setSuggestedQuestions(data.suggestedQuestions || []);

      // Expand the root-level view and first-level folders.
      setExpandedFolders(
        new Set(
          files.flatMap(file => {
            const parts = file.path.split("/");
            return parts.slice(0, -1).map((_, index) =>
              parts.slice(0, index + 1).join("/")
            );
          }).filter(path => !path.includes("/", path.indexOf("/") + 1))
        )
      );

      setLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  async function selectFile(path: string) {
    setActiveFile(path);
    setActiveLine(null);

    // Use cached source code if already retrieved.
    if (repositoryFiles.find(file => file.path === path)?.content !== undefined) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/api/file?path=${encodeURIComponent(path)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load file.");
      }

      setRepositoryFiles(previous =>
        previous.map(file =>
          file.path === path
            ? { ...file, content: data.content }
            : file
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "File loading failed.");
    }
  }

  function openFile(path: string) {
    setOpenTabs(previous =>
      previous.includes(path) ? previous : [...previous, path]
    );

    selectFile(path);
  }

  function closeTab(path: string) {
    const updatedTabs = openTabs.filter(tab => tab !== path);

    setOpenTabs(updatedTabs);

    if (activeFile === path) {
      const nextTab = updatedTabs.length
        ? updatedTabs[updatedTabs.length - 1]
        : null;

      if (nextTab) {
        selectFile(nextTab);
      } else {
        setActiveFile(null);
        setActiveLine(null);
      }
    }
  }

  async function askQuestion(value = question) {
    const trimmed = value.trim();
    if (!trimmed || asking) return;

    setQuestion(trimmed);
    setAsking(true);
    setError("");

    try {
      const response = await fetch(`${API}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Question failed.");
      }

      setResponses(previous => [
        ...previous,
        {
          question: trimmed,
          answer: data.answer,
          sources: data.sources || [],
        },
      ]);

      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not get an answer.");
    } finally {
      setAsking(false);
    }
  }

  function toggleFolder(path: string) {
    setExpandedFolders(previous => {
      const next = new Set(previous);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  async function openSource(reference: SourceReference) {
    await selectFile(reference.path);
    setActiveLine(reference.startLine);
  }

  const selectedFile = repositoryFiles.find(
    file => file.path === activeFile
  );

  const tree = buildTree(
    repositoryFiles.filter(file =>
      file.path.toLowerCase().includes(fileSearch.toLowerCase())
    )
  );

  function renderTree(nodes: TreeNode[], depth = 0): React.ReactNode {
    return nodes.map(node => (
      <div key={node.path}>
        {node.isFolder ? (
          <>
            <button
              className="file-item"
              style={{ paddingLeft: `${12 + depth * 16}px` }}
              onClick={() => toggleFolder(node.path)}
              title={node.path}
            >
              {expandedFolders.has(node.path)
                ? <FolderOpen size={16} />
                : <Folder size={16} />}
              <span>{node.name}</span>
              {expandedFolders.has(node.path)
                ? <ChevronDown size={13} />
                : <ChevronRight size={13} />}
            </button>

            {expandedFolders.has(node.path) &&
              renderTree(node.children, depth + 1)}
          </>
        ) : (
          <button
            className={`file-item ${activeFile === node.path ? "selected" : ""}`}
            style={{ paddingLeft: `${12 + depth * 16}px` }}
            onClick={() => openFile(node.path)}
            title={node.path}
          >
            <FileCode2 size={16} />
            <span>{node.name}</span>
          </button>
        )}
      </div>
    ));
  }

  if (!loaded) {
    return (
      <div className="landing">
        <header className="landing-nav">
          <div className="brand">
            <div className="brand-icon"><Code2 size={19} /></div>
            <span>code<span className="brand-light">insight</span></span>
          </div>
          <span className="landing-tag">DEVELOPER WORKSPACE</span>
        </header>

        <main className="landing-main">
          <div className="landing-eyebrow">
            <span className="live-dot" />
            REPOSITORY INTELLIGENCE
          </div>

          <h1>
            Understand code.
            <br />
            <span>Not just read it.</span>
          </h1>

          <p className="landing-description">
            Explore codebases, understand architecture, and trace
            implementation details. Start with any public GitHub repository.
          </p>

          <div className="repo-input-card">
            <label htmlFor="repo-url">PUBLIC GITHUB REPOSITORY</label>

            <div className="repo-input-row">
              <GitFork size={20} />
              <input
                id="repo-url"
                value={repoUrl}
                onChange={e => {
                  setRepoUrl(e.target.value);
                  setError("");
                }}
                onKeyDown={e => {
                  if (e.key === "Enter") analyzeRepository();
                }}
                placeholder="https://github.com/owner/repository"
              />
            </div>

            {error && <p className="input-error">{error}</p>}

            <button
              className="analyze-button"
              onClick={analyzeRepository}
              disabled={loading}
            >
              {loading ? (
                <><LoaderCircle size={17} /> Scanning repository...</>
              ) : (
                <>Analyze repository <ArrowRight size={17} /></>
              )}
            </button>

            <div className="input-note">
              <ShieldCheck size={14} />
              Public repositories only · No Git clone required
            </div>
          </div>

          <div className="landing-features">
            <div><Code2 size={18} /><strong>Code exploration</strong><span>Navigate repository files</span></div>
            <div><Search size={18} /><strong>Contextual search</strong><span>Find relevant implementation</span></div>
            <div><MessageSquare size={18} /><strong>Code understanding</strong><span>Ask questions about code</span></div>
          </div>
        </main>

        <footer className="landing-footer">
          <span>CODEINSIGHT © 2026</span>
          <span>Built for developers, by developers.</span>
        </footer>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon"><Code2 size={19} /></div>
          <span>code<span className="brand-light">insight</span></span>
          <span className="version">WORKSPACE</span>
        </div>

        <div className="top-repo">
          <GitFork size={16} />
          <span>{repository.replace("/", " / ")}</span>
          <ChevronDown size={14} />
          <span className="branch"><GitBranch size={13} /> {branch}</span>
        </div>

        <div className="top-actions">
          <span className="connection"><span /> Repository connected</span>
          <button className="icon-button" title="Settings"><Settings size={17} /></button>
        </div>
      </header>

      <main
        className="workspace"
        ref={workspaceRef}
        style={{
          gridTemplateColumns: `${explorerWidth}px 5px minmax(300px, 1fr) 5px ${analysisWidth}px`
        }}
      >
        <aside className="sidebar">
          <div className="sidebar-heading">
            <span>EXPLORER</span>
            <PanelLeftClose size={16} />
          </div>

          <div className="repo-card">
            <div className="repo-icon"><GitFork size={17} /></div>
            <div className="repo-info">
              <strong>{repository.split("/")[1]}</strong>
              <span>{repository}</span>
            </div>
            <CircleDot size={14} className="green-icon" />
          </div>

          <div className="section-label">
            <span>PROJECT FILES ({repositoryFiles.length})</span>
            <Search size={15} />
          </div>

          <input
            className="file-search"
            placeholder="Find a file..."
            value={fileSearch}
            onChange={e => setFileSearch(e.target.value)}
          />

          <div className="file-tree">
            {repositoryFiles.length === 0
              ? <p className="empty-editor">No files found.</p>
              : renderTree(tree)}
          </div>

          <div className="sidebar-bottom">
            <div className="section-label"><span>WORKSPACE</span></div>
            <div className="nav-item"><Clock3 size={16} /> Recent analysis</div>
            <div className="nav-item"><MessageSquare size={16} /> Saved questions</div>
            <div className="nav-item"><Settings size={16} /> Preferences</div>
          </div>
        </aside>
        <div
          className="resize-handle"
          title="Resize explorer"
          onPointerDown={e => {
            e.currentTarget.setPointerCapture(e.pointerId);
          }}
          onPointerMove={e => {
            if (e.buttons !== 1) return;

            const rect = workspaceRef.current?.getBoundingClientRect();
            if (!rect) return;

            const newWidth = e.clientX - rect.left;
            setExplorerWidth(Math.max(180, Math.min(400, newWidth)));
          }}
        />

        <section className="code-panel">
          <div className="panel-tabs">
            <div className="tabs-list">
              {openTabs.map(path => (
                <div
                  key={path}
                  className={`file-tab ${activeFile === path ? "active-tab" : ""}`}
                  onClick={() => selectFile(path)}
                >
                  <FileCode2 size={15} />

                  <span className="tab-name">
                    {path.split("/").pop()}
                  </span>

                  <button
                    className="close-tab"
                    onClick={e => {
                      e.stopPropagation();
                      closeTab(path);
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div className="panel-breadcrumb">
              {selectedFile?.path || repository}
            </div>
          </div>

          <div className="code-toolbar">
            <div><Code2 size={15} /><span>Source code</span></div>
            <span>{selectedFile ? getLanguage(selectedFile.path) : "—"}</span>
          </div>

          <div className="code-content">
            {selectedFile ? (
              selectedFile.content === undefined ? (
                <div className="empty-editor">
                  <LoaderCircle size={18} /> Loading source code...
                </div>
              ) : (
                selectedFile.content.split("\n").map((line, index) => (
                  <div
                    className={`code-line ${activeLine === index + 1 ? "active-code-line" : ""}`}
                    key={index}
                    onClick={() => setActiveLine(index + 1)}
                  >
                    <span className="line-number">{index + 1}</span>
                    <code>{line || " "}</code>
                  </div>
                ))
              )
            ) : (
              <div className="empty-editor">
                Select a repository file to view its source code.
              </div>
            )}
          </div>

          <div className="code-footer">
            <span>UTF-8</span>
            <span>{selectedFile ? getLanguage(selectedFile.path) : "No language detected"}</span>
            <span>{activeLine ? `Line ${activeLine}` : "No line selected"}</span>
          </div>
        </section>
        
        <div
  className="resize-handle"
  title="Resize analysis panel"
  onPointerDown={e => {
    e.currentTarget.setPointerCapture(e.pointerId);
  }}
  onPointerMove={e => {
    if (e.buttons !== 1) return;

    const rect = workspaceRef.current?.getBoundingClientRect();
    if (!rect) return;

    const newWidth = rect.right - e.clientX;
    setAnalysisWidth(Math.max(320, Math.min(650, newWidth)));
  }}
/>
        
        <aside className="analysis-panel">
          <div className="analysis-header">
            <div>
              <div className="analysis-title">
                <Sparkles size={17} /> Code analysis
              </div>
              <p>Understand your codebase</p>
            </div>

            <button
              className="icon-button"
              title="New conversation"
              onClick={() => {
                setResponses([]);
                setQuestion("");
                setError("");
              }}
            >
              <Plus size={17} />
            </button>
          </div>

          {/* SCROLLABLE CONVERSATION AREA */}
          <div className="analysis-body">

            <div className="welcome-icon">
              <Code2 size={23} />
            </div>

            <h2>Explore this repository</h2>

            <p>
              Ask questions about architecture, functions, execution flow,
              and implementation details.
            </p>

            <div className="suggestion-label">SUGGESTED QUESTIONS</div>

            {suggestedQuestions.map(item => (
              <button
                className="suggestion"
                key={item}
                onClick={() => setQuestion(item)}
              >
                {item}
                <ChevronRight size={15} />
              </button>
            ))}

            {/* AI CONVERSATION RESPONSES */}
            {responses.map((response, index) => (
              <div className="chat-response" key={index}>

                <div className="user-question">
                  <MessageSquare size={15} />
                  <strong>{response.question}</strong>
                </div>

                <div className="markdown-answer">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {response.answer}
                  </ReactMarkdown>
                </div>

                {response.sources.length > 0 && (
                  <div className="source-references">
                    <span>RELATED SOURCE FILES</span>

                    {response.sources.map((source, sourceIndex) => (
                      <button
                        key={`${source.path}-${sourceIndex}`}
                        onClick={() => openSource(source)}
                      >
                        <FileCode2 size={14} />
                        {source.path}
                        <span>
                          L{source.startLine}–{source.endLine}
                        </span>
                        <ArrowRight size={13} />
                      </button>
                    ))}
                  </div>
                )}

              </div>
            ))}

            {/* Error messages remain visible in the conversation */}
            {error && <p className="input-error">{error}</p>}

          </div>

          {/* FIXED QUESTION INPUT AT BOTTOM */}
          <div className="chat-input-area">

            <textarea
              placeholder="Ask about this codebase..."
              rows={3}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  askQuestion();
                }
              }}
            />

            <div className="input-bottom">
              <span>
                {asking
                  ? "Gemini is analyzing..."
                  : "Answers grounded in source code"}
              </span>

              <button
                className="send-button"
                onClick={() => askQuestion()}
                disabled={!question.trim() || asking}
              >
                {asking
                  ? <LoaderCircle size={16} />
                  : <Send size={16} />}
              </button>
            </div>

          </div>
        </aside>

      </main>

      <footer className="statusbar">
        <div><CircleDot size={13} /> Repository connected</div>
        <div><GitBranch size={13} /> {branch}</div>
        <div className="status-right"><Terminal size={13} /> CodeInsight workspace</div>
      </footer>
    </div>
  );
}

export default App;
