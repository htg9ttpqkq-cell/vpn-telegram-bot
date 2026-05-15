"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden min-h-[70vh] flex items-center">
      <div className="absolute top-0 left-0 w-full h-full bg-grid z-0 opacity-40 pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-none bg-white/5 border border-white/10 mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-white">Digital Resistance</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-6xl md:text-9xl font-bold mb-6 stencil-text tracking-tighter"
          >
            EDELIA | <span className="opacity-50">VPN</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg text-muted-foreground mb-10 max-w-2xl uppercase tracking-widest font-medium"
          >
            Быстро. Приватно. Без компромиссов.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 mb-10"
          >
            <Button size="lg" variant="outline" className="h-14 px-10 rounded-none border-white/20 hover:bg-white/5 bg-transparent font-black uppercase tracking-widest text-xs" asChild>
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                <Send className="mr-2 w-4 h-4" /> Перейти в Telegram
              </a>
            </Button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
