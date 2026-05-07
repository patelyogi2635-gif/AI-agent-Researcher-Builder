import Navbar       from "@/components/Navbar";
import Hero         from "@/components/Hero";
import Services     from "@/components/Services";
import HowItWorks   from "@/components/HowItWorks";
import AgentPanel   from "@/components/AgentPanel";
import Footer       from "@/components/Footer";

export default function Home() {
  return (
    <main className="overflow-x-hidden">
      <Navbar />
      <Hero />
      <Services />
      <HowItWorks />
      <AgentPanel />
      <Footer />
    </main>
  );
}
