"use client";
import { useState, useEffect } from "react";
import { Cpu, Menu, X } from "lucide-react";
import clsx from "clsx";

const NAV_LINKS = [
  { label: "Services",     href: "#services"     },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Try Agent",    href: "#agent"        },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={clsx(
        "fixed top-0 inset-x-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/95 backdrop-blur-sm shadow-sm border-b border-slate-100"
          : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shadow-md shadow-brand-600/30 group-hover:scale-105 transition-transform duration-200">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-slate-900 text-lg">
            Synapse <span className="text-brand-600">AI</span>
          </span>
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((n) => (
            <a
              key={n.label}
              href={n.href}
              className="text-sm font-medium text-slate-600 hover:text-brand-600 transition-colors duration-150"
            >
              {n.label}
            </a>
          ))}
        </div>

        {/* CTA */}
        <a href="#agent" className="hidden md:inline-flex btn-primary text-sm py-2.5 px-5">
          Try Free →
        </a>

        {/* Mobile toggle */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-b border-slate-100 shadow-lg px-6 py-4 space-y-1">
          {NAV_LINKS.map((n) => (
            <a
              key={n.label}
              href={n.href}
              onClick={() => setMenuOpen(false)}
              className="block py-2.5 text-sm font-medium text-slate-700 hover:text-brand-600 transition-colors"
            >
              {n.label}
            </a>
          ))}
          <div className="pt-2">
            <a href="#agent" className="btn-primary text-sm py-2.5 w-full justify-center">
              Try Free →
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}
