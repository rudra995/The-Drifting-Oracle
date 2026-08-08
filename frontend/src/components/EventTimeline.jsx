import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CloudOff, Activity, Filter, Clock } from 'lucide-react';
import { fetchApi } from '../api';

export default function EventTimeline() {
 const [events, setEvents] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/governance-log')
 .then(setEvents)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 if (loading) {
 return (
 <section className="glass-panel rounded-2xl shadow-sm overflow-hidden">
 <div className="p-6 flex justify-between items-center border-b border-surface-container/30">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <Clock className="text-primary w-5 h-5" />
 Event Timeline
 </h3>
 </div>
 <div className="p-8 h-[300px] flex items-center justify-center relative">
 <div className="absolute inset-0 bg-primary/5 blur-3xl rounded-full" />
 <p className="text-on-surface-variant font-label text-sm animate-pulse relative z-10 glass-panel px-6 py-3 rounded-full border border-primary/20 bg-primary/5">
 Syncing governance log...
 </p>
 </div>
 </section>
 );
 }

 if (error || !events) {
 return (
 <section className="glass-panel rounded-2xl shadow-sm overflow-hidden">
 <div className="p-6 flex justify-between items-center border-b border-surface-container/30">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <Clock className="text-primary w-5 h-5" />
 Event Timeline
 </h3>
 </div>
 <div className="p-8 flex flex-col items-center justify-center gap-2 text-center">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">
 {error || 'Missing endpoint: /api/v1/governance-log'}
 </p>
 <p className="text-on-surface-variant text-sm">
 Required to display event timeline.
 </p>
 </div>
 </section>
 );
 }

 const eventList = Array.isArray(events) ? events : [];

 if (eventList.length === 0) {
 return (
 <section className="glass-panel rounded-2xl shadow-sm overflow-hidden">
 <div className="p-6 flex justify-between items-center border-b border-surface-container/30">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <Clock className="text-primary w-5 h-5" />
 Event Timeline
 </h3>
 </div>
 <div className="p-8 h-[300px] flex flex-col items-center justify-center gap-3 relative">
 <div className="absolute inset-0 bg-surface-container-highest/10 blur-[80px] rounded-full" />
 <div className="relative z-10 glass-panel bg-surface-container/20 p-6 rounded-3xl flex flex-col items-center border border-outline-variant/10 shadow-[0_0_30px_rgba(255,255,255,0.02)]">
 <Activity size={40} className="text-on-surface-variant/30 mb-2" />
 <p className="text-on-surface-variant font-label tracking-widest text-xs uppercase">No governance events</p>
 </div>
 </div>
 </section>
 );
 }

 // Map event_type to style
 const getTypeStyle = (eventType) => {
 const normalized = (eventType || '').toLowerCase();
 if (normalized.includes('drift') || normalized.includes('alert')) {
 return { bg: 'bg-error/10 border border-error/20', color: 'text-error' };
 }
 if (normalized.includes('train') || normalized.includes('eval')) {
 return { bg: 'bg-accent/10 border border-accent/20', color: 'text-accent' };
 }
 return { bg: 'bg-primary/10 border border-primary/20', color: 'text-primary' };
 };

 return (
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.4 }}
 className="glass-panel rounded-2xl shadow-sm overflow-hidden"
 >
 <div className="p-6 flex justify-between items-center border-b border-surface-container/30">
 <h3 className="font-headline text-xl font-bold text-on-surface flex items-center gap-2">
 <Clock className="text-primary w-5 h-5" />
 Event Timeline
 </h3>
 <button className="text-on-surface-variant hover:text-on-surface transition-colors">
 <Filter size={18} />
 </button>
 </div>
 <div className="overflow-x-auto">
 <table className="w-full text-left border-collapse">
 <thead>
 <tr className="bg-surface-container-low/50">
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/10">
 Timestamp
 </th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/10">
 Event Type
 </th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/10">
 Details
 </th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/10">
 Model ID
 </th>
 </tr>
 </thead>
 <tbody className="divide-y divide-surface-container-low/50">
 {eventList.map((event, i) => {
 const style = getTypeStyle(event.event_type);
 return (
 <motion.tr
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.5 + i * 0.05 }}
 key={i}
 className="hover:bg-primary-container/10 transition-colors group"
 >
 <td className="px-6 py-4 font-label text-sm text-on-surface-variant group-hover:text-on-surface transition-colors">
 {event.timestamp}
 </td>
 <td className="px-6 py-4">
 <span
 className={`${style.bg} ${style.color} px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wide inline-block`}
 >
 {event.event_type}
 </span>
 </td>
 <td className="px-6 py-4 font-label text-sm text-on-surface">
 {event.details}
 </td>
 <td className="px-6 py-4 text-on-surface-variant text-sm font-mono">
 {event.model_id || '—'}
 </td>
 </motion.tr>
 );
 })}
 </tbody>
 </table>
 </div>
 </motion.section>
 );
}
