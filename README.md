<div align="center">

<img src="https://img.shields.io/badge/Synapse-AI-2563eb?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==&logoColor=white" alt="Synapse AI" />

# Synapse AI

### Research anything. Build anything. AI-powered.

**Autonomous multi-agent system powered by LangGraph — research any topic with live web data and generate production-quality websites in minutes.**

<br/>

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-synapse--ai--delta--coral.vercel.app-2563eb?style=for-the-badge)](https://synapse-ai-delta-coral.vercel.app/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)](https://nextjs.org)

<br/>

![Synapse AI Demo](https://img.shields.io/badge/Status-Production_Ready-34d399?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-orange?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-red?style=flat-square)
![Tavily](https://img.shields.io/badge/Tavily-Search_API-blue?style=flat-square)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-purple?style=flat-square)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Architecture](#-architecture)
- [Agent Graphs](#-agent-graphs)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [How It Works](#-how-it-works)
- [Author](#-author)

---

## 🧠 Overview

**Synapse AI** is a production-grade autonomous AI agent system built with **LangGraph** that can:

- 🔬 **Research** any topic by searching the live web, scraping pages, and synthesising multi-source findings into structured 6-section professional reports
- 🏗️ **Build** complete, responsive websites from a single text description — with real content, animations, and SEO tags
- ✨ **Do Both** — research a topic and automatically inject the real findings into the generated website

The system uses **three specialist LangGraph graphs** orchestrated by a Planning Manager that acts like a senior engineer — breaking goals into ordered steps, resolving dependencies, and dispatching tasks to the right agents.

> Built as a showcase of **production-level AI agent engineering** — not a toy, not a demo.

---

## 🚀 Live Demo

**[https://synapse-ai-delta-coral.vercel.app/](https://synapse-ai-delta-coral.vercel.app/)**

### Example Queries to Try

| Mode | Query |
|------|-------|
| 🔬 Research | `Analyse AI engineer skills needed for freshers in 2026` |
| 🔬 Research | `Research LangGraph vs CrewAI vs AutoGen 2025` |
| 🏗️ Build | `Build a SaaS landing page for a project management tool` |
| ✨ Both | `Research electric vehicles and build a landing page about it` |
| ✨ Both | `Research machine learning trends and build a developer page` |

---

## 🏛 Architecture

```
User Query (Natural Language)
         │
         ▼
┌─────────────────────────────┐
│     🧠 Planning Graph        │  ← Manager Brain
│  task_splitter               │    Breaks goal into ordered steps
│  subtask_generator           │    Resolves dependencies (Kahn's sort)
│  dependency_resolver         │    Assigns to specialist graphs
│  plan_emitter                │
└────────────┬────────────────┘
             │ MasterState (shared TypedDict)
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────┐  ┌──────────────┐
│🔬 Research│  │🏗️ Web Builder│
│  Graph    │  │    Graph     │
│           │  │              │
│ sub_planner  │ requirements │
│ searcher  │  │ wireframe    │
│ scraper   │  │ html_gen     │
│ analyser  │  │ css_styler   │
│ memory    │  │ js_gen       │
│ reviewer  │  │ validator    │
│ reporter  │  │ self_healer  │
└─────┬─────┘  │ seo_enhancer │
      │        └──────┬───────┘
      │               │
      ▼               ▼
┌─────────────────────────────┐
│         ChromaDB            │  ← Shared Vector Memory
│   Research findings stored  │    Builder pulls context
│   for web builder use       │    to inject real content
└─────────────────────────────┘
```

### Data Flow

```
Planning Graph  →  execution_plan[]  →  Orchestrator
Orchestrator    →  per-step state    →  Research Graph
Research Graph  →  findings + keys   →  ChromaDB
ChromaDB        →  research context  →  Web Builder Graph
Web Builder     →  final_html        →  disk (generated_pages/)
FastAPI         →  SSE stream        →  Next.js frontend
```

---

## 🔀 Agent Graphs

### Graph 1 — Planning Graph (Manager Brain)

| Node | Role |
|------|------|
| `task_splitter` | Detects mode (research/builder/both), breaks query into 2-8 tasks |
| `subtask_generator` | Expands each task into concrete subtasks with tool hints |
| `dependency_resolver` | Topological sort (Kahn's algorithm), assigns graphs, generates search queries |
| `plan_emitter` | Emits structured execution plan, sets `next_graph` for orchestrator |

### Graph 2 — Research Graph

| Node | Role |
|------|------|
| `sub_planner` | Sharpens search queries for maximum relevance |
| `searcher` | Tavily API (primary) + DuckDuckGo (fallback) — up to 18 results |
| `scraper` | BeautifulSoup4 fetches full page text from top URLs |
| `analyser` | Groq LLM synthesises into 6-section structured report |
| `memory_writer` | Saves findings to ChromaDB vector store |
| `reviewer` | Quality check — loops back to searcher if gaps found (max 3×) |
| `reporter` | Packages final `ResearchReport` into `MasterState` |

**Self-healing loop:**
```
searcher → scraper → analyser → reviewer
                                    │
                          gaps? ────┘ (max 3 iterations)
                                    │
                          approved? → reporter → END
```

### Graph 3 — Web Builder Graph

| Node | Role |
|------|------|
| `requirements_parser` | Extracts page type, brand, sections, features from description |
| `wireframe_planner` | Plans section layout and component structure |
| `html_generator` | Generates semantic HTML5 with real content |
| `css_styler` | Modern CSS with variables, responsive design, animations |
| `js_generator` | Vanilla JS — smooth scroll, intersection observer, counter animations |
| `validator` | Checks HTML/CSS structure, flags missing elements |
| `self_healer` | LLM patches validation errors, re-routes to validator |
| `seo_enhancer` | Injects meta tags, OG tags, assembles final HTML document |

---

## 🛠 Tech Stack

### All Free Tier

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | Groq — `llama-3.3-70b-versatile` | All language tasks |
| **Agent Framework** | LangGraph 0.2.28 | Graph orchestration |
| **Chain Layer** | LangChain 0.2.16 | LLM wrappers & tools |
| **Web Search** | Tavily API | Primary search (1000 req/month free) |
| **Web Search** | DuckDuckGo Search | Fallback search (no key needed) |
| **Scraping** | BeautifulSoup4 + Requests | Full page content extraction |
| **Vector Store** | ChromaDB | Local persistent research memory |
| **Config** | Pydantic Settings | Type-safe environment config |
| **Backend** | FastAPI + Uvicorn | REST API + SSE streaming |
| **Frontend** | Next.js 14 (App Router) | React UI |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Icons** | Lucide React | Icon library |
| **Deploy Backend** | Railway | Auto-deploy from GitHub |
| **Deploy Frontend** | Vercel | Next.js hosting |

---

## ✨ Features

### Core Capabilities
- ✅ **Multi-mode agent** — research only, build only, or both
- ✅ **Live web search** — real-time data via Tavily + DuckDuckGo
- ✅ **Self-healing** — reviewer loops back when quality insufficient
- ✅ **Research → Website** — ChromaDB passes real facts into generated pages
- ✅ **SSE streaming** — live progress stream to frontend, node by node
- ✅ **Disk persistence** — generated pages survive server restarts

### Research Graph
- ✅ 6-section structured reports (Executive Summary → Recommendations)
- ✅ Real source citations with clickable URLs
- ✅ Multi-query search (up to 5 queries, 18+ results per run)
- ✅ Full-page scraping with noise removal (nav/footer/scripts stripped)
- ✅ Quality reviewer with automatic gap-filling

### Web Builder Graph
- ✅ Complete HTML/CSS/JS in single file
- ✅ Responsive design (mobile + desktop)
- ✅ Smooth scroll, animations, counter effects
- ✅ SEO meta tags + OpenGraph tags
- ✅ Research context injected as real copy
- ✅ Self-healing validator (up to 2 fix passes)

### Platform
- ✅ FastAPI with auto-generated Swagger docs (`/api/docs`)
- ✅ Server-Sent Events for real-time streaming
- ✅ Production Next.js with `next/font` optimisation
- ✅ CORS configured for production domains

---

## 📁 Project Structure

```
ai_agent_system/
├── 📄 .env                          # API keys (never commit)
├── 📄 .env.example                  # Template
├── 📄 .gitignore
├── 📄 requirements.txt              # All Python deps
├── 📄 Procfile                      # Railway start command
├── 📄 runtime.txt                   # Python 3.11.0
│
├── 📁 config/
│   ├── __init__.py
│   └── settings.py                  # Pydantic settings (all env vars)
│
├── 📁 state/
│   ├── __init__.py
│   └── master_state.py              # Shared TypedDict across all graphs
│
├── 📁 graphs/
│   ├── __init__.py
│   ├── 📁 planning/                 # Graph 1 — Manager Brain
│   │   ├── nodes.py                 # 4 nodes
│   │   └── graph.py                 # Compiled LangGraph
│   ├── 📁 research/                 # Graph 2 — Research Agent
│   │   ├── nodes.py                 # 7 nodes + conditional reviewer loop
│   │   └── graph.py
│   └── 📁 builder/                  # Graph 3 — Web Builder Agent
│       ├── nodes.py                 # 8 nodes + self-healer loop
│       └── graph.py
│
├── 📁 api/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app + SSE streaming
│   └── schemas.py                   # Pydantic request/response models
│
├── 📁 utils/
│   ├── __init__.py
│   ├── logger.py                    # Rich structured logging
│   └── parser.py                    # JSON/text extraction helpers
│
├── 📁 generated_pages/              # Built HTML files (gitignored)
├── 📁 chroma_db/                    # Vector store (gitignored)
│
└── 📁 frontend/                     # Next.js 14 App
    ├── next.config.js
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── 📁 app/
    │   ├── layout.tsx               # Root layout + fonts
    │   ├── page.tsx                 # Home page
    │   └── globals.css              # Tailwind + custom CSS
    └── 📁 components/
        ├── Navbar.tsx               # Sticky transparent→white navbar
        ├── Hero.tsx                 # Gradient hero + stats strip
        ├── Services.tsx             # 6 service cards
        ├── HowItWorks.tsx           # 5-step flow
        ├── AgentPanel.tsx           # Live agent UI + SSE + tabs
        └── Footer.tsx               # Dark footer
```

---

## ⚡ Quick Start

### Prerequisites

```
Python 3.11+
Node.js 18+
Git
```

### 1. Clone

```bash
git clone https://github.com/patelyogi2635-gif/synapse-ai.git
cd synapse-ai
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Frontend Setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 4. Run

```bash
# Terminal 1 — Backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)**

---

## 🔑 Environment Variables

Create `.env` in the project root:

```env
# ── LLM (Required) ────────────────────────────────────────────────
# Free at: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_key_here

# ── Web Search (Required) ──────────────────────────────────────────
# Free at: https://app.tavily.com (1000 searches/month)
TAVILY_API_KEY=tvly_your_key_here

# ── App Settings ───────────────────────────────────────────────────
LOG_LEVEL=INFO
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.1
MAX_PLAN_STEPS=10
MAX_SEARCH_RESULTS=5
MAX_SCRAPE_PAGES=5
MAX_REVIEW_LOOPS=3
```

| Variable | Required | Free Tier | Get It |
|----------|----------|-----------|--------|
| `GROQ_API_KEY` | ✅ Yes | Unlimited | [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | ✅ Yes | 1000/month | [app.tavily.com](https://app.tavily.com) |

> DuckDuckGo is used as automatic fallback — no key needed.

---

## 📡 API Reference

Base URL: `https://web-production-dcc87.up.railway.app`

### Health Check
```http
GET /api/health
```
```json
{"status": "ok", "service": "Synapse AI", "version": "1.0.0"}
```

### Run Agent (JSON)
```http
POST /api/run
Content-Type: application/json

{
  "query": "Research machine learning trends in 2025",
  "mode": "research",
  "max_steps": 3
}
```

**Mode options:** `auto` | `research` | `builder` | `both`

### Stream Agent (SSE)
```http
POST /api/stream
Content-Type: application/json

{
  "query": "Build a SaaS landing page for an AI tool",
  "mode": "builder"
}
```

SSE events streamed:
```
data: {"event":"start","graph":"planner","node":"task_splitter","message":"Planning..."}
data: {"event":"done","graph":"research","node":"reporter","message":"Report ready"}
data: {"event":"result","graph":"system","node":"final","message":"Complete","data":{...}}
```

### Get Built Page
```http
GET /api/page/{page_id}
```
Returns full HTML page.

**Interactive Docs:** `/api/docs` (Swagger UI)

---

## 🚀 Deployment

### Backend → Railway

```bash
# 1. Push to GitHub
git push origin main

# 2. Railway Dashboard
#    New Project → Deploy from GitHub → Select repo
#    Settings → Start Command:
#    uvicorn api.main:app --host 0.0.0.0 --port 8000
#    Settings → Networking → Port: 8000

# 3. Add Environment Variables in Railway dashboard
```

### Frontend → Vercel

```bash
# 1. Vercel Dashboard → New Project → Import GitHub repo
#    Root Directory: frontend
#    Framework: Next.js

# 2. Add Environment Variable:
#    NEXT_PUBLIC_API_URL = https://your-app.up.railway.app

# 3. Deploy → get URL like: synapse-ai-xxx.vercel.app
```

### Live URLs

| Service | URL |
|---------|-----|
| 🌐 Frontend | [synapse-ai-delta-coral.vercel.app](https://synapse-ai-delta-coral.vercel.app) |
| ⚙️ API | [web-production-dcc87.up.railway.app](https://web-production-dcc87.up.railway.app) |
| 📄 API Docs | [web-production-dcc87.up.railway.app/api/docs](https://web-production-dcc87.up.railway.app/api/docs) |

---

## 🔄 How It Works

```
1. User types:  "Research EV market and build a landing page"
                              │
2. Planning Graph             │  Detects mode = BOTH
   ├── Splits into 6 tasks    │  Research first, then build
   ├── Generates sub-tasks    │  24 subtasks total
   ├── Topological sort       │  Research → Builder dependency
   └── Emits execution plan   │
                              │
3. Research Graph (×3 steps)  │  Per research step:
   ├── Sharpens queries       │  "EV market 2025 trends"
   ├── Tavily search          │  18 results found
   ├── Scrapes top 5 pages    │  Full article text
   ├── LLM analysis           │  6-section report generated
   ├── ChromaDB save          │  Findings persisted
   └── Quality review         │  Approved ✅
                              │
4. Web Builder Graph          │  Uses research context:
   ├── Requirements parsed    │  Brand: "EV Horizon"
   ├── Wireframe planned      │  5 sections defined
   ├── HTML generated         │  Real EV facts injected
   ├── CSS styled             │  Responsive + animated
   ├── JS added               │  Smooth scroll + counters
   ├── Validated ✅           │  0 errors
   └── SEO enhanced           │  Meta + OG tags added
                              │
5. Output delivered           │  Report + Website
   ├── Research Report        │  Cited, structured
   ├── Website Preview        │  Live iframe
   └── Full Page URL          │  /api/page/page_1
```

---

## 🗺 Roadmap

- [ ] User authentication + saved sessions
- [ ] PDF export of research reports
- [ ] Multi-page website generation
- [ ] Custom domain integration for built pages
- [ ] Debate Agent Graph (pro/con analysis)
- [ ] Data Analysis Agent Graph (CSV → charts → report)
- [ ] API rate limiting + usage dashboard
- [ ] Docker Compose for one-command local setup

---

## 🤝 Contributing

Contributions are welcome!

```bash
# Fork the repo
# Create feature branch
git checkout -b feature/your-feature

# Commit changes
git commit -m "feat: add your feature"

# Push and open PR
git push origin feature/your-feature
```

---

## 📄 License

```
MIT License — free to use, modify, and distribute.
See LICENSE file for details.
```

---

## 👨‍💻 Author

<div align="center">

**Yogi Patel**

*AI/ML Engineer — Gujarat, India*

[![GitHub](https://img.shields.io/badge/GitHub-patelyogi2635--gif-181717?style=for-the-badge&logo=github)](https://github.com/patelyogi2635-gif)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-patel--yogi--0a2526346-0077b5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/patel-yogi-0a2526346)

*Built with LangGraph · Groq · Tavily · ChromaDB · FastAPI · Next.js*

*All tools free to use — zero cost to run*

</div>

---

<div align="center">

⭐ **Star this repo if you found it useful!**

</div>
