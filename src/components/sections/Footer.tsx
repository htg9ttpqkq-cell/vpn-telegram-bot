"use client";

import Link from "next/link";
import { Send, Twitter, Github, Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-20 border-t border-white/5 relative bg-background">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-6 group">
              <div className="p-1.5 rounded-lg bg-primary/10 group-hover:bg-primary transition-colors">
                <Shield className="w-6 h-6 text-primary group-hover:text-white" />
              </div>
              <span className="text-2xl font-headline font-bold tracking-tight">Edelia <span className="text-primary">VPN</span></span>
            </Link>
            <p className="text-muted-foreground max-w-sm leading-relaxed">
              Премиальный VPN-сервис для современного интернета. Безопасный, без границ и молниеносно быстрый. Почувствуйте истинную цифровую свободу.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-6 uppercase text-xs tracking-widest text-primary">Ресурсы</h4>
            <ul className="space-y-4">
              <li><Link href="/privacy" className="text-muted-foreground hover:text-white transition-colors text-sm">Приватность</Link></li>
              <li><Link href="/terms" className="text-muted-foreground hover:text-white transition-colors text-sm">Условия</Link></li>
              <li><Link href="/docs" className="text-muted-foreground hover:text-white transition-colors text-sm">Документация</Link></li>
              <li><Link href="/faq" className="text-muted-foreground hover:text-white transition-colors text-sm">FAQ</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6 uppercase text-xs tracking-widest text-primary">Сообщество</h4>
            <div className="flex gap-4">
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary/20 transition-all">
                <Send className="w-5 h-5" />
              </a>
              <Link href="#" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary/20 transition-all">
                <Twitter className="w-5 h-5" />
              </Link>
              <Link href="#" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary/20 transition-all">
                <Github className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
          <p>© 2024 Edelia VPN. Все права защищены.</p>
          <div className="flex gap-6">
            <Link href="#" className="hover:text-white transition-colors">Статус</Link>
            <Link href="#" className="hover:text-white transition-colors">Карта сети</Link>
            <Link href="#" className="hover:text-white transition-colors">Поддержка</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
