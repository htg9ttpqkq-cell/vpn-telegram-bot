
"use client";

import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Shield, Zap, Activity, Navigation, MapPin } from "lucide-react";

const data = [
  { time: "00:00", speed: 45 },
  { time: "04:00", speed: 52 },
  { time: "08:00", speed: 38 },
  { time: "12:00", speed: 65 },
  { time: "16:00", speed: 48 },
  { time: "20:00", speed: 58 },
  { time: "23:59", speed: 55 },
];

export default function DashboardPreview() {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-6">
        <div className="flex flex-col lg:flex-row gap-12 items-center">
          <div className="lg:w-1/2">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <Badge className="bg-primary/20 text-primary border-primary/30 mb-6">LIVE STATUS</Badge>
              <h2 className="text-4xl md:text-5xl font-headline font-bold mb-6">
                Total Control at <span className="text-gradient">Your Fingertips</span>
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                Our dashboard provides real-time insights into your connection. Monitor speed, manage servers, and verify your encrypted tunnel health with ease.
              </p>
              
              <div className="space-y-4">
                {[
                  { icon: Activity, text: "Real-time bandwidth monitoring" },
                  { icon: Navigation, text: "Instant server switching across 50+ countries" },
                  { icon: Shield, text: "Automatic kill-switch status check" },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      <item.icon className="w-5 h-5" />
                    </div>
                    <span className="font-medium">{item.text}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          <div className="lg:w-1/2 w-full">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="glass-card rounded-3xl p-8 relative overflow-hidden"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <Shield className="text-green-400 w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold">Protected</h4>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Active Session: 04h 22m</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">Netherlands, NL-1</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Download</p>
                  <p className="text-2xl font-headline font-bold">142.5 <span className="text-sm font-normal text-muted-foreground">Mbps</span></p>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Upload</p>
                  <p className="text-2xl font-headline font-bold">89.2 <span className="text-sm font-normal text-muted-foreground">Mbps</span></p>
                </div>
              </div>

              <div className="h-48 w-full">
                <p className="text-xs text-muted-foreground uppercase font-semibold mb-4">Traffic Usage</p>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data}>
                    <defs>
                      <linearGradient id="colorSpeed" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#000', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Area type="monotone" dataKey="speed" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorSpeed)" strokeWidth={3} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
