"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative pt-48 pb-32 overflow-hidden flex items-center justify-center bg-black">
      <div className="absolute top-0 left-0 w-full h-full bg-grid z-0 opacity-20 pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 border border-white/10 mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-white">Digital Resistance</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-6xl md:text-9xl font-bold mb-6 stencil-text tracking-tighter text-white"
          >
            EDELIA | <span className="opacity-50">VPN</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg text-muted-foreground max-w-2xl uppercase tracking-[0.2em] font-medium mb-12"
          >
            Быстро. Приватно. Без компромиссов.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Button 
              size="lg" 
              className="rounded-none bg-black text-white border border-white/40 px-10 h-14 font-black uppercase tracking-[0.2em] text-[12px] hover:bg-white/5 group"
              asChild
            >
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                Подключить бота
                <Send className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </a>
            </Button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
