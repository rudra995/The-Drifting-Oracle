import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, CloudOff, CalendarCheck, Search, SlidersHorizontal, ChevronRight, TrendingUp, ShieldCheck } from 'lucide-react';
import { fetchApi } from '../api';

const filterTabs = ['ALL', 'MODEL_TRAINED', 'DRIFT_ALERT', 'EVAL_COMPLETED', 'ACCESS_CHANGE'];

const shieldItems = ['Bias Mitigation', 'Drift Intervention', 'Hallucination Trap'];

export default function GovernancePage() {
 const [activeFilter, setActiveFilter] = useState('ALL');

 // Dashboard metrics state
 const [metrics, setMetrics] = useState(null);
 const [metricsLoading, setMetricsLoading] = useState(true);
 const [metricsError, setMetricsError] = useState(null);

 // Governance log state
 const [events, setEvents] = useState(null);
 const [eventsLoading, setEventsLoading] = useState(true);
 const [eventsError, setEventsError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/dashboard-metrics')
 .then(setMetrics)
 .catch((err) => setMetricsError(err.message))
 .finally(() => setMetricsLoading(false));

 fetchApi('/api/v1/governance-log')
 .then(setEvents)
 .catch((err) => setEventsError(err.message))
 .finally(() => setEventsLoading(false));
 }, []);

 const eventList = Array.isArray(events) ? events : [];

 // Filter events based on active tab
 const filteredEvents = activeFilter === 'ALL'
 ? eventList
 : eventList.filter((ev) => {
 const type = (ev.event_type || '').toUpperCase().replace(/\s+/g, '_');
 return type.includes(activeFilter);
 });

 // Build stats from metrics data
 const stats = metricsLoading
 ? Array(6).fill({ label: '...', value: '—' })
 : metricsError
 ? null
 : metrics
 ? [
 { label: 'Total Models', value: metrics.total_models ?? '—', color: 'text-on-surface', barColor: 'bg-primary', barW: '50%' },
 { label: 'Drift Detections', value: metrics.drift_detections ?? '—', color: 'text-on-surface', barColor: 'bg-tertiary', barW: '12%' },
 { label: 'Drift Rate %', value: metrics.drift_rate != null ? `${metrics.drift_rate}%` : '—', color: 'text-error', barColor: 'bg-error', barW: `${Math.min(metrics.drift_rate || 0, 100)}%` },
 { label: 'Total LLM Evals', value: metrics.total_llm_evaluations ?? '—', color: 'text-on-surface', barColor: 'bg-primary', barW: '70%' },
 { label: 'Hallucination Rate %', value: metrics.hallucination_rate != null ? `${metrics.hallucination_rate}%` : '—', color: 'text-tertiary', barColor: 'bg-tertiary', barW: `${Math.min(metrics.hallucination_rate || 0, 100)}%` },
 { label: 'Total Governance Events', value: metrics.governance_events ?? '—', color: 'text-on-surface', barColor: 'bg-primary-dim', barW: '100%' },
 ]
 : null;

 // Map event_type to style
 const getEventTypeStyle = (eventType) => {
 const normalized = (eventType || '').toLowerCase();
 if (normalized.includes('drift') || normalized.includes('alert') || normalized.includes('critical')) {
 return { bg: 'bg-error/10', color: 'text-error', dot: 'bg-error' };
 }
 if (normalized.includes('train') || normalized.includes('model')) {
 return { bg: 'bg-tertiary/10', color: 'text-tertiary', dot: 'bg-tertiary' };
 }
 if (normalized.includes('access') || normalized.includes('permission')) {
 return { bg: 'bg-primary/10', color: 'text-primary', dot: 'bg-primary' };
 }
 if (normalized.includes('eval') || normalized.includes('completed')) {
 return { bg: 'bg-tertiary-fixed/10', color: 'text-tertiary-dim', dot: 'bg-tertiary-fixed' };
 }
 return { bg: 'bg-surface-container-highest', color: 'text-on-surface-variant', dot: 'bg-on-surface-variant' };
 };

 return (
 <>
 <motion.main 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ duration: 0.8 }}
 className="max-w-400 mx-auto px-8 py-10 space-y-8 relative z-10"
 >
 {/* Header */}
 <header className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
 <div>
 <h1 className="text-4xl font-headline font-bold tracking-tight mb-2 bg-clip-text text-transparent bg-gradient-to-r from-on-surface to-on-surface-variant">
 Governance Oversight
 </h1>
 <p className="text-on-surface-variant font-label text-sm uppercase tracking-widest font-medium">
 Compliance &amp; Audit Integrity Ledger
 </p>
 </div>
 <button
 onClick={() => {
 setMetricsLoading(true);
 setEventsLoading(true);
 fetchApi('/api/v1/dashboard-metrics')
 .then(setMetrics)
 .catch((err) => setMetricsError(err.message))
 .finally(() => setMetricsLoading(false));
 fetchApi('/api/v1/governance-log')
 .then(setEvents)
 .catch((err) => setEventsError(err.message))
 .finally(() => setEventsLoading(false));
 }}
 className="oracle-glow text-white px-6 py-2.5 rounded-xl font-headline font-semibold flex items-center gap-2 shadow-lg hover:opacity-90 hover:scale-105 active:scale-95 transition-all cursor-pointer"
 >
 <RefreshCw size={20} className={metricsLoading || eventsLoading ? "animate-spin" : ""} />
 Refresh Log
 </button>
 </header>

 {/* Summary Stats */}
 {metricsLoading ? (
 <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
 {[1, 2, 3, 4, 5, 6].map((i) => (
 <div key={i} className="glass-panel p-5 rounded-xl flex flex-col justify-between animate-pulse">
 <div className="h-3 bg-surface-container-highest rounded w-2/3 mb-4"></div>
 <div className="h-6 bg-surface-container-highest rounded w-1/3"></div>
 <div className="h-1.5 bg-surface-container-highest mt-2 rounded-full"></div>
 </div>
 ))}
 </div>
 ) : metricsError || !stats ? (
 <div className="glass-panel border-error/30 bg-error/5 rounded-xl p-8 text-center">
 <CloudOff size={32} className="text-error mx-auto mb-2" />
 <p className="text-error font-headline font-bold text-lg">
 {metricsError || 'Missing endpoint: /api/v1/dashboard-metrics'}
 </p>
 <p className="text-on-surface-variant text-sm mt-1">
 Required to display governance summary statistics.
 </p>
 </div>
 ) : (
 <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
 {stats.map((s, idx) => (
 <motion.div 
 initial={{ opacity: 0, y: 15 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.1 + idx * 0.05 }}
 key={s.label} 
 className="glass-panel p-5 rounded-2xl flex flex-col justify-between group hover:-translate-y-1 transition-transform"
 >
 <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none" />
 <span className="text-on-surface-variant text-xs font-label font-bold uppercase tracking-tighter relative z-10">
 {s.label}
 </span>
 <div className="mt-4 relative z-10">
 <span className={`text-2xl font-headline font-bold flex ${s.label.includes('Drift Rate') ? 'text-error ' : 'text-on-surface'}`}>{s.value}</span>
 <div className="h-1.5 w-full bg-surface-container-highest mt-2 rounded-full overflow-hidden">
 <motion.div 
 initial={{ width: 0 }}
 animate={{ width: s.barW }}
 transition={{ duration: 1, delay: 0.3 + idx * 0.1 }}
 className={`${s.barColor} h-full`} 
 />
 </div>
 </div>
 </motion.div>
 ))}
 </div>
 )}

 {/* Filter Bar */}
 <motion.div 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ delay: 0.3 }}
 className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 py-4 border-b border-outline-variant/10"
 >
 <div className="flex items-center gap-2 flex-wrap">
 {filterTabs.map((tab) => (
 <button
 key={tab}
 onClick={() => setActiveFilter(tab)}
 className={`px-5 py-2 glass-button text-xs font-label font-bold tracking-tight transition-all cursor-pointer ${
 activeFilter === tab
 ? 'oracle-glow text-white'
 : 'text-on-surface-variant hover:text-on-surface'
 }`}
 >
 {tab}
 </button>
 ))}
 </div>
 <div className="flex items-center gap-4">
 <div className="relative">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-outline" />
 <input
 className="bg-surface-container-highest/50 border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 focus:outline-none w-64 text-on-surface placeholder:text-outline transition-all"
 placeholder="Search event history..."
 type="text"
 />
 </div>
 <button className="flex items-center gap-2 text-on-surface-variant text-sm font-label hover:text-primary transition-colors cursor-pointer border border-outline-variant/20 px-3 py-2 rounded-xl glass-panel">
 <SlidersHorizontal size={16} />
 Advanced Filters
 </button>
 </div>
 </motion.div>

 {/* Audit Event Log */}
 {eventsLoading ? (
 <div className="glass-panel min-h-[300px] flex items-center justify-center rounded-2xl">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading governance log...</p>
 </div>
 ) : eventsError ? (
 <div className="glass-panel border-error/20 bg-error/5 min-h-[300px] flex flex-col items-center justify-center gap-2 rounded-2xl">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">{eventsError}</p>
 <p className="text-on-surface-variant text-sm">Required to display governance event log.</p>
 </div>
 ) : filteredEvents.length === 0 ? (
 <div className="glass-panel min-h-[300px] flex flex-col items-center justify-center gap-2 rounded-2xl">
 <CalendarCheck size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No governance events found.</p>
 </div>
 ) : (
 <motion.div 
 initial={{ opacity: 0, y: 10 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.4 }}
 className="glass-panel rounded-2xl overflow-hidden shadow-sm"
 >
 <table className="w-full text-left border-collapse">
 <thead>
 <tr className="bg-surface-container-high/50 border-b border-surface-container">
 <th className="px-6 py-4 text-xs font-label font-bold uppercase tracking-widest text-on-surface-variant">Timestamp</th>
 <th className="px-6 py-4 text-xs font-label font-bold uppercase tracking-widest text-on-surface-variant">Event Type</th>
 <th className="px-6 py-4 text-xs font-label font-bold uppercase tracking-widest text-on-surface-variant">Details</th>
 <th className="px-6 py-4 text-xs font-label font-bold uppercase tracking-widest text-on-surface-variant">Model ID</th>
 <th className="px-6 py-4 text-xs font-label font-bold uppercase tracking-widest text-on-surface-variant text-right">Action</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-outline-variant/10">
 {filteredEvents.map((ev, i) => {
 const style = getEventTypeStyle(ev.event_type);
 return (
 <motion.tr
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.1 * Math.min(i, 10) }}
 key={i}
 className="hover:bg-primary/5 transition-colors cursor-pointer group"
 >
 <td className="px-6 py-5">
 <span className="text-on-surface font-mono font-bold text-sm tracking-tighter">{ev.timestamp}</span>
 </td>
 <td className="px-6 py-5">
 <span className={`${style.bg} ${style.color} px-3 py-1 rounded-md border border-${style.color?.split('-')[1]}/20 text-[10px] font-bold uppercase tracking-tighter flex items-center gap-2 max-w-fit shadow-sm`}>
 <span className={`w-1.5 h-1.5 ${style.dot} rounded-full shadow-[0_0_5px_currentColor]`}></span>
 {ev.event_type}
 </span>
 </td>
 <td className="px-6 py-5">
 <div className="max-w-md">
 <span className="text-on-surface-variant group-hover:text-on-surface transition-colors font-medium text-sm block">{ev.details}</span>
 </div>
 </td>
 <td className="px-6 py-5">
 <span className="text-outline font-mono text-xs">{ev.model_id || '—'}</span>
 </td>
 <td className="px-6 py-5 text-right">
 <ChevronRight size={18} className="text-outline inline-block group-hover:text-primary group-hover:translate-x-1 transition-all" />
 </td>
 </motion.tr>
 );
 })}
 </tbody>
 </table>

 {/* Pagination */}
 <div className="px-6 py-4 bg-surface-container-high/30 border-t border-surface-container flex items-center justify-between">
 <span className="text-on-surface-variant text-xs font-label tracking-widest">
 Showing <span className="font-bold text-primary">{filteredEvents.length}</span> records
 </span>
 </div>
 </motion.div>
 )}

 {/* Secondary Insights */}
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.6 }}
 className="grid grid-cols-1 lg:grid-cols-3 gap-8"
 >
 {/* Policy Compliance Trend */}
 <div className="lg:col-span-2 glass-panel p-8 rounded-2xl">
 <div className="flex justify-between items-start mb-6 border-b border-surface-container/30 pb-4">
 <div>
 <h3 className="text-xl font-headline font-bold text-on-surface flex items-center gap-2">
 <TrendingUp className="text-primary w-5 h-5" />
 Policy Compliance Trend
 </h3>
 <p className="text-sm text-on-surface-variant font-label tracking-widest mt-1">
 Governance adherence over the last 30 days
 </p>
 </div>
 </div>
 {eventsLoading ? (
 <div className="h-64 flex items-center justify-center">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading...</p>
 </div>
 ) : eventsError ? (
 <div className="h-64 flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold text-sm">{eventsError}</p>
 </div>
 ) : eventList.length === 0 ? (
 <div className="h-64 flex flex-col items-center justify-center gap-2">
 <TrendingUp size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No compliance data to chart.</p>
 </div>
 ) : (
 <div className="h-64 flex items-center justify-center bg-surface-container/20 rounded-xl border border-surface-container border-dashed">
 <p className="text-on-surface-variant text-sm font-label tracking-widest">
 Compliance visualizer rendering requires aggregation from <strong className="text-primary">/api/v1/governance-log</strong>.
 </p>
 </div>
 )}
 </div>

 {/* Integrity Shield */}
 <div className="oracle-glow bg-primary/10 border border-primary/30 p-8 rounded-2xl flex flex-col justify-between relative overflow-hidden group">
 <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent pointer-events-none" />
 <div className="relative z-10">
 <h3 className="text-xl font-headline font-bold text-on-surface flex items-center gap-2 ">
 <ShieldCheck className="text-accent" />
 Integrity Shield
 </h3>
 <p className="text-sm text-on-surface-variant font-label tracking-widest mt-2 leading-relaxed">
 Automatic guardrail enforcement is currently active and protecting production traffic.
 </p>
 </div>
 <div className="mt-8 space-y-3 relative z-10">
 {shieldItems.map((item, idx) => (
 <motion.div
 initial={{ opacity: 0, x: 20 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.8 + idx * 0.1 }}
 key={item}
 className="flex items-center justify-between glass-panel bg-white/5 border border-white/10 p-3.5 rounded-xl hover:bg-white/10 transition-colors"
 >
 <span className="text-sm font-bold text-on-surface">{item}</span>
 <ShieldCheck size={18} className="text-accent " />
 </motion.div>
 ))}
 </div>
 <button className="mt-8 mx-auto w-full glass-button text-on-surface font-headline font-bold text-sm tracking-widest uppercase py-3 border border-outline-variant/30 hover:border-primary cursor-pointer relative z-10">
 Update Policy Config
 </button>
 </div>
 </motion.div>
 </motion.main>

 {/* Decorative blurs */}
 <div className="fixed -bottom-32 -right-32 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
 <div className="fixed top-1/4 -left-32 w-[400px] h-[400px] bg-accent/-[120px] pointer-events-none" />
 <div className="fixed -top-32 right-1/4 w-[300px] h-[300px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />
 </>
 );
}
