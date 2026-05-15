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
    name: "Премиум",
    duration: "12 месяцев",
    price: "1199 ₽",
    billing: "Выгода 30%",
    description: "Максимальный приоритет и скорость.",
    features: ["VIP поддержка", "Выделенные узлы", "10 устройств", "Все фишки"],
    popular: true,
  },
  {
    name: "Продвинутый",
    duration: "3 месяца",
    price: "349 ₽",
    billing: "Лучший выбор",
    description: "Сбалансированный тариф.",
    features: ["Все локации", "VLESS Reality", "5 устройств", "Поддержка"],
    popular: false,
  },
];

export default function Pricing() {
  return (
    <section className="py-24 relative" id="pricing">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-6xl font-bold mb-4 stencil-text">Тарифы</h2>
          <p className="text-muted-foreground uppercase tracking-widest text-xs">Прозрачная стоимость без скрытых платежей</p>
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
                "p-8 rounded-none flex flex-col relative transition-all duration-300 border",
                plan.popular 
                ? "bg-white/[0.05] border-white z-10 lg:scale-105" 
                : "bg-transparent border-white/10 z-0"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-white text-black text-[10px] font-black uppercase tracking-widest">
                  Популярный
                </div>
              )}
              
              <div className="mb-8">
                <h3 className="text-xl font-bold uppercase tracking-tighter stencil-text mb-1">{plan.name}</h3>
                <p className="text-muted-foreground text-xs uppercase tracking-widest">{plan.duration}</p>
              </div>

              <div className="mb-8 flex items-baseline gap-1">
                <span className="text-5xl font-bold stencil-text">{plan.price}</span>
              </div>
              
              {plan.billing && (
                <p className="text-[10px] text-white font-black mb-6 uppercase tracking-widest opacity-60">{plan.billing}</p>
              )}

              <p className="text-muted-foreground text-xs mb-8 leading-relaxed uppercase tracking-wider">
                {plan.description}
              </p>

              <div className="space-y-4 mb-10 flex-grow">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-3">
                    <Check className="w-3 h-3 text-white" />
                    <span className="text-[10px] font-bold uppercase tracking-widest opacity-80">{feature}</span>
                  </div>
                ))}
              </div>

              <Button 
                size="lg" 
                variant={plan.popular ? "default" : "outline"}
                className={cn(
                  "w-full rounded-none h-12 font-black uppercase tracking-widest text-[10px]",
                  plan.popular ? "bg-white text-black hover:bg-white/90 border-none" : "border-white/10 hover:bg-white/5"
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