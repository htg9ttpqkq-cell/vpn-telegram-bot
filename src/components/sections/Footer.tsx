"use client";

import Link from "next/link";
import { Send, Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-20 border-t border-white/5 relative bg-black">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-6 group">
              <Shield className="w-6 h-6 text-white" />
              <span className="text-2xl font-bold tracking-widest stencil-text text-white">
                EDELIA | <span className="opacity-50">VPN</span>
              </span>
            </Link>
            <p className="text-muted-foreground max-w-sm leading-relaxed uppercase text-[10px] tracking-widest font-medium">
              Премиальный VPN-сервис для современного интернета. Безопасный, без границ и молниеносно быстрый.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-6 uppercase text-[10px] tracking-widest text-white/50">Ресурсы</h4>
            <ul className="space-y-4">
              <li><Link href="#hero" className="text-muted-foreground hover:text-white transition-colors text-[10px] uppercase tracking-widest">Главная</Link></li>
              <li><Link href="#features" className="text-muted-foreground hover:text-white transition-colors text-[10px] uppercase tracking-widest">Технологии</Link></li>
              <li><Link href="#pricing" className="text-muted-foreground hover:text-white transition-colors text-[10px] uppercase tracking-widest">Тарифы</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6 uppercase text-[10px] tracking-widest text-white/50">Сообщество</h4>
            <div className="flex gap-4">
              <a 
                href="https://t.me/edelia_vpn" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="w-10 h-10 border border-white/10 flex items-center justify-center hover:bg-white hover:text-black transition-all"
              >
                <Send className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-[8px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
          <p>© 2024 EDELIA | VPN. ALL RIGHTS RESERVED.</p>
          <div className="flex gap-6">
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
