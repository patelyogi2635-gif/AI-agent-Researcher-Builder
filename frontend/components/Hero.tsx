import { ArrowRight, Sparkles, Globe, BarChart3, Code2 } from "lucide-react";

const STATS = [
  { icon: Globe,     value: "Tavily + DDG",   label: "Live Web Search"   },
  { icon: BarChart3, value: "Multi-step",      label: "Research Reports"  },
  { icon: Code2,     value: "Production HTML", label: "Auto-Built Pages"  },
];

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">

      {/* Background */}
      <div className="absolute inset-0 -z-10">
        {/* Soft gradient blobs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[900px] h-[700px] bg-gradient-to-r from-brand-500/10 via-indigo-500/8 to-purple-500/8 rounded-full blur-3xl" />
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-100/70 rounded-full blur-3xl -translate-y-1/3 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-100/50 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4" />
        {/* Subtle dot grid */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle, #2563eb18 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-28 w-full">
        <div className="text-center max-w-4xl mx-auto">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-50 border border-brand-100 text-brand-700 text-sm font-medium mb-8 shadow-sm">
            <Sparkles className="w-4 h-4" />
            LangGraph · Groq · Tavily · Powered
          </div>

          {/* Heading */}
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 tracking-tight leading-[1.08] mb-6">
            Research anything.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 via-blue-600 to-indigo-600">
              Build anything.
            </span>
          </h1>

          {/* Subtext */}
          <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            Synapse AI deploys autonomous LangGraph agents that research any topic
            with live web data, then automatically generate production-quality
            websites — in minutes.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-20">
            <a href="#agent" className="btn-primary text-base px-8 py-4">
              Start for Free <ArrowRight className="w-4 h-4" />
            </a>
            <a href="#how-it-works" className="btn-secondary text-base px-8 py-4">
              See How It Works
            </a>
          </div>

          {/* Stats strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
            {STATS.map((s) => (
              <div
                key={s.label}
                className="glass flex flex-col items-center gap-2 px-5 py-4"
              >
                <s.icon className="w-5 h-5 text-brand-600" />
                <span className="text-sm font-bold text-brand-700">{s.value}</span>
                <span className="text-xs text-slate-400">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
