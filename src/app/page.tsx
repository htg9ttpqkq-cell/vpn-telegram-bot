
import Navbar from "@/components/Navbar";
import Hero from "@/components/sections/Hero";
import Stats from "@/components/sections/Stats";
import Features from "@/components/sections/Features";
import HowItWorks from "@/components/sections/HowItWorks";
import DashboardPreview from "@/components/sections/DashboardPreview";
import Pricing from "@/components/sections/Pricing";
import TelegramSection from "@/components/sections/TelegramSection";
import Footer from "@/components/sections/Footer";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <div id="hero">
          <Hero />
        </div>
        <div id="stats">
          <Stats />
        </div>
        <div id="features">
          <Features />
        </div>
        <div id="how-it-works">
          <HowItWorks />
        </div>
        <div id="dashboard">
          <DashboardPreview />
        </div>
        <div id="pricing">
          <Pricing />
        </div>
        <div id="telegram">
          <TelegramSection />
        </div>
      </main>
      <Footer />
    </div>
  );
}
