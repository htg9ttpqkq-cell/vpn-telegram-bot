"use client";

import { motion } from "framer-motion";
import { ShieldCheck, Rocket, Lock, Terminal, Radio, Smartphone } from "lucide-react";

const features = [
  {
    title: "Технология VLESS Reality",
    description: "Протокол нового поколения, который делает ваш трафик неотличимым от обычного просмотра веб-страниц.",
    icon: ShieldCheck,
  },
  {
    title: "Ультраскорость",
    description: "Оптимизированные серверы для стриминга в 4K без буферизации и ограничений провайдера.",
    icon: Rocket,
  },
  {
    title: "Военное шифрование",
    description: "Ваши данные защищены отраслевым стандартом AES-256-GCM в любое время.",
    icon: Lock,
  },
  {
    title: "Управление в Telegram",
    description: "Управляйте подпиской и серверами напрямую через нашего продвинутого бота.",
    icon: Terminal,
  },
  {
    title: "Защита в Public Wi-Fi",
    description: "Автоматическая защита при подключении к незащищенным общественным сетям.",
    icon: Radio,
  },
  {
    title: "Синхронизация устройств",
    description: "Подключайте все свои устройства с одного аккаунта. Приложения для iOS, Android и Windows.",
    icon: Smartphone,
  },
];

export default function Features() {
  return (
    <section className="py-24 relative" id="features">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40%] h-[40%] bg-accent/5 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-headline font-bold mb-4"
          >
            Премиальные стандарты <span className="text-primary">безопасности</span>
          </motion.h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Испытайте передовые технологии туннелирования. Приватность — это не привилегия, а право.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-8 rounded-2xl glass-card hover:border-primary/50 transition-all duration-300 group"
            >
              <div className="mb-6 inline-flex p-3 rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-all">
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-headline font-bold mb-4">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
