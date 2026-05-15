"use client";

import { motion } from "framer-motion";
import { Shield, Zap, Globe, Cpu } from "lucide-react";

const stats = [
  { label: "Аптайм", value: "99.9%", icon: Shield, color: "text-primary" },
  { label: "Задержка", value: "<50мс", icon: Zap, color: "text-accent" },
  { label: "Серверов", value: "500+", icon: Globe, color: "text-blue-400" },
  { label: "Пользователей", value: "1M+", icon: Cpu, color: "text-cyan-400" },
];

export default function Stats() {
  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-8 rounded-2xl glass-card relative group"
            >
              <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none" />
              <div className="flex flex-col items-center text-center">
                <div className={`p-4 rounded-xl bg-white/5 mb-6 group-hover:scale-110 transition-transform ${stat.color}`}>
                  <stat.icon className="w-8 h-8" />
                </div>
                <h3 className="text-4xl font-headline font-bold mb-2 text-white">
                  {stat.value}
                </h3>
                <p className="text-muted-foreground font-medium uppercase tracking-wider text-sm">
                  {stat.label}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
