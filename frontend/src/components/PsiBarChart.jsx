import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CloudOff, BarChart3, Activity } from 'lucide-react';
import { fetchApi } from '../api';

export default function PsiBarChart() {
 const [data, setData] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/drift-history')
 .then(setData)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 if (loading) {
 return (
 <div className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden">
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <BarChart3 className="text-primary w-5 h-5" />
 PSI Bar Chart
 </h3>
 <span className="text-accent font-label text-[10px] uppercase tracking-widest bg-accent-container/20 px-2 py-1 rounded">
 Threshold 0.25
 </span>
 </div>
 <div className="h-[300px] flex items-center justify-center relative">
 <div className="absolute inset-0 bg-primary/5 blur-3xl rounded-full" />
 <p className="text-on-surface-variant font-label text-sm animate-pulse relative z-10 glass-panel px-6 py-3 rounded-full border border-primary/20 bg-primary/5">
 Gathering signals...
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
 <BarChart3 className="text-primary w-5 h-5" />
 PSI Bar Chart
 </h3>
 </div>
 <div className="h-[300px] flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">
 {error || 'Missing endpoint: /api/v1/drift-history'}
 </p>
 <p className="text-on-surface-variant text-sm">
 Required to display PSI feature bars.
 </p>
 </div>
 </div>
 );
 }

 // Derive bars from drift history data
 const bars = Array.isArray(data) ? data.map((entry) => {
 const features = entry.drift_features || [];
 return features.map((f) => ({
 label: f.feature_name,
 height: `${Math.min((f.psi_score / 0.5) * 100, 100)}%`,
 alert: f.psi_score > 0.1,
 }));
 }).flat().slice(0, 8) : [];

 if (bars.length === 0) {
 return (
 <div className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden">
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <BarChart3 className="text-primary w-5 h-5" />
 PSI Bar Chart
 </h3>
 </div>
 <div className="h-[300px] flex flex-col items-center justify-center gap-3 relative">
 <div className="absolute inset-0 bg-surface-container-highest/10 blur-[80px] rounded-full" />
 <div className="relative z-10 glass-panel bg-surface-container/20 p-6 rounded-3xl flex flex-col items-center border border-outline-variant/10 shadow-[0_0_30px_rgba(255,255,255,0.02)]">
 <Activity size={40} className="text-on-surface-variant/30 mb-2" />
 <p className="text-on-surface-variant font-label tracking-widest text-xs uppercase">No active signals</p>
 </div>
 </div>
 </div>
 );
 }

 return (
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.1 }}
 className="glass-panel p-8 rounded-2xl shadow-sm relative overflow-hidden"
 >
 <div className="flex justify-between items-center mb-8 border-b border-surface-container/30 pb-4">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <BarChart3 className="text-primary w-5 h-5" />
 PSI Bar Chart
 </h3>
 <span className="text-accent font-label text-[10px] uppercase tracking-widest bg-accent/10 border border-accent/20 px-2 py-1 rounded-md">
 Threshold 0.25
 </span>
 </div>
 <div className="h-[300px] flex justify-between gap-4 relative pb-6 border-b border-outline-variant/10">
 <div className="absolute bottom-[calc(25%+24px)] left-0 w-full border-t-2 border-dashed border-error/50 z-10">
 <span className="absolute -top-5 right-0 text-[10px] font-bold text-error uppercase tracking-widest bg-[#0D0D0D] px-1">
 Drift Alert
 </span>
 </div>
 {/* Bars */}
 {bars.map((bar, i) => (
 <div key={bar.label} className="flex-1 flex flex-col justify-end items-center group h-full relative z-0">
 <motion.div
 initial={{ height: '0%', opacity: 0 }}
 animate={{ height: bar.height, opacity: 1 }}
 transition={{ duration: 0.8, delay: 0.3 + i * 0.05, type: 'spring', damping: 15 }}
 className={`w-full ${
 bar.alert 
 ? 'bg-gradient-to-t from-error/60 to-error shadow-[0_0_15px_rgba(255,68,68,0.3)]' 
 : 'bg-gradient-to-t from-primary/40 to-primary/90 hover:to-primary shadow-[0_0_15px_rgba(104,245,155,0.2)]'
 } rounded-t-sm transition-all duration-300 group-hover:shadow-[0_0_20px_rgba(104,245,155,0.4)]`}
 >
 </motion.div>
 <span className="font-label text-[10px] mt-3 text-on-surface-variant truncate w-full text-center shrink-0">
 {bar.label}
 </span>
 </div>
 ))}
 </div>
 </motion.div>
 );
}
