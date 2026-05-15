"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative pt-64 pb-32 overflow-hidden flex items-center justify-center bg-black" id="hero">
      <div className="absolute top-0 left-0 w-full h-full bg-grid z-0 opacity-20 pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 border border-white/10 mb-12"
          >
            <span className="w-1 h-1 rounded-full bg-white animate-pulse" />
            <span className="text-[9px] font-bold uppercase tracking-[0.5em] text-white/60">Digital Resistance</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-6xl md:text-9xl font-bold mb-8 stencil-text tracking-tight text-white uppercase"
          >
            EDELIA | <span className="opacity-30">VPN</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base md:text-lg text-white/40 max-w-2xl uppercase tracking-[0.4em] font-medium mb-16"
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
              className="rounded-none bg-black text-white border border-white/40 px-12 h-16 font-black uppercase tracking-[0.3em] text-[11px] hover:bg-white/5 transition-all group"
              asChild
            >
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                Подключить бота
                <Send className="ml-3 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </a>
            </Button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}