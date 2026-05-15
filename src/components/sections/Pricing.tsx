"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const plans = [
  {
    name: "Стандарт",
    duration: "1 месяц",
    price: "149 ₽",
    description: "Базовая защита на каждый день.",
    features: ["Все локации", "VLESS Reality", "3 устройства", "Telegram бот"],
    popular: false,
  },
  {
    name: "Продвинутый",
    duration: "3 месяца",
    price: "349 ₽",
    billing: "Лучший выбор",
    description: "Сбалансированный тариф.",
    features: ["Все локации", "VLESS Reality", "5 устройств", "Поддержка"],
    popular: true,
  },
  {
    name: "Премиум",
    duration: "12 месяцев",
    price: "1199 ₽",
    billing: "Выгода 30%",
    description: "Максимальный приоритет и скорость.",
    features: ["VIP поддержка", "Выделенные узлы", "10 устройств", "Все фишки"],
    popular: false,
  },
];

export default function Pricing() {
  return (
    <section className="py-32 bg-black relative" id="pricing">
      <div className="container mx-auto px-6">
        <div className="text-center mb-24">
          <h2 className="text-4xl md:text-6xl font-bold mb-6 stencil-text text-white uppercase">Тарифы</h2>
          <p className="text-white/40 uppercase tracking-[0.4em] text-[10px] font-bold">Прозрачная стоимость без скрытых платежей</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.duration}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={cn(
                "p-10 rounded-none flex flex-col relative transition-all duration-300 border",
                plan.popular 
                ? "bg-white/[0.03] border-white z-10" 
                : "bg-transparent border-white/10 z-0"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-6 py-1 bg-white text-black text-[9px] font-black uppercase tracking-[0.2em]">
                  Выгодно
                </div>
              )}
              
              <div className="mb-10">
                <h3 className="text-2xl font-bold uppercase tracking-widest stencil-text mb-2 text-white">{plan.name}</h3>
                <p className="text-white/40 text-[10px] uppercase tracking-[0.2em] font-bold">{plan.duration}</p>
              </div>

              <div className="mb-10 flex items-baseline gap-1">
                <span className="text-6xl font-bold stencil-text text-white">{plan.price}</span>
              </div>
              
              {plan.billing && (
                <p className="text-[10px] text-white font-black mb-8 uppercase tracking-[0.2em] opacity-80">{plan.billing}</p>
              )}

              <p className="text-white/40 text-[10px] mb-10 leading-relaxed uppercase tracking-widest font-bold">
                {plan.description}
              </p>

              <div className="space-y-5 mb-12 flex-grow">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-4">
                    <Check className="w-4 h-4 text-white/50" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/80">{feature}</span>
                  </div>
                ))}
              </div>

              <Button 
                size="lg" 
                variant={plan.popular ? "default" : "outline"}
                className={cn(
                  "w-full rounded-none h-14 font-black uppercase tracking-[0.3em] text-[10px]",
                  plan.popular ? "bg-white text-black hover:bg-white/90 border-none" : "border-white/20 hover:bg-white/5 text-white"
                )}
                asChild
              >
                <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                  Подключить
                </a>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}