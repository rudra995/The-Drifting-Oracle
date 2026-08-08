import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CloudOff, Network, ScatterChart } from 'lucide-react';
import { fetchApi } from '../api';

export default function ScatterPlot() {
 const [data, setData] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/llm-evaluations')
 .then(setData)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 if (loading) {
 return (
 <div className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden">
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <ScatterChart className="text-primary w-5 h-5" />
 Hallucination vs Grounding
 </h3>
 </div>
 <div className="h-[300px] flex items-center justify-center relative">
 <div className="absolute inset-0 bg-primary/5 blur-3xl rounded-full" />
 <p className="text-on-surface-variant font-label text-sm animate-pulse relative z-10 glass-panel px-6 py-3 rounded-full border border-primary/20 bg-primary/5">
 Plotting evaluation vectors...
 </p>
 </div>
 </div>
 );
 }

 if (error || !data) {
 return (
 <div className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden">
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <ScatterChart className="text-primary w-5 h-5" />
 Hallucination vs Grounding
 </h3>
 </div>
 <div className="h-[300px] flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">
 {error || 'Missing endpoint: /api/v1/llm-evaluations'}
 </p>
 <p className="text-on-surface-variant text-sm">
 Required to display hallucination scatter plot.
 </p>
 </div>
 </div>
 );
 }

 // Derive scatter dots from evaluation data
 const evaluations = Array.isArray(data) ? data : [];
 const dots = evaluations.map((ev) => ({
 x: `${Math.round((ev.factual_grounding_score || 0) * 100)}%`,
 y: `${Math.round((1 - (ev.hallucination_score || 0)) * 100)}%`,
 pass: ev.status === 'acceptable',
 }));

 if (dots.length === 0) {
 return (
 <div className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden">
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <ScatterChart className="text-primary w-5 h-5" />
 Hallucination vs Grounding
 </h3>
 </div>
 <div className="h-[300px] flex flex-col items-center justify-center gap-3 relative">
 <div className="absolute inset-0 bg-surface-container-highest/10 blur-[80px] rounded-full" />
 <div className="relative z-10 glass-panel bg-surface-container/20 p-6 rounded-3xl flex flex-col items-center border border-outline-variant/10 shadow-[0_0_30px_rgba(255,255,255,0.02)]">
 <Network size={40} className="text-on-surface-variant/30 mb-2" />
 <p className="text-on-surface-variant font-label tracking-widest text-xs uppercase">No evaluation points</p>
 </div>
 </div>
 </div>
 );
 }

 return (
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.2 }}
 className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden"
 >
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <ScatterChart className="text-primary w-5 h-5" />
 Hallucination vs Grounding
 </h3>
 <div className="flex gap-3">
 <div className="flex items-center gap-1.5 bg-accent/20 px-2 py-1 rounded border border-accent/30">
 <div className="w-2 h-2 rounded-full bg-accent shadow-[0_0_8px_rgba(236, 72, 153,0.6)]"></div>
 <span className="text-[10px] font-bold tracking-widest text-accent uppercase">
 PASS
 </span>
 </div>
 <div className="flex items-center gap-1.5 bg-error/20 px-2 py-1 rounded border border-error/30">
 <div className="w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(255, 68, 68,0.6)]"></div>
 <span className="text-[10px] font-bold tracking-widest text-error uppercase">
 FAIL
 </span>
 </div>
 </div>
 </div>
 <div className="h-[300px] border-l border-b border-outline-variant/30 relative ml-4 mb-4">
 {/* Scatter dots */}
 {dots.map((dot, i) => (
 <motion.div
 initial={{ scale: 0, opacity: 0 }}
 animate={{ scale: 1, opacity: 1 }}
 transition={{ delay: 0.4 + i * 0.05, type: 'spring', damping: 10 }}
 key={i}
 className={`absolute w-3 h-3 ${
 dot.pass ? 'bg-accent shadow-[0_0_10px_rgba(236, 72, 153,0.5)]' : 'bg-error shadow-[0_0_10px_rgba(255, 68, 68,0.5)]'
 } rounded-full`}
 style={{ left: dot.x, bottom: dot.y, transform: 'translate(-50%, 50%)' }}
 ></motion.div>
 ))}
 {/* Axis Labels */}
 <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 font-label text-[10px] uppercase tracking-[0.15em] text-on-surface-variant font-bold">
 Grounding Score (X)
 </span>
 <span className="absolute -left-[52px] top-1/2 -translate-y-1/2 -rotate-90 font-label text-[10px] uppercase tracking-[0.15em] text-on-surface-variant font-bold whitespace-nowrap">
 Faithfulness Score (Y)
 </span>
 </div>
 </motion.div>
 );
}
