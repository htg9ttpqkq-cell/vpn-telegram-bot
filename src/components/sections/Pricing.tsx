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
    description: "Идеально для теста нашей сети.",
    features: ["Все локации серверов", "Поддержка VLESS Reality", "3 устройства", "Бот в Telegram"],
    popular: false,
  },
  {
    name: "Премиум",
    duration: "12 месяцев",
    price: "1199 ₽",
    billing: "Всего 99 ₽ / мес",
    description: "Ультимативный щит приватности.",
    features: ["Приоритетная поддержка", "Выделенные узлы", "10 устройств", "Ранний доступ к фишкам"],
    popular: true,
  },
  {
    name: "Продвинутый",
    duration: "3 месяца",
    price: "349 ₽",
    billing: "Всего 116 ₽ / мес",
    description: "Баланс безопасности и цены.",
    features: ["Все локации серверов", "Поддержка VLESS Reality", "5 устройств", "Стандартная поддержка"],
    popular: false,
  },
];

export default function Pricing() {
  return (
    <section className="py-24 relative" id="pricing">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-headline font-bold mb-4">Прозрачные цены</h2>
          <p className="text-muted-foreground">Выберите план, который подходит вашему стилю жизни.</p>
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
                "p-8 rounded-3xl flex flex-col relative transition-all duration-300",
                plan.popular 
                ? "bg-white/[0.05] border-2 border-primary neon-glow z-10 lg:scale-105" 
                : "glass-card z-0"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-primary text-white text-xs font-bold uppercase tracking-widest">
                  Самый выгодный
                </div>
              )}
              
              <div className="mb-8">
                <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                <p className="text-muted-foreground text-sm">{plan.duration}</p>
              </div>

              <div className="mb-8 flex items-baseline gap-1">
                <span className="text-4xl font-headline font-bold">{plan.price}</span>
              </div>
              
              {plan.billing && (
                <p className="text-xs text-primary font-semibold mb-6 uppercase">{plan.billing}</p>
              )}

              <p className="text-muted-foreground text-sm mb-8 leading-relaxed">
                {plan.description}
              </p>

              <div className="space-y-4 mb-10 flex-grow">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center">
                      <Check className="w-3 h-3 text-primary" />
                    </div>
                    <span className="text-sm font-medium">{feature}</span>
                  </div>
                ))}
              </div>

              <Button 
                size="lg" 
                variant={plan.popular ? "default" : "outline"}
                className={cn(
                  "w-full rounded-full h-12 font-bold",
                  plan.popular ? "primary-gradient border-none" : "border-white/10"
                )}
                asChild
              >
                <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                  Подключиться
                </a>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
