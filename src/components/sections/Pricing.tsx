
"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";

const plans = [
  {
    name: "Standard",
    duration: "1 Month",
    price: "$7.99",
    description: "Perfect for testing our network.",
    features: ["All Server Locations", "VLESS Reality Support", "3 Devices", "Telegram Bot Control"],
    popular: false,
  },
  {
    name: "Premium",
    duration: "12 Months",
    price: "$3.99",
    billing: "Billed $47.88 / yr",
    description: "The ultimate privacy shield.",
    features: ["Priority Support", "Dedicated Nodes", "10 Devices", "Exclusive Early Access"],
    popular: true,
  },
  {
    name: "Advanced",
    duration: "3 Months",
    price: "$5.99",
    billing: "Billed $17.97 / qtr",
    description: "Balanced security for digital nomads.",
    features: ["All Server Locations", "VLESS Reality Support", "5 Devices", "Standard Support"],
    popular: false,
  },
];

export default function Pricing() {
  return (
    <section className="py-24 relative" id="pricing">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-headline font-bold mb-4">Transparent Pricing</h2>
          <p className="text-muted-foreground">Select the plan that matches your lifestyle.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.duration}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`p-8 rounded-3xl flex flex-col relative ${
                plan.popular 
                ? "bg-white/[0.05] border-2 border-primary neon-glow z-10 scale-105" 
                : "glass-card z-0"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-primary text-white text-xs font-bold uppercase tracking-widest">
                  Most Popular
                </div>
              )}
              
              <div className="mb-8">
                <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                <p className="text-muted-foreground text-sm">{plan.duration}</p>
              </div>

              <div className="mb-8 flex items-baseline gap-1">
                <span className="text-4xl font-headline font-bold">{plan.price}</span>
                <span className="text-muted-foreground">/mo</span>
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
                className={`w-full rounded-full h-12 font-bold ${
                  plan.popular ? "primary-gradient border-none" : "variant-outline border-white/10"
                }`}
              >
                Connect Now
              </Button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
