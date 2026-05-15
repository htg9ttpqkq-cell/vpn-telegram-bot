
"use client";

import { motion } from "framer-motion";
import { ShieldCheck, Rocket, Lock, Terminal, Radio, Smartphone } from "lucide-react";

const features = [
  {
    title: "VLESS Reality Tech",
    description: "Next-gen stealth protocol that makes your traffic indistinguishable from normal web browsing.",
    icon: ShieldCheck,
  },
  {
    title: "Ultra Speed Streaming",
    description: "Optimized server nodes for 4K streaming without buffering or ISP throttling.",
    icon: Rocket,
  },
  {
    title: "Military Encryption",
    description: "Your data is protected by industry-standard AES-256-GCM encryption at all times.",
    icon: Lock,
  },
  {
    title: "Telegram Control",
    description: "Manage your connection, subscription, and servers directly through our advanced bot.",
    icon: Terminal,
  },
  {
    title: "Public Wi-Fi Shield",
    description: "Automatic protection whenever you connect to an unsecured public network.",
    icon: Radio,
  },
  {
    title: "Multi-Device Sync",
    description: "Connect all your devices with a single account. Native apps for iOS, Android, and Windows.",
    icon: Smartphone,
  },
];

export default function Features() {
  return (
    <section className="py-24 relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40%] h-[40%] bg-accent/5 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-headline font-bold mb-4"
          >
            Premium Security <span className="text-primary">Standards</span>
          </motion.h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Experience advanced tunneling technology designed for the modern web. Privacy is not a privilege, it's a right.
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
