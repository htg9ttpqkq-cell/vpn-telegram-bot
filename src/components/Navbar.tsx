"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Shield, Menu } from "lucide-react";
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
      scrolled ? "bg-black/90 backdrop-blur-lg border-b border-white/5 py-3" : "bg-transparent py-6"
    }`}>
      <div className="container mx-auto px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Shield className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
          <span className="text-xl font-bold tracking-widest stencil-text">EDELIA | <span className="text-muted-foreground">VPN</span></span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="#features" className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white transition-colors">Преимущества</Link>
          <Link href="#how-it-works" className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white transition-colors">Как это работает</Link>
          <Link href="#pricing" className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white transition-colors">Цены</Link>
          <Link href="#telegram" className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white transition-colors">Telegram</Link>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" className="hidden sm:inline-flex text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white">Войти</Button>
          <Button className="rounded-none bg-white text-black px-6 font-bold uppercase tracking-tighter hover:bg-white/90" asChild>
            <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">Подключить</a>
          </Button>
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="w-6 h-6" />
          </Button>
        </div>
      </div>
    </nav>
  );
}
