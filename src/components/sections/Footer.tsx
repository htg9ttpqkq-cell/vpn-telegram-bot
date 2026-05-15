"use client";

import Link from "next/link";
import { Send, Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-24 border-t border-white/5 relative bg-black">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-16 mb-24">
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-8 group">
              <Shield className="w-6 h-6 text-white" />
              <span className="text-2xl font-bold tracking-widest stencil-text text-white uppercase">
                EDELIA | <span className="opacity-40">VPN</span>
              </span>
            </Link>
            <p className="text-white/40 max-w-sm leading-relaxed uppercase text-[10px] tracking-[0.3em] font-medium">
              Премиальный VPN-сервис для современного интернета. Безопасный, без границ и молниеносно быстрый.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-8 uppercase text-[10px] tracking-[0.3em] text-white/30">Навигация</h4>
            <ul className="space-y-5">
              <li><Link href="#hero" className="text-white/50 hover:text-white transition-colors text-[10px] uppercase tracking-[0.2em]">Главная</Link></li>
              <li><Link href="#features" className="text-white/50 hover:text-white transition-colors text-[10px] uppercase tracking-[0.2em]">Технологии</Link></li>
              <li><Link href="#pricing" className="text-white/50 hover:text-white transition-colors text-[10px] uppercase tracking-[0.2em]">Тарифы</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-8 uppercase text-[10px] tracking-[0.3em] text-white/30">Связь</h4>
            <div className="flex gap-6">
              <a 
                href="https://t.me/edelia_vpn" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="w-12 h-12 border border-white/10 flex items-center justify-center hover:bg-white hover:text-black transition-all"
                title="Community"
              >
                <Send className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="pt-12 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-8 text-[9px] uppercase tracking-[0.3em] text-white/30 font-bold">
          <p>© 2026 EDELIA | VPN. ALL RIGHTS RESERVED.</p>
          <div className="flex gap-8">
            <Link href="#" className="hover:text-white transition-colors">STATUS</Link>
            <Link href="#" className="hover:text-white transition-colors">NETWORK</Link>
            <a 
              href="https://t.me/AveLxu" 
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
