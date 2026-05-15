"use client";

import { motion } from "framer-motion";
import { Send, Smartphone, LayoutDashboard, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TelegramSection() {
  return (
    <section className="py-32 bg-black border-y border-white/5" id="telegram">
      <div className="container mx-auto px-6">
        <div className="flex flex-col lg:flex-row items-center gap-24">
          <div className="lg:w-1/2">
            <div className="inline-flex items-center gap-2 px-3 py-1 border border-white/10 mb-8">
              <Send className="w-3 h-3 text-white/60" />
              <span className="text-[9px] font-bold text-white/60 uppercase tracking-[0.4em]">Единая экосистема</span>
            </div>
            <h2 className="text-4xl md:text-6xl font-bold mb-8 stencil-text uppercase">
              Управление в <span className="opacity-40 text-white">Telegram</span>
            </h2>
            <p className="text-[12px] text-white/40 mb-12 uppercase tracking-[0.3em] font-bold leading-loose">
              Забудьте о сложных сайтах. Полный контроль над подпиской и серверами через интуитивно понятный интерфейс мессенджера.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-16">
              {[
                { icon: LayoutDashboard, title: "Кабинет", desc: "Конфигурации за секунды" },
                { icon: Send, title: "Выдача", desc: "Мгновенные ключи VLESS" },
                { icon: Share2, title: "Рефералы", desc: "Бонусы за друзей" },
                { icon: Smartphone, title: "Простота", desc: "Один клик для старта" },
              ].map((item, i) => (
                <div key={i} className="flex gap-4">
                  <div className="p-3 h-fit bg-white/5 text-white">
                    <item.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-[10px] mb-1 uppercase tracking-widest">{item.title}</h4>
                    <p className="text-[9px] text-white/30 uppercase tracking-widest">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <Button size="lg" className="bg-white text-black hover:bg-white/90 rounded-none px-12 h-16 font-black uppercase tracking-[0.3em] text-[11px]" asChild>
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                Запустить @edelia_vpn_bot
              </a>
            </Button>
          </div>

          <div className="lg:w-1/2 relative hidden md:block">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="relative z-10 w-full max-w-sm mx-auto border border-white/10 bg-black p-8 shadow-2xl"
            >
              <div className="space-y-6">
                <div className="flex items-center gap-4 pb-6 border-b border-white/5">
                  <div className="w-12 h-12 bg-white text-black flex items-center justify-center font-black stencil-text text-xl">E</div>
                  <div>
                    <p className="font-bold text-xs uppercase tracking-widest">Edelia VPN Bot</p>
                    <p className="text-[9px] text-green-500 uppercase tracking-widest font-bold">online</p>
                  </div>
                </div>

                <div className="p-4 bg-white/5 text-[9px] max-w-[90%] leading-relaxed uppercase tracking-widest font-bold">
                  Добро пожаловать в Edelia VPN. Выберите действие:
                </div>

                <div className="space-y-3 pt-4">
                  <div className="p-4 border border-white/30 text-center text-[10px] font-black uppercase tracking-[0.3em] hover:bg-white/5 transition-colors cursor-pointer">
                    ⚡ ПОДКЛЮЧИТЬСЯ
                  </div>
                  <div className="p-4 border border-white/10 text-center text-[10px] font-black uppercase tracking-[0.3em] bg-white/5">
                    💳 КУПИТЬ ПОДПИСКУ
                  </div>
                  <div className="p-4 border border-white/10 text-center text-[10px] font-black uppercase tracking-[0.3em] bg-white/5">
                    👤 МОЙ ПРОФИЛЬ
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}