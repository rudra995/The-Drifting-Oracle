import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, AlertTriangle, Cpu, Gavel, CloudOff } from 'lucide-react';
import { fetchApi } from '../api';

export default function KpiCards() {
 const [data, setData] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/dashboard-metrics')
 .then(setData)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 if (loading) {
 return (
 <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
 {[1, 2, 3, 4].map((i) => (
 <div
 key={i}
 className="glass-panel p-6 rounded-2xl relative overflow-hidden flex flex-col justify-between h-[140px]"
 >
 <div className="absolute inset-0 bg-primary/5 blur-2xl rounded-full" />
 <div className="relative z-10 w-full animate-pulse transition-all">
 <div className="flex justify-between items-start mb-4">
 <div className="h-2 bg-surface-container-high rounded w-1/2"></div>
 <div className="w-8 h-8 rounded-xl bg-surface-container-high"></div>
 </div>
 <div className="h-6 bg-surface-container-high rounded w-1/3 mb-5"></div>
 <div className="h-1.5 w-full bg-surface-container-high rounded-full"></div>
 </div>
 </div>
 ))}
 </section>
 );
 }

 if (error || !data) {
 return (
 <section className="bg-error-container/20 border border-error/30 rounded-2xl p-8 text-center flex flex-col items-center">
 <CloudOff size={32} className="text-error mb-3" />
 <p className="text-error font-headline font-bold text-lg">
 {error || 'Missing endpoint: /api/v1/dashboard-metrics'}
 </p>
 <p className="text-on-surface-variant text-sm mt-1">
 This endpoint is required to display KPI metrics.
 </p>
 </section>
 );
 }

 const cards = [
 {
 label: 'Models Trained',
 value: data.total_models,
 Icon: BrainCircuit,
 iconColor: 'text-primary',
 iconBg: 'bg-primary/20 border-primary/30',
 barColor: 'bg-primary',
 },
 {
 label: 'Drift Detections',
 value: data.drift_detections,
 Icon: AlertTriangle,
 iconColor: 'text-error',
 iconBg: 'bg-error/20 border-error/30',
 barColor: 'bg-error',
 },
 {
 label: 'LLM Evaluations',
 value: data.total_llm_evaluations,
 Icon: Cpu,
 iconColor: 'text-accent',
 iconBg: 'bg-accent/20 border-accent/30',
 barColor: 'bg-accent',
 },
 {
 label: 'Governance Events',
 value: data.governance_events,
 Icon: Gavel,
 iconColor: 'text-on-surface-variant',
 iconBg: 'bg-surface-bright border-outline-variant/30',
 barColor: 'bg-on-surface-variant',
 },
 ];

 return (
 <motion.section 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ duration: 0.5, staggerChildren: 0.1 }}
 className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
 >
 {cards.map((card) => (
 <motion.div
 whileHover={{ y: -4 }}
 key={card.label}
 className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
 >
 {/* Subtle background glow on hover */}
 <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />

 <div className="flex justify-between items-start mb-4 relative z-10">
 <span className="font-label text-[11px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
 {card.label}
 </span>
 <div
 className={`${card.iconColor} p-2.5 ${card.iconBg} rounded-xl border`}
 >
 <card.Icon size={20} />
 </div>
 </div>
 <div className="flex items-baseline gap-2 relative z-10">
 <span className="text-4xl font-headline font-bold text-on-surface">
 {card.value ?? '—'}
 </span>
 </div>
 <div className="mt-5 h-1.5 w-full bg-surface-container-highest/50 rounded-full overflow-hidden relative z-10">
 <div
 className={`h-full ${card.barColor} rounded-full transition-all duration-1000`}
 style={{ width: card.value ? '50%' : '0%' }}
 ></div>
 </div>
 </motion.div>
 ))}
 </motion.section>
 );
}
