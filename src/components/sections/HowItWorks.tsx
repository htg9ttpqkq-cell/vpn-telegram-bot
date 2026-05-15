
"use client";

import { motion } from "framer-motion";
import { CreditCard, Key, CheckCircle } from "lucide-react";

const steps = [
  {
    title: "Choose your Plan",
    description: "Select the subscription that fits your needs perfectly.",
    icon: CreditCard,
  },
  {
    title: "Receive Access",
    description: "Get instant credentials via email and Telegram.",
    icon: Key,
  },
  {
    title: "Connect instantly",
    description: "One-click connection and you're fully protected.",
    icon: CheckCircle,
  },
];

export default function HowItWorks() {
  return (
    <section className="py-24 bg-background/50">
      <div className="container mx-auto px-6">
        <div className="text-center mb-20">
          <h2 className="text-4xl font-headline font-bold mb-4">Start in 60 Seconds</h2>
          <p className="text-muted-foreground">Minimal friction, maximum security.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
          <div className="hidden md:block absolute top-[2.75rem] left-[15%] right-[15%] h-0.5 bg-white/10 z-0" />
          
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.2 }}
              className="relative z-10 flex flex-col items-center text-center"
            >
              <div className="w-20 h-20 rounded-full primary-gradient p-0.5 mb-8 shadow-xl shadow-primary/20">
                <div className="w-full h-full rounded-full bg-background flex items-center justify-center">
                  <step.icon className="w-8 h-8 text-primary" />
                </div>
              </div>
              <div className="absolute top-0 -right-4 text-8xl font-black text-white/[0.03] pointer-events-none select-none">
                0{index + 1}
              </div>
              <h3 className="text-2xl font-headline font-bold mb-4">{step.title}</h3>
              <p className="text-muted-foreground">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
