"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowRight, Send } from "lucide-react";
import Image from "next/image";
import { PlaceHolderImages } from "@/lib/placeholder-images";

export default function Hero() {
  const dashboardImg = PlaceHolderImages.find(img => img.id === "hero-dashboard");
  const imgSrc = dashboardImg?.imageUrl || "https://picsum.photos/seed/edelia-hero/1200/800";

  return (
    <section className="relative pt-32 pb-20 overflow-hidden min-h-[90vh] flex items-center">
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
            className="flex flex-col sm:flex-row gap-4 mb-20"
          >
            <Button size="lg" className="h-14 px-10 rounded-none bg-white text-black hover:bg-white/90 font-black uppercase tracking-widest text-xs">
              Начать <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
            <Button size="lg" variant="outline" className="h-14 px-10 rounded-none border-white/20 hover:bg-white/5 bg-transparent font-black uppercase tracking-widest text-xs" asChild>
              <a href="https://t.me/edelia_vpn_bot" target="_blank" rel="noopener noreferrer">
                <Send className="mr-2 w-4 h-4" /> Telegram
              </a>
            </Button>
          </motion.div>

          {/* Hero Image / Dashboard Mockup */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="relative w-full max-w-5xl rounded-none overflow-hidden border border-white/10 grayscale contrast-125"
          >
            <div className="absolute top-0 left-0 w-full h-8 bg-white/5 border-b border-white/10 flex items-center px-4 justify-between">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-white/20" />
                <div className="w-2 h-2 rounded-full bg-white/20" />
                <div className="w-2 h-2 rounded-full bg-white/20" />
              </div>
              <span className="text-[8px] uppercase tracking-widest font-bold opacity-30">Encrypted Tunnel v2.0</span>
            </div>
            <div className="p-2 pt-10">
              <Image
                src={imgSrc}
                width={1200}
                height={800}
                alt={dashboardImg?.description || "Личный кабинет"}
                className="rounded-none opacity-80"
                data-ai-hint={dashboardImg?.imageHint || "industrial interface"}
              />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}