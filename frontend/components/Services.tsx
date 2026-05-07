import {
  Brain, Search, Code2,
  Layers, GitBranch, Zap,
} from "lucide-react";

const SERVICES = [
  {
    icon:  Brain,
    title: "Planning Agent",
    desc:  "Acts as a senior manager. Breaks your goal into ordered steps, assigns tasks to specialist agents, and resolves dependencies automatically using Kahn's topological sort.",
    tag:   "LangGraph",
    bg:    "bg-amber-50",
    fg:    "text-amber-600",
    ring:  "border-amber-100",
  },
  {
    icon:  Search,
    title: "Research Agent",
    desc:  "Searches the live web via Tavily and DuckDuckGo, scrapes full-page content with BeautifulSoup4, and synthesises multi-source findings into structured 6-section reports.",
    tag:   "Tavily + ChromaDB",
    bg:    "bg-cyan-50",
    fg:    "text-cyan-600",
    ring:  "border-cyan-100",
  },
  {
    icon:  Code2,
    title: "Web Builder Agent",
    desc:  "Generates complete HTML/CSS/JS websites from a description. Pulls real content from research reports stored in ChromaDB and self-heals validation errors automatically.",
    tag:   "Groq LLM",
    bg:    "bg-violet-50",
    fg:    "text-violet-600",
    ring:  "border-violet-100",
  },
  {
    icon:  Layers,
    title: "Memory System",
    desc:  "ChromaDB vector store persists all research findings across sessions. The Builder Agent queries it semantically to inject real, researched copy into generated pages.",
    tag:   "ChromaDB",
    bg:    "bg-emerald-50",
    fg:    "text-emerald-600",
    ring:  "border-emerald-100",
  },
  {
    icon:  GitBranch,
    title: "Self-Healing Loops",
    desc:  "Built-in quality reviewer re-triggers search when gaps are found. HTML validator fires the self-healer node on errors. Max 3 correction loops per task — fully autonomous.",
    tag:   "Conditional Edges",
    bg:    "bg-rose-50",
    fg:    "text-rose-600",
    ring:  "border-rose-100",
  },
  {
    icon:  Zap,
    title: "Streaming API",
    desc:  "FastAPI Server-Sent Events stream every node's live progress to the frontend. See exactly which graph and node is executing in real time as your query runs.",
    tag:   "FastAPI + SSE",
    bg:    "bg-brand-50",
    fg:    "text-brand-600",
    ring:  "border-brand-100",
  },
];

export default function Services() {
  return (
    <section id="services" className="py-28 bg-slate-50">
      <div className="max-w-7xl mx-auto px-6">

        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 rounded-full bg-brand-100 text-brand-700 text-sm font-semibold mb-5">
            Platform Capabilities
          </span>
          <h2 className="section-heading mb-4">
            Six intelligent services.
            <br />
            One unified platform.
          </h2>
          <p className="section-sub max-w-2xl mx-auto">
            Each service is a specialist LangGraph agent — modular, observable,
            and production-ready out of the box.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {SERVICES.map((s) => (
            <div
              key={s.title}
              className="card p-6 group cursor-default"
            >
              {/* Icon */}
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center mb-5 ${s.bg} border ${s.ring}`}
              >
                <s.icon className={`w-5 h-5 ${s.fg}`} />
              </div>

              {/* Title + tag */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="font-display font-semibold text-slate-900 text-lg leading-tight">
                  {s.title}
                </h3>
                <span className="shrink-0 text-xs bg-slate-100 text-slate-500 px-2.5 py-0.5 rounded-full border border-slate-200">
                  {s.tag}
                </span>
              </div>

              {/* Description */}
              <p className="text-sm text-slate-500 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
