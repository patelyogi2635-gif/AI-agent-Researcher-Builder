"use client";
import { useState, useRef, useEffect } from "react";
import {
  Send, Loader2, FileText, Globe,
  Code2, AlertCircle, ExternalLink, ChevronRight,
} from "lucide-react";
import clsx from "clsx";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Mode = "auto" | "research" | "builder" | "both";
type Tab  = "log" | "report" | "website";

interface LogEntry {
  graph:   string;
  node:    string;
  message: string;
  ts:      string;
  done?:   boolean;
}

const MODE_OPTIONS = [
  { id: "auto"     as Mode, label: "⚡ Auto",            color: "border-amber-300 bg-amber-50 text-amber-700",      placeholder: "Describe what you want — agent decides automatically..." },
  { id: "research" as Mode, label: "🔬 Research Only",   color: "border-cyan-300 bg-cyan-50 text-cyan-700",         placeholder: "e.g. Analyse AI agent frameworks landscape in 2025..." },
  { id: "builder"  as Mode, label: "🏗️ Build Only",     color: "border-violet-300 bg-violet-50 text-violet-700",   placeholder: "e.g. Build a SaaS landing page for a code review tool..." },
  { id: "both"     as Mode, label: "✨ Research + Build", color: "border-emerald-300 bg-emerald-50 text-emerald-700",placeholder: "e.g. Research electric vehicles and build a landing page..." },
];

const GRAPH_COLORS: Record<string, string> = {
  planner:  "text-amber-400",
  research: "text-cyan-400",
  builder:  "text-violet-400",
  system:   "text-emerald-400",
};

const EXAMPLES = [
  { mode: "research" as Mode, q: "Analyse AI engineer skills needed for freshers in 2026" },
  { mode: "builder"  as Mode, q: "Build a SaaS landing page for a project management tool" },
  { mode: "both"     as Mode, q: "Research LangGraph 2025 and build a developer landing page" },
  { mode: "research" as Mode, q: "Best practices for RAG pipelines in production AI systems" },
];

export default function AgentPanel() {
  const [query,      setQuery]      = useState("");
  const [mode,       setMode]       = useState<Mode>("auto");
  const [running,    setRunning]    = useState(false);
  const [logs,       setLogs]       = useState<LogEntry[]>([]);
  const [reports,    setReports]    = useState<any[]>([]);
  const [pages,      setPages]      = useState<any[]>([]);
  const [activeTab,  setActiveTab]  = useState<Tab>("log");
  const [error,      setError]      = useState("");
  const [iframeHtml, setIframeHtml] = useState("");
  const [loadingPage,setLoadingPage]= useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current)
      logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  // Fetch HTML from disk when page_id arrives
  useEffect(() => {
    if (!pages.length || !pages[0]?.page_id) return;
    setLoadingPage(true);
    setIframeHtml("");
    fetch(`${API}/api/page/${pages[0].page_id}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then((html) => setIframeHtml(html))
      .catch((e)  => setError(`Preview failed: ${e.message}`))
      .finally(()  => setLoadingPage(false));
  }, [pages]);

  const addLog = (graph: string, node: string, message: string, done = false) =>
    setLogs((l) => [...l, { graph, node, message, ts: new Date().toLocaleTimeString(), done }]);

  const placeholder = MODE_OPTIONS.find((m) => m.id === mode)?.placeholder ?? "";

  const run = async () => {
    if (!query.trim() || running) return;
    setRunning(true);
    setLogs([]); setReports([]); setPages([]);
    setError(""); setIframeHtml(""); setActiveTab("log");

    try {
      const res = await fetch(`${API}/api/stream`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ query, mode, max_steps: 3 }),
      });
      if (!res.ok) throw new Error(`Server error: HTTP ${res.status}`);

      const reader = res.body!.getReader();
      const dec    = new TextDecoder();
      let   buf    = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const blocks = buf.split("\n\n");
        buf = blocks.pop() || "";

        for (const block of blocks) {
          if (!block.startsWith("data:")) continue;
          try {
            const d    = JSON.parse(block.replace(/^data:\s*/, ""));
            const done = ["done","result","complete"].includes(d.event);
            addLog(d.graph, d.node, d.message, done);

            if (d.event === "result") {
              const rpts = d.data?.reports || [];
              const pgs  = d.data?.pages   || [];
              setReports(rpts);
              setPages(pgs);
              if (rpts.length)      setActiveTab("report");
              else if (pgs.length)  setActiveTab("website");
            }
          } catch { /* ignore */ }
        }
      }
    } catch (e: any) {
      setError(e.message || "Something went wrong");
      addLog("system", "error", e.message);
    } finally {
      setRunning(false);
    }
  };

  const hasOutput = logs.length > 0 || !!error;

  return (
    <section id="agent" className="py-28 bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-7xl mx-auto px-6">

        {/* Header */}
        <div className="text-center mb-12">
          <span className="inline-block px-4 py-1.5 rounded-full bg-brand-100 text-brand-700 text-sm font-semibold mb-5">
            Live Agent
          </span>
          <h2 className="section-heading mb-4">Try Synapse AI now</h2>
          <p className="section-sub max-w-xl mx-auto">
            Real agents, real web search, real output. Not a demo.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">

          {/* Mode pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {MODE_OPTIONS.map((m) => (
              <button key={m.id} onClick={() => setMode(m.id)}
                className={clsx(
                  "px-4 py-1.5 rounded-lg text-sm font-semibold border transition-all duration-150",
                  mode === m.id
                    ? m.color
                    : "border-slate-200 text-slate-500 bg-white hover:border-slate-300"
                )}>
                {m.label}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="flex gap-3 items-end mb-6">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !running) { e.preventDefault(); run(); }}}
              placeholder={placeholder}
              rows={2}
              className="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 transition-all leading-relaxed shadow-sm"
            />
            <button onClick={run} disabled={running || !query.trim()}
              className={clsx("btn-primary px-5 py-3 shrink-0 self-stretch",
                (running || !query.trim()) && "opacity-60 cursor-not-allowed hover:translate-y-0")}>
              {running
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Running</>
                : <><Send className="w-4 h-4" /> Run</>}
            </button>
          </div>

          {/* Output panel */}
          {hasOutput && (
            <div className="card overflow-hidden mb-6">

              {/* Tabs */}
              <div className="flex border-b border-slate-100 bg-slate-50/80">
                {([
                  { id:"log",     label:"Execution Log",   icon:Loader2,  count:logs.length    },
                  { id:"report",  label:"Research Report", icon:FileText, count:reports.length },
                  { id:"website", label:"Built Website",   icon:Globe,    count:pages.length   },
                ] as const).map((t) => (
                  <button key={t.id} onClick={() => setActiveTab(t.id)}
                    className={clsx(
                      "flex items-center gap-2 px-5 py-3.5 text-sm font-medium border-b-2 transition-all",
                      activeTab === t.id
                        ? "border-brand-600 text-brand-600 bg-white"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:bg-white/60"
                    )}>
                    <t.icon className="w-4 h-4" />
                    {t.label}
                    {t.count > 0 && (
                      <span className="text-xs bg-brand-100 text-brand-600 rounded-full px-1.5 py-0.5 font-semibold">
                        {t.count}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* ── LOG ── */}
              {activeTab === "log" && (
                <div ref={logRef} className="h-72 overflow-y-auto bg-slate-900 p-4 space-y-1.5 font-mono">
                  {logs.map((e, i) => (
                    <div key={i} className="flex items-start gap-3 text-xs">
                      <span className="text-slate-500 shrink-0 tabular-nums">{e.ts}</span>
                      <span className={clsx("font-bold shrink-0", GRAPH_COLORS[e.graph] || "text-slate-400")}>
                        [{e.graph}/{e.node}]
                      </span>
                      <span className={clsx("flex-1", e.done ? "text-emerald-400" : "text-slate-300")}>
                        {e.done && "✓ "}{e.message}
                      </span>
                    </div>
                  ))}
                  {running && (
                    <div className="flex items-center gap-2 text-brand-400 text-xs pt-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>Processing...</span>
                    </div>
                  )}
                </div>
              )}

              {/* ── REPORT ── */}
              {activeTab === "report" && (
                <div className="max-h-[560px] overflow-y-auto p-6 space-y-8">
                  {reports.length === 0 ? (
                    <p className="text-slate-400 text-sm text-center py-12">No research reports yet.</p>
                  ) : reports.map((r, i) => (
                    <div key={i}>
                      <div className="flex items-center gap-2 mb-5 pb-3 border-b border-slate-100">
                        <div className="w-6 h-6 rounded-md bg-cyan-100 flex items-center justify-center">
                          <FileText className="w-3.5 h-3.5 text-cyan-600" />
                        </div>
                        <h3 className="font-display font-semibold text-slate-900 flex-1">{r.topic}</h3>
                        <span className="text-xs text-slate-400">{r.sources?.length || 0} sources</span>
                      </div>

                      <div className="space-y-1.5">
                        {r.findings?.split("\n").map((line: string, j: number) => {
                          if (line.startsWith("## "))
                            return <h4 key={j} className="font-display font-semibold text-brand-700 text-sm mt-5 mb-2">{line.replace("## ", "")}</h4>;
                          if (line.match(/^\d+\.\s/) || line.startsWith("- ") || line.startsWith("* "))
                            return <p key={j} className="text-slate-600 text-sm ml-4 leading-relaxed">{line}</p>;
                          if (!line.trim()) return <div key={j} className="h-1.5" />;
                          const parts = line.split(/(\*\*[^*]+\*\*)/g);
                          return (
                            <p key={j} className="text-slate-600 text-sm leading-relaxed">
                              {parts.map((p, k) =>
                                p.startsWith("**") && p.endsWith("**")
                                  ? <strong key={k} className="text-slate-800 font-semibold">{p.slice(2,-2)}</strong>
                                  : p
                              )}
                            </p>
                          );
                        })}
                      </div>

                      {r.sources?.length > 0 && (
                        <div className="mt-5 pt-4 border-t border-slate-100">
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Sources</p>
                          <div className="flex flex-wrap gap-2">
                            {r.sources.slice(0, 6).map((src: string, k: number) => {
                              let host = src;
                              try { host = new URL(src).hostname.replace("www.", ""); } catch {}
                              return (
                                <a key={k} href={src} target="_blank" rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 bg-brand-50 px-2.5 py-1 rounded-full border border-brand-100 transition-colors">
                                  <ExternalLink className="w-2.5 h-2.5" />{host}
                                </a>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* ── WEBSITE ── */}
              {activeTab === "website" && (
                <div>
                  {pages.length === 0 ? (
                    <p className="text-slate-400 text-sm text-center py-12 p-6">No website built yet.</p>
                  ) : (
                    <>
                      {/* Browser toolbar */}
                      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 bg-slate-50">
                        <div className="flex gap-1.5">
                          <div className="w-3 h-3 rounded-full bg-rose-400" />
                          <div className="w-3 h-3 rounded-full bg-amber-400" />
                          <div className="w-3 h-3 rounded-full bg-emerald-400" />
                        </div>
                        <Code2 className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-xs text-slate-500 flex-1 truncate">
                          {pages[0]?.description || "Generated Website"}
                        </span>
                        {pages[0]?.page_id && (
                          <a href={`${API}/api/page/${pages[0].page_id}`}
                            target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-brand-600 hover:underline font-medium">
                            Open full page <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      {/* Preview */}
                      {loadingPage ? (
                        <div className="h-[540px] flex items-center justify-center text-slate-400 text-sm gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" /> Loading preview...
                        </div>
                      ) : iframeHtml ? (
                        <iframe
                          srcDoc={iframeHtml}
                          className="w-full h-[540px] border-0"
                          title="Generated website"
                          sandbox="allow-scripts allow-same-origin"
                        />
                      ) : (
                        <div className="h-[540px] flex items-center justify-center text-slate-400 text-sm">
                          Preview not available
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="flex items-start gap-3 p-4 bg-rose-50 border-t border-rose-100">
                  <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-rose-700">{error}</p>
                </div>
              )}
            </div>
          )}

          {/* Examples */}
          {!hasOutput && (
            <div>
              <p className="text-xs text-slate-400 font-medium mb-3 text-center">Try an example</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {EXAMPLES.map((ex) => {
                  const m = MODE_OPTIONS.find((o) => o.id === ex.mode)!;
                  return (
                    <button key={ex.q}
                      onClick={() => { setQuery(ex.q); setMode(ex.mode); }}
                      className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-brand-300 hover:bg-brand-50/40 transition-all group shadow-sm hover:shadow-md">
                      <span className={clsx("text-xs font-semibold block mb-1.5 px-2 py-0.5 rounded-full w-fit border", m.color)}>
                        {m.label}
                      </span>
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs text-slate-500 group-hover:text-slate-700 leading-relaxed">
                          "{ex.q}"
                        </span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-brand-400 shrink-0 mt-0.5 transition-colors" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </div>
    </section>
  );
}