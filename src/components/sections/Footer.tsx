"use client";

import Link from "next/link";
import { Send, Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-32 border-t border-white/10 relative bg-black" id="footer">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-20 mb-32">
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-8 group">
              <Shield className="w-5 h-5 text-white" />
              <span className="text-2xl font-bold tracking-widest stencil-text text-white uppercase">
                EDELIA | <span className="opacity-30">VPN</span>
              </span>
            </Link>
            <p className="text-white/30 max-w-sm leading-relaxed uppercase text-[9px] tracking-[0.4em] font-bold">
              Премиальный VPN-сервис для современного интернета. Безопасный, без границ и молниеносно быстрый.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-10 uppercase text-[10px] tracking-[0.4em] text-white/20">Навигация</h4>
            <ul className="space-y-6">
              <li><Link href="#hero" className="text-white/40 hover:text-white transition-colors text-[9px] uppercase tracking-[0.3em] font-bold">Главная</Link></li>
              <li><Link href="#features" className="text-white/40 hover:text-white transition-colors text-[9px] uppercase tracking-[0.3em] font-bold">Технологии</Link></li>
              <li><Link href="#pricing" className="text-white/40 hover:text-white transition-colors text-[9px] uppercase tracking-[0.3em] font-bold">Тарифы</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-10 uppercase text-[10px] tracking-[0.4em] text-white/20">Связь</h4>
            <div className="flex gap-4">
              <a 
                href="https://t.me/edelia_vpn" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="w-14 h-14 border border-white/10 flex items-center justify-center hover:bg-white hover:text-black transition-all group"
                title="Community"
              >
                <Send className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </a>
            </div>
          </div>
        </div>

        <div className="pt-16 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-12 text-[8px] uppercase tracking-[0.5em] text-white/20 font-black">
          <p>© 2026 EDELIA | VPN. ALL RIGHTS RESERVED.</p>
          <div className="flex gap-10">
            <Link href="#features" className="hover:text-white transition-colors">STATUS</Link>
            <Link href="#hero" className="hover:text-white transition-colors">NETWORK</Link>
            <a 
              href="https://t.me/edelia_support" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="hover:text-white transition-colors"
            >
              SUPPORT
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}