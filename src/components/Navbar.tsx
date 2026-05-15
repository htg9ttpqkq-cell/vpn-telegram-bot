"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Shield } from "lucide-react";
import { useState, useEffect } from "react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? "bg-black/95 border-b border-white/10 py-3" : "bg-transparent py-6"
    }`}>
      <div className="container mx-auto px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Shield className="w-6 h-6 text-white group-hover:rotate-12 transition-transform" />
          <span className="text-xl font-bold tracking-widest stencil-text text-white uppercase">
            EDELIA | <span className="text-white/50">VPN</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="#features" className="text-[10px] font-bold uppercase tracking-widest text-white/50 hover:text-white transition-colors">Технологии</Link>
          <Link href="#pricing" className="text-[10px] font-bold uppercase tracking-widest text-white/50 hover:text-white transition-colors">Тарифы</Link>
          <Link href="#telegram" className="text-[10px] font-bold uppercase tracking-widest text-white/50 hover:text-white transition-colors">Бот</Link>
        </div>

        <div className="flex items-center gap-4">
          <Button className="rounded-none bg-white text-black px-6 font-bold uppercase tracking-widest text-[10px] hover:bg-white/90" asChild>
            <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">Подключить</a>
          </Button>
        </div>
      </div>
    </nav>
  );
}