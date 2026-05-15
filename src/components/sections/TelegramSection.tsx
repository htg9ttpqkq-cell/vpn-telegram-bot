"use client";

import { motion } from "framer-motion";
import { Send, Smartphone, LayoutDashboard, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TelegramSection() {
  return (
    <section className="py-24 bg-primary/5" id="telegram">
      <div className="container mx-auto px-6">
        <div className="glass-card rounded-[3rem] p-12 overflow-hidden relative">
          <div className="absolute top-0 right-0 w-[40%] h-full bg-primary/10 blur-[100px] -z-10" />
          
          <div className="flex flex-col lg:flex-row items-center gap-16">
            <div className="lg:w-1/2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 mb-6">
                <Send className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-bold text-sky-400 uppercase tracking-widest">Единая экосистема</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-headline font-bold mb-6">
                Управляйте через <span className="text-[#24A1DE]">Telegram</span>
              </h2>
              <p className="text-lg text-muted-foreground mb-10">
                Самый удобный способ управления VPN. Никаких сложных внешних сайтов — контролируйте всё через наш бот.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-10">
                {[
                  { icon: LayoutDashboard, title: "Личный кабинет", desc: "Управление подпиской и ключами" },
                  { icon: Send, title: "Мгновенная выдача", desc: "Конфиги приходят за секунды" },
                  { icon: Share2, title: "Реферальная система", desc: "Бонусы за приглашение друзей" },
                  { icon: Smartphone, title: "Простое управление", desc: "Команды для любых задач" },
                ].map((item, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="p-2 h-fit rounded-lg bg-white/5 text-primary">
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-sm mb-1">{item.title}</h4>
                      <p className="text-xs text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <Button size="lg" className="bg-[#24A1DE] hover:bg-[#208fbd] text-white rounded-full px-8 h-14" asChild>
                <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                  Запустить @edelia_vpn_bot
                </a>
              </Button>
            </div>

            <div className="lg:w-1/2 relative">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                className="relative z-10 w-full max-w-sm mx-auto rounded-[3rem] border-[8px] border-white/5 bg-background shadow-2xl p-6"
              >
                {/* Simulated Telegram Chat */}
                <div className="space-y-4">
                  <div className="flex items-center gap-3 pb-4 border-b border-white/5">
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center font-bold">E</div>
                    <div>
                      <p className="font-bold text-sm">Edelia VPN Bot</p>
                      <p className="text-xs text-green-400">бот активен</p>
                    </div>
                  </div>

                  <div className="p-3 rounded-2xl rounded-tl-none bg-white/5 text-xs max-w-[85%] leading-relaxed">
                    Добро пожаловать в Edelia VPN! Пожалуйста, выберите действие ниже.
                  </div>

                  <div className="space-y-2 pt-4">
                    <div className="p-3 rounded-xl border border-primary/30 text-center text-xs font-bold text-primary bg-primary/10">
                      ⚡ ПОДКЛЮЧИТЬСЯ
                    </div>
                    <div className="p-3 rounded-xl border border-white/10 text-center text-xs font-bold bg-white/5">
                      💳 КУПИТЬ ПОДПИСКУ
                    </div>
                    <div className="p-3 rounded-xl border border-white/10 text-center text-xs font-bold bg-white/5">
                      👤 МОЙ ПРОФИЛЬ
                    </div>
                  </div>
                </div>
              </motion.div>
              
              {/* Decorative elements */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-accent/20 rounded-full blur-3xl" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
