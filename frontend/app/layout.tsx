import type { Metadata } from "next";
import { Inter, Sora } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets:  ["latin"],
  variable: "--font-inter",
  display:  "swap",
});

const sora = Sora({
  subsets:  ["latin"],
  variable: "--font-sora",
  weight:   ["600", "700", "800"],
  display:  "swap",
});

export const metadata: Metadata = {
  title:       "Synapse AI — Research & Build Intelligence Platform",
  description: "LangGraph-powered AI agents: deep research with live web data and automated website generation.",
  keywords:    "AI research, website builder, LangGraph, AI agent, Groq, Tavily, ChromaDB",
  openGraph: {
    title:       "Synapse AI — Research & Build Intelligence Platform",
    description: "Research anything. Build anything. AI-powered.",
    type:        "website",
  },
  twitter: {
    card:        "summary_large_image",
    title:       "Synapse AI",
    description: "LangGraph-powered research and web builder agents.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${sora.variable} scroll-smooth`}
    >
      <body className="min-h-screen bg-white antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
