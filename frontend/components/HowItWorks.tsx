const STEPS = [
  {
    n:    "01",
    title:"Describe your goal",
    desc: "Type any research question or website description in plain English. The Planning Agent reads your intent and auto-detects the mode — research, build, or both.",
    color:"bg-amber-500",
  },
  {
    n:    "02",
    title:"Manager plans the work",
    desc: "The Planning Graph breaks it into ordered steps using dependency resolution — like a senior engineer scoping a sprint. Subtasks are assigned to specialist graphs.",
    color:"bg-brand-600",
  },
  {
    n:    "03",
    title:"Research Agent runs",
    desc: "Live web search via Tavily + DuckDuckGo, full-page scraping, LLM synthesis. Outputs a structured 6-section report saved to ChromaDB for downstream use.",
    color:"bg-cyan-500",
  },
  {
    n:    "04",
    title:"Builder gets real context",
    desc: "Research findings are stored in ChromaDB. The Web Builder queries them semantically and injects real facts and copy into generated pages — no Lorem Ipsum.",
    color:"bg-emerald-500",
  },
  {
    n:    "05",
    title:"Website delivered",
    desc: "Complete HTML/CSS/JS with SEO tags, responsive design, smooth animations, and self-healed validation errors — production-ready in one file.",
    color:"bg-violet-500",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-28 bg-white">
      <div className="max-w-7xl mx-auto px-6">

        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 rounded-full bg-slate-100 text-slate-600 text-sm font-semibold mb-5">
            How It Works
          </span>
          <h2 className="section-heading mb-4">
            From query to output in 5 steps
          </h2>
          <p className="section-sub max-w-xl mx-auto">
            Three LangGraph agents work in sequence, sharing a unified MasterState.
            Every step streams live to your browser.
          </p>
        </div>

        {/* Steps */}
        <div className="max-w-3xl mx-auto relative">
          {/* Vertical connector */}
          <div className="absolute left-5 top-10 bottom-10 w-px bg-gradient-to-b from-amber-300 via-brand-300 to-violet-300 hidden sm:block" />

          <div className="space-y-6">
            {STEPS.map((s) => (
              <div key={s.n} className="flex gap-5 items-start group">
                {/* Number bubble */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-xl ${s.color} text-white flex items-center justify-center text-sm font-bold font-display shadow-lg z-10 group-hover:scale-110 transition-transform duration-200`}
                >
                  {s.n}
                </div>

                {/* Card */}
                <div className="card flex-1 p-5">
                  <h3 className="font-display font-semibold text-slate-900 mb-1.5">
                    {s.title}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
