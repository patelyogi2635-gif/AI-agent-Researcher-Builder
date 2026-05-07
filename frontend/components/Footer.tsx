import { Cpu, Github, Linkedin, ExternalLink } from "lucide-react";

const STACK = [
  "LangGraph", "Groq (llama-3.3-70b)", "Tavily Search",
  "DuckDuckGo", "ChromaDB", "FastAPI", "Next.js 14",
];

const LINKS = [
  { label: "API Docs",    href: "http://localhost:8000/api/docs" },
  { label: "Try Agent",   href: "#agent"                        },
  { label: "Services",    href: "#services"                     },
  { label: "How It Works",href: "#how-it-works"                 },
];

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 pt-14 pb-8">

        {/* Top grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">

          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30">
                <Cpu className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold text-white text-lg">
                Synapse <span className="text-brand-400">AI</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed max-w-xs text-slate-400">
              LangGraph-powered agent system. Research any topic with live web data.
              Build production websites automatically. All free tools.
            </p>
            <div className="flex gap-3 mt-5">
              <a
                href="https://github.com/patelyogi2635-gif"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center hover:bg-slate-700 hover:border-slate-600 transition-colors"
              >
                <Github className="w-4 h-4" />
              </a>
              <a
                href="https://linkedin.com/in/patel-yogi-0a2526346"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center hover:bg-slate-700 hover:border-slate-600 transition-colors"
              >
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Tech stack */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-4 font-display">Tech Stack</h4>
            <ul className="space-y-2">
              {STACK.map((t) => (
                <li key={t} className="text-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-4 font-display">Links</h4>
            <ul className="space-y-2">
              {LINKS.map((l) => (
                <li key={l.label}>
                  <a
                    href={l.href}
                    className="text-sm flex items-center gap-1.5 hover:text-white transition-colors"
                  >
                    {l.label}
                    {l.href.startsWith("http") && (
                      <ExternalLink className="w-3 h-3 opacity-50" />
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-800 pt-6 flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="text-xs text-slate-500">
            Built with LangGraph · Groq · Tavily · ChromaDB · FastAPI · Next.js 14
          </p>
          <p className="text-xs text-slate-600">
            Synapse AI © {new Date().getFullYear()} · All tools free to use
          </p>
        </div>
      </div>
    </footer>
  );
}
