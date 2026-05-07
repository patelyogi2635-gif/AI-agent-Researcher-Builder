# graphs/builder/nodes.py
# -----------------------------------------------------------------
# Web Builder Graph — 8 nodes
#
# Flow:
#   requirements_parser -> wireframe_planner -> html_generator
#   -> css_styler -> js_generator -> validator
#   -> self_healer (conditional) -> seo_enhancer -> END
#
# Key feature: pulls ChromaDB research context and injects real
# copy from the Research Graph into generated pages.
# -----------------------------------------------------------------
from __future__ import annotations

import re
from typing import Any

from langchain_groq import ChatGroq

from config import get_settings
from state import BuiltPage, MasterState, PlanStep
from utils import get_logger, safe_json

log      = get_logger(__name__)
settings = get_settings()


def _llm() -> ChatGroq:
    s = get_settings()
    return ChatGroq(
        model=s.llm_model,
        temperature=0.3,
        api_key=s.groq_api_key,
    )


def _current_builder_step(state: MasterState) -> PlanStep | None:
    plan    = state.get("execution_plan", [])
    current = state.get("current_builder_step", 0)
    if current < len(plan):
        return plan[current]
    return None


def _pull_research_context(topic: str) -> str:
    """Pull relevant research from ChromaDB to inject into website copy."""
    try:
        import chromadb
        client     = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("research_memory")
        results    = collection.query(query_texts=[topic], n_results=3)
        docs       = results.get("documents", [[]])[0]
        return "\n\n---\n\n".join(docs)[:3000] if docs else ""
    except Exception as e:
        log.warning(f"[Builder] ChromaDB pull failed: {e}")
        return ""


# -----------------------------------------------------------------
# NODE 1 — Requirements Parser
# -----------------------------------------------------------------
def requirements_parser(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] requirements_parser started")

    step        = _current_builder_step(state)
    description = step["task"] if step else state.get("website_type", "")
    topic       = state.get("research_topic", description)

    # Pull research context saved by Research Graph
    research_ctx = _pull_research_context(topic)
    if research_ctx:
        log.info(f"[Builder] Pulled {len(research_ctx)} chars from ChromaDB")
    else:
        # Fall back to in-memory reports
        reports = state.get("research_reports", [])
        if reports:
            research_ctx = "\n\n".join(
                r.get("findings", "")[:1500] for r in reports[:2]
            )

    # ── Extract ALL dynamic parts BEFORE f-string (Python 3.10 safe) ──
    ctx_available  = "YES - use real facts below" if research_ctx else "NO - use general knowledge"
    ctx_block      = "Research context:\n" + research_ctx[:2000] if research_ctx else ""
    has_research   = "true" if research_ctx else "false"

    brand_hint = description.split()[:4]
    brand_hint_str = " ".join(brand_hint)

    prompt = f"""Extract website requirements as JSON for this specific product.

    Product description: "{description}"

    Rules:
    - brand_name: MUST be a creative 1-2 word product name derived from "{description}". 
      Examples: "AgentForge" for AI agents, "NexusAI" for AI tools, "FlowMind" for workflow AI.
      NEVER use "AI Platform" or generic names.
    - tagline: specific to "{description}" — what this exact product does
    - key_features: 3 real features specific to this product type
    - tone: professional

    Return ONLY JSON:
    {{
      "page_type": "saas",
      "brand_name": "specific creative name here",
      "tagline": "specific tagline for {description[:50]}",
      "color_scheme": "modern blue light",
      "sections": ["Hero","Features","How It Works","Pricing","CTA","Footer"],
      "key_features": ["feature specific to {brand_hint_str}", "feature 2", "feature 3"],
      "target_audience": "developers and teams",
      "tone": "professional",
      "has_research_data": {has_research}
    }}"""

    try:

        resp = _llm().invoke(prompt)
        reqs = safe_json(resp.content, default={
            "page_type":       "landing",
            "brand_name":      "Synapse AI",
            "tagline":         description[:60],
            "color_scheme":    "clean modern light",
            "sections":        ["Hero", "Features", "How It Works", "CTA", "Footer"],
            "key_features":    ["AI-powered", "Fast", "Reliable"],
            "target_audience": "professionals",
            "tone":            "professional",
            "has_research_data": bool(research_ctx),
        })
        reqs["_description"] = description
    except Exception as e:
        log.warning(f"[Builder] requirements_parser LLM failed: {e}")
        reqs = {
            "page_type":  "landing",
            "brand_name": "AI Platform",
            "tagline":    description,
            "sections":   ["Hero", "Features", "Footer"],
        }

    log.info(
        f"[Builder] requirements: {reqs.get('page_type')} page "
        f"| {len(reqs.get('sections', []))} sections"
    )
    return {
        "build_requirements": reqs,
        "build_research_ctx": research_ctx,
        "build_description":  description,
        "fix_attempts":       0,
        "build_errors":       [],
    }


# -----------------------------------------------------------------
# NODE 2 — Wireframe Planner
# -----------------------------------------------------------------
def wireframe_planner(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] wireframe_planner started")
    reqs = state.get("build_requirements", {})

    prompt = f"""You are a senior UX architect. Create a detailed wireframe plan.

Requirements: {reqs}

For each section, define:
- layout (full-width/split/grid/centered)
- key content elements
- visual treatment (hero image, icons, cards, table, etc.)

Return a concise wireframe plan in plain text - 1-2 lines per section.
Focus on structure, not copy."""

    try:
        resp      = _llm().invoke(prompt)
        wireframe = resp.content
    except Exception as e:
        sections  = reqs.get("sections", ["Hero", "Features", "Footer"])
        wireframe = "\n".join(
            f"{s}: full-width section with heading and content" for s in sections
        )

    log.info(f"[Builder] wireframe: {len(wireframe)} chars")
    return {"build_wireframe": wireframe}


# -----------------------------------------------------------------
# NODE 3 — HTML Generator
# -----------------------------------------------------------------
def html_generator(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] html_generator started")

    reqs     = state.get("build_requirements", {})
    wire     = state.get("build_wireframe", "")
    ctx      = state.get("build_research_ctx", "")
    desc     = state.get("build_description", "")
    sections = reqs.get("sections", ["Hero", "Features", "Footer"])
    brand    = reqs.get("brand_name", "AI Platform")
    tagline  = reqs.get("tagline", desc[:60])
    features = reqs.get("key_features", [])

    # Extract before f-string — Python 3.10 safe
    ctx_block = "USE THESE REAL FACTS in copy:\n" + ctx[:1500] if ctx else ""

    prompt = f"""Write complete semantic HTML5 for a professional website.

Brand: {brand}
Tagline: {tagline}
Sections: {sections}
Wireframe: {wire[:500]}
Key features: {features}
{ctx_block}

Rules:
- Output ONLY the HTML body content (no <html>, <head>, <body> tags)
- Use semantic tags: <header>, <nav>, <main>, <section id="...">, <footer>
- Give each section a unique id matching the section name in lowercase
- Add class names that CSS can target: .hero, .features-grid, .stat-card etc.
- Use REAL meaningful content - no Lorem Ipsum
- Include a working responsive navigation with smooth scroll links
- Add data-animate attribute to elements that should animate on scroll"""

    try:
        resp = _llm().invoke(prompt)
        html = resp.content.strip()
        html = re.sub(r"```html?|```", "", html).strip()

        html = re.sub(r"(?i)<!DOCTYPE[^>]*>", "", html).strip()
        html = re.sub(r"(?i)<html[^>]*>|</html>", "", html).strip()
        body_match = re.search(r"(?is)<body[^>]*>(.*?)</body>", html)
        if body_match:
            html = body_match.group(1).strip()
        html = re.sub(r"(?is)<head>.*?</head>", "", html).strip()

    except Exception as e:
        log.warning(f"[Builder] html_generator LLM failed: {e}")
        html = f"<section><h1>{brand}</h1><p>{tagline}</p></section>"

    log.info(f"[Builder] html: {len(html)} chars")
    return {"build_html": html}


# -----------------------------------------------------------------
# NODE 4 — CSS Styler
# -----------------------------------------------------------------
def css_styler(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] css_styler started")
    reqs  = state.get("build_requirements", {})
    tone  = reqs.get("tone", "professional")
    ptype = reqs.get("page_type", "landing")

    prompt = f"""Write complete modern CSS for a {tone} {ptype} website.

Requirements:
- Light theme with clean white/light grey backgrounds
- Primary accent: professional blue (#2563EB) or indigo
- Google Fonts import (Inter for body, Poppins or Sora for headings)
- CSS custom properties for all colours at :root
- Fully responsive: mobile-first, breakpoints at 768px and 1200px
- Navigation: sticky, transparent to white on scroll effect via CSS
- Hero: gradient background, large heading, subtext, CTA buttons
- Feature cards: glassmorphism or clean card with subtle shadow
- Smooth CSS animations: fade-in on scroll (use Intersection Observer classes)
- Stats section: large numbers with subtle background
- Footer: dark background, multi-column layout
- CSS transitions on all interactive elements
- No external CSS frameworks - pure CSS only

Output ONLY the CSS. Start with @import for Google Fonts."""

    try:
        resp = _llm().invoke(prompt)
        css  = resp.content.strip()
        css  = re.sub(r"```css|```", "", css).strip()
    except Exception as e:
        log.warning(f"[Builder] css_styler LLM failed: {e}")
        css  = ":root{--primary:#2563EB;--bg:#fff;--text:#1e293b} body{font-family:system-ui;margin:0}"

    log.info(f"[Builder] css: {len(css)} chars")
    return {"build_css": css}


# -----------------------------------------------------------------
# NODE 5 — JS Generator
# -----------------------------------------------------------------
def js_generator(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] js_generator started")

    prompt = """Write clean vanilla JavaScript for a modern landing page.

Include ALL of these:
1. Smooth scroll navigation
2. Sticky navbar: add .scrolled class on window scroll > 50px
3. Intersection Observer: add .visible class to [data-animate] elements
4. Mobile hamburger menu toggle
5. Counter animation for stat numbers (count up on visible)
6. Active nav link highlight based on scroll position
7. Optional: typing effect for hero headline (if #hero-headline exists)

Rules:
- Vanilla JS only - no jQuery, no frameworks
- Use DOMContentLoaded wrapper
- Add null checks before all DOM queries
- Comments explaining each feature

Output ONLY the JavaScript."""

    try:
        resp = _llm().invoke(prompt)
        js   = resp.content.strip()
        js   = re.sub(r"```javascript?|```js|```", "", js).strip()
    except Exception as e:
        log.warning(f"[Builder] js_generator LLM failed: {e}")
        js   = "document.addEventListener('DOMContentLoaded',()=>{console.log('Page loaded')});"

    log.info(f"[Builder] js: {len(js)} chars")
    return {"build_js": js}


# -----------------------------------------------------------------
# NODE 6 — Validator
# -----------------------------------------------------------------
def validator(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] validator started")
    html   = state.get("build_html", "")
    css    = state.get("build_css", "")
    js     = state.get("build_js", "")
    errors = []

    # Structural HTML checks
    required_tags = ["<section", "<header", "<footer", "<nav"]
    for tag in required_tags:
        if tag not in html.lower():
            errors.append(f"Missing semantic tag: {tag}")

    # CSS checks
    required_css = ["@import", ":root", "@media", "font-family"]
    for rule in required_css:
        if rule not in css:
            errors.append(f"Missing CSS rule: {rule}")

    # JS checks
    if "DOMContentLoaded" not in js and len(js) > 50:
        errors.append("JS missing DOMContentLoaded wrapper")

    # Minimum content check
    if len(html) < 200:
        errors.append("HTML too short - likely generation failed")

    if errors:
        log.warning(f"[Builder] validator: {len(errors)} issues found: {errors}")
    else:
        log.info("[Builder] validator: PASSED")

    return {"build_errors": errors}


def route_validator(state: MasterState) -> str:
    """Conditional edge: route to self_healer or seo_enhancer."""
    errors   = state.get("build_errors", [])
    attempts = state.get("fix_attempts", 0)
    if errors and attempts < 2:
        return "self_healer"
    return "seo_enhancer"


# -----------------------------------------------------------------
# NODE 7 — Self-Healer
# -----------------------------------------------------------------
def self_healer(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] self_healer started")
    errors   = state.get("build_errors", [])
    html     = state.get("build_html", "")
    css      = state.get("build_css", "")
    attempts = state.get("fix_attempts", 0)

    # Extract before f-string — Python 3.10 safe (no backslash in expression)
    errors_text = "\n".join("- " + e for e in errors)
    html_preview = html[:1500]
    css_preview  = css[:500]

    prompt = f"""Fix these specific issues in the website code:

ERRORS TO FIX:
{errors_text}

CURRENT HTML (first 1500 chars):
{html_preview}

CURRENT CSS (first 500 chars):
{css_preview}

Fix ONLY the issues listed. Return a JSON object:
{{
  "html_fix": "corrected HTML additions or replacements",
  "css_fix": "corrected CSS additions",
  "fixed_errors": ["error 1 fixed", "error 2 fixed"]
}}"""

    try:
        resp = _llm().invoke(prompt)
        data = safe_json(resp.content, default={})

        if data.get("html_fix"):
            html = html + "\n<!-- HEALED -->\n" + data["html_fix"]
        if data.get("css_fix"):
            css  = css + "\n/* HEALED */\n" + data["css_fix"]

        fixed = data.get("fixed_errors", [])
        log.info(f"[Builder] self_healer: fixed {len(fixed)} issues")
    except Exception as e:
        log.warning(f"[Builder] self_healer LLM failed: {e}")

    return {
        "build_html":   html,
        "build_css":    css,
        "fix_attempts": attempts + 1,
        "build_errors": [],
    }


# -----------------------------------------------------------------
# NODE 8 — SEO Enhancer
# Assembles the final complete HTML document with meta tags.
# -----------------------------------------------------------------
def seo_enhancer(state: MasterState) -> dict[str, Any]:
    log.info("[Builder] seo_enhancer started")

    reqs  = state.get("build_requirements", {})
    html  = state.get("build_html", "")
    js    = state.get("build_js", "")
    brand = reqs.get("brand_name", "AI Platform")
    tag   = reqs.get("tagline", "")
    desc  = reqs.get("tagline", "AI-powered platform")

    step     = _current_builder_step(state)
    step_num = step["step"] if step else 0
    title    = brand + " - " + tag[:50] if tag else brand

    # ── Strip full HTML wrapper from LLM output ──────────────────
    html = re.sub(r"(?i)<!DOCTYPE[^>]*>", "", html).strip()
    html = re.sub(r"(?i)<html[^>]*>|</html>", "", html).strip()
    body_m = re.search(r"(?is)<body[^>]*>(.*?)</body>", html)
    if body_m:
        html = body_m.group(1).strip()
    html = re.sub(r"(?is)<head>.*?</head>", "", html).strip()
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", "", html).strip()

    # ── Guaranteed CSS — LLM css discarded (too unreliable) ──────
    safe_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --primary: #2563eb; --primary-dark: #1d4ed8;
  --bg: #ffffff; --bg2: #f8fafc; --bg3: #eff6ff;
  --text: #1e293b; --text2: #475569; --text3: #94a3b8;
  --border: #e2e8f0; --radius: 12px;
}
html { scroll-behavior: smooth; }
body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; font-size: 16px; }
h1,h2,h3,h4,h5,h6 { font-family: 'Sora', sans-serif; color: #0f172a; line-height: 1.2; font-weight: 700; margin-bottom: 1rem; }
h1 { font-size: clamp(2rem, 5vw, 3.5rem); }
h2 { font-size: clamp(1.5rem, 3vw, 2.5rem); }
h3 { font-size: 1.25rem; }
p  { color: var(--text2); margin-bottom: 1rem; }
a  { color: var(--primary); text-decoration: none; }
a:hover { color: var(--primary-dark); }
img { max-width: 100%; display: block; }
ul,ol { padding-left: 1.5rem; color: var(--text2); }
li { margin-bottom: 0.5rem; }
strong { color: var(--text); font-weight: 600; }

/* Layout */
.container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }
section { padding: 5rem 1.5rem; }

/* Navbar */
header, nav {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,0.95); backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
  padding: 1rem 2rem; display: flex;
  justify-content: space-between; align-items: center;
}
nav a, header a { color: var(--text); font-weight: 500; margin-left: 1.5rem; transition: color .2s; }
nav a:hover, header a:hover { color: var(--primary); }
.logo, .brand { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.25rem; color: var(--primary) !important; }

/* Hero */
.hero, [class*="hero"], #hero {
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 50%, #faf5ff 100%);
  min-height: 85vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center; padding: 6rem 1.5rem;
}
.hero h1, [class*="hero"] h1, #hero h1 { color: #1e3a8a; font-size: clamp(2.5rem,6vw,4.5rem); margin-bottom: 1.5rem; }
.hero p,  [class*="hero"] p,  #hero p  { color: #475569; font-size: 1.2rem; max-width: 650px; margin: 0 auto 2.5rem; }

/* Buttons */
.btn, button:not([class*="nav"]) {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.875rem 2rem; border-radius: var(--radius);
  font-weight: 600; font-size: 1rem; cursor: pointer; border: none;
  transition: all .2s; text-decoration: none;
}
.btn-primary, .cta-btn, .primary-btn, [class*="btn-primary"] {
  background: var(--primary); color: #fff !important;
  box-shadow: 0 4px 14px rgba(37,99,235,0.3);
}
.btn-primary:hover, .cta-btn:hover { background: var(--primary-dark); transform: translateY(-2px); }
.btn-secondary, [class*="btn-secondary"] {
  background: #fff; color: var(--text) !important;
  border: 2px solid var(--border);
}

/* Cards */
.card, [class*="card"], .feature, [class*="feature-item"] {
  background: #fff; border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: box-shadow .2s, transform .2s;
}
.card:hover, [class*="card"]:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.1); transform: translateY(-4px); }
.card h3, [class*="card"] h3 { color: #1e40af; margin-bottom: 0.75rem; }

/* Grids */
.grid, .features-grid, [class*="grid"] {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}
.flex, [class*="flex"] { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }

/* Sections */
.features, #features, [id*="feature"], [class*="features"] { background: var(--bg2); }
.stats, #stats, [class*="stats"] { background: var(--bg3); text-align: center; }
.stat-number, [class*="stat-num"] { font-size: 3rem; font-weight: 800; color: var(--primary); }
.how-it-works, #how-it-works, [id*="how"] { background: #fff; }

/* Steps */
.step, [class*="step"] { display: flex; gap: 1.5rem; align-items: flex-start; margin-bottom: 2rem; }
.step-number, [class*="step-num"] {
  width: 3rem; height: 3rem; border-radius: 0.75rem;
  background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 1.1rem; flex-shrink: 0;
}

/* CTA section */
.cta, #cta, [class*="cta-section"] {
  background: linear-gradient(135deg, #1e3a8a, #2563eb);
  color: #fff; text-align: center; padding: 6rem 1.5rem;
}
.cta h2, #cta h2 { color: #fff !important; }
.cta p,  #cta p  { color: rgba(255,255,255,0.85); }

/* Footer */
footer {
  background: #0f172a; color: #94a3b8;
  padding: 4rem 1.5rem 2rem; text-align: center;
}
footer h3, footer h4 { color: #fff; margin-bottom: 1rem; }
footer a { color: #93c5fd; }

/* Badges / Tags */
.badge, .tag, [class*="badge"] {
  display: inline-block; padding: 0.25rem 0.875rem;
  border-radius: 999px; font-size: 0.875rem; font-weight: 600;
  background: var(--bg3); color: var(--primary); border: 1px solid #bfdbfe;
}

/* Utilities */
.text-center { text-align: center; }
.mx-auto     { margin-left: auto; margin-right: auto; }
.max-w-2xl   { max-width: 42rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-8 { margin-bottom: 2rem; }
.mt-4 { margin-top: 1rem; }
.mt-8 { margin-top: 2rem; }
.py-4 { padding-top:1rem; padding-bottom:1rem; }
.gap-4 { gap: 1rem; }

/* Animations */
@keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
[data-animate] { opacity:0; transform:translateY(20px); transition: opacity .6s ease, transform .6s ease; }
[data-animate].visible { opacity:1; transform:translateY(0); }

/* Mobile */
@media (max-width: 768px) {
  header, nav { flex-direction: column; gap: 1rem; text-align: center; }
  nav a, header a { margin-left: 0; }
  h1 { font-size: 2rem; }
  .hero { min-height: auto; padding: 4rem 1rem; }
  section { padding: 3rem 1rem; }
}
"""

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'  <meta name="description" content="{desc}">',
        f'  <meta property="og:title" content="{title}">',
        f'  <title>{title}</title>',
        "  <style>",
        safe_css,
        "  </style>",
        "</head>",
        "<body>",
        html if html.strip() else _generate_body(
            brand, tag,
            {**reqs, "_description": state.get("build_description", state.get("user_query", brand))},
            state.get("build_research_ctx", "")
        ),
        "<script>",
        js,
        "</script>",
        "</body>",
        "</html>",
    ]
    final_html = "\n".join(html_parts)

    page = BuiltPage(
        step_id=step_num, description=state.get("build_description", ""),
        html=final_html, css_lines=len(safe_css.split("\n")), js_lines=len(js.split("\n")),
    )
    log.info(f"[Builder] seo_enhancer: {len(final_html)} chars")
    return {
        "built_pages": state.get("built_pages", []) + [page],
        "build_html": "", "build_css": "", "build_js": "",
        "build_errors": [], "build_wireframe": "",
    }


def _fallback_html(brand: str, tag: str, reqs: dict) -> str:
    """Guaranteed visible fallback if html is empty."""
    features = reqs.get("key_features", ["Fast", "Reliable", "AI-Powered"])
    cards = "".join(f'<div class="card"><h3>{f}</h3><p>Core capability of {brand}.</p></div>' for f in features[:3])
    return f"""
<header><span class="logo">{brand}</span><nav><a href="#features">Features</a><a href="#cta">Get Started</a></nav></header>
<section class="hero">
  <div class="badge">AI-Powered Platform</div>
  <h1>{brand}</h1>
  <p>{tag or "The intelligent platform built for the future."}</p>
  <a href="#features" class="btn btn-primary">Explore Features</a>
</section>
<section id="features" class="features">
  <div class="container">
    <h2 class="text-center">What We Offer</h2>
    <div class="grid" style="margin-top:2rem">{cards}</div>
  </div>
</section>
<section id="cta" class="cta">
  <h2>Ready to get started?</h2>
  <p>Join thousands using {brand} today.</p>
  <a href="#" class="btn btn-primary" style="margin-top:1.5rem">Get Started Free</a>
</section>
<footer><p>&copy; 2025 {brand}. All rights reserved.</p></footer>
"""

def _generate_body(brand: str, tag: str, reqs: dict, ctx: str) -> str:
    description = reqs.get("_description", f"{brand} — {tag}")
    features    = reqs.get("key_features", [])
    audience    = reqs.get("target_audience", "professionals")
    ctx_block   = f"USE THESE REAL FACTS:\n{ctx[:2000]}" if ctx else ""

    prompt = f"""Generate a complete HTML landing page body for this SPECIFIC product:

PRODUCT: "{description}"
Brand name to use: "{brand}"
Tagline: "{tag}"
Key features: {features}
Audience: {audience}
{ctx_block}

STRICT RULES:
- Every heading, paragraph, feature must be SPECIFIC to "{description}"
- Brand name in logo must be TEXT: <span class="logo">{brand}</span> — NOT an <img> tag
- Hero h1 must describe what THIS product does, not generic AI
- Feature cards must describe THIS product's actual capabilities
- Use numbers/stats where possible (e.g. "10x faster", "99.9% uptime")
- Footer brand must be "{brand}"

Available CSS: .container .hero .badge .btn .btn-primary .features .grid .card .cta .step .step-number .text-center .flex

REQUIRED structure:
<header>
  <span class="logo">{brand}</span>
  <nav><a href="#features">Features</a><a href="#how">How It Works</a><a href="#cta">Get Started</a></nav>
</header>
<section class="hero">
  <div class="badge">specific badge text</div>
  <h1>specific headline about {description[:40]}</h1>
  <p>specific subheading</p>
  <a href="#cta" class="btn btn-primary">Get Started Free</a>
</section>
<section id="features" class="features">
  <div class="container">
    <h2 class="text-center">Why Choose {brand}</h2>
    <div class="grid" style="margin-top:2rem">
      [3 specific feature cards]
    </div>
  </div>
</section>
<section id="how">
  <div class="container text-center">
    <h2>How {brand} Works</h2>
    [3 specific steps]
  </div>
</section>
<section id="cta" class="cta">
  <h2>Start Using {brand} Today</h2>
  <p>specific value proposition</p>
  <a href="#" class="btn btn-primary">Get Started Free</a>
</section>
<footer>
  <p>&copy; 2025 {brand}. Built for {audience}.</p>
</footer>

Output ONLY the HTML body content. No markdown. No style tags."""

    try:
        resp = _llm().invoke(prompt)
        body = resp.content.strip()
        body = re.sub(r"```html?|```", "", body).strip()
        body = re.sub(r"(?i)<!DOCTYPE[^>]*>", "", body)
        body = re.sub(r"(?i)<html[^>]*>|</html>", "", body)
        bm = re.search(r"(?is)<body[^>]*>(.*?)</body>", body)
        if bm: body = bm.group(1).strip()
        body = re.sub(r"(?is)<head>.*?</head>", "", body)
        body = re.sub(r"(?is)<style[^>]*>.*?</style>", "", body)
        # Fix broken image logos → text logos
        body = re.sub(
            r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*>',
            r'<span class="logo">\1</span>',
            body
        )
        return body if len(body.strip()) > 100 else _fallback_html(brand, tag, reqs)
    except Exception as e:
        log.warning(f"[Builder] _generate_body failed: {e}")
        return _fallback_html(brand, tag, reqs)