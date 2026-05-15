"use client";

import { motion } from "framer-motion";
import { ShieldCheck, Rocket, Lock, Terminal, Radio, Smartphone } from "lucide-react";

const features = [
  {
    title: "VLESS Reality",
    description: "Протокол нового поколения, который делает ваш трафик неотличимым от обычного просмотра веб-страниц.",
    icon: ShieldCheck,
  },
  {
    title: "Ультраскорость",
    description: "Оптимизированные серверы для стриминга в 4K без буферизации и ограничений провайдера.",
    icon: Rocket,
  },
  {
    title: "Шифрование",
    description: "Ваши данные защищены отраслевым стандартом AES-256-GCM в любое время.",
    icon: Lock,
  },
  {
    title: "Telegram Бот",
    description: "Управляйте подпиской и серверами напрямую через нашего продвинутого бота.",
    icon: Terminal,
  },
  {
    title: "Публичный Wi-Fi",
    description: "Автоматическая защита при подключении к незащищенным общественным сетям.",
    icon: Radio,
  },
  {
    title: "Все устройства",
    description: "Подключайте все свои устройства с одного аккаунта. Приложения для всех платформ.",
    icon: Smartphone,
  },
];

export default function Features() {
  return (
    <section className="py-24 relative" id="features">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-6xl font-bold mb-4 stencil-text"
          >
            Технологии
          </motion.h2>
          <p className="text-muted-foreground uppercase tracking-widest text-xs max-w-2xl mx-auto">
            Испытайте передовые стандарты безопасности. Приватность — это право.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 0 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-10 border border-white/5 hover:bg-white/5 transition-all duration-300 group"
            >
              <div className="mb-6 inline-flex p-3 bg-white/5 text-white group-hover:bg-white group-hover:text-black transition-all">
                <feature.icon className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-black uppercase tracking-widest mb-4">{feature.title}</h3>
              <p className="text-[10px] text-muted-foreground leading-relaxed uppercase tracking-widest font-medium">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
