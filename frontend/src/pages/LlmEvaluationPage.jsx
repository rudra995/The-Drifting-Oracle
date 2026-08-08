import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { fetchApi } from '../api';
import { Info, CloudOff, BrainCircuit, AlertTriangle, CheckCircle, Flame } from 'lucide-react';

export default function LlmEvaluationPage() {
 const [data, setData] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/llm-evaluations')
 .then(setData)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 const evaluations = Array.isArray(data) ? data : [];

 // Derive summary metrics from real data
 const totalEvals = evaluations.length;
 const rejectedCount = evaluations.filter((e) => e.status === 'rejected').length;
 const hallucinationRate = totalEvals > 0 ? ((rejectedCount / totalEvals) * 100).toFixed(1) : '—';
 const acceptableRate = totalEvals > 0 ? (((totalEvals - rejectedCount) / totalEvals) * 100).toFixed(1) : '—';

 // Find most recent hallucination for the findings card
 const latestRejection = evaluations.find((e) => e.status === 'rejected');

 return (
 <motion.main 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ duration: 0.8 }}
 className="max-w-7xl mx-auto px-8 py-12 space-y-10 relative z-10"
 >
 {/* Decorative blurs */}
 <div className="fixed top-20 right-20 w-[400px] h-[400px] bg-accent/-[100px] pointer-events-none" />
 <div className="fixed bottom-20 left-20 w-[400px] h-[400px] bg-primary/-[100px] pointer-events-none" />

 {/* Page Header */}
 <div className="flex flex-col gap-2">
 <h1 className="font-headline text-5xl font-semibold tracking-tight text-on-surface flex items-center gap-4">
 LLM Evaluation
 </h1>
 <span className="font-label text-xs uppercase tracking-[0.2em] text-outline flex items-center gap-2">
 <Flame size={14} className="text-tertiary" /> Explainability &amp; Compliance Assurance
 </span>
 </div>

 {/* Section 1: Pipeline Context & Summary Metrics */}
 <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
 <motion.div 
 initial={{ opacity: 0, y: 15 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.1 }}
 className="lg:col-span-3 glass-panel p-8 rounded-2xl space-y-6 shadow-sm border border-outline-variant/20"
 >
 <div className="flex items-start gap-4 glass-panel bg-surface-container/30 p-4 rounded-xl border border-outline-variant/30 text-sm text-on-surface-variant mb-4">
 <Info className="text-primary mt-0.5 shrink-0" size={20} />
 <p className="leading-loose"><strong className="text-primary tracking-widest uppercase text-xs">Automated Pipeline Active:</strong> Explanations are automatically generated from model predictions and evaluated using LLM-based validation. The system continuously monitors for hallucination and factual grounding violations.</p>
 </div>

 {loading ? (
 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
 {[1, 2, 3].map((i) => (
 <div key={i} className="glass-panel p-6 rounded-xl border border-outline-variant/10 shadow-sm flex flex-col justify-center items-center animate-pulse">
 <div className="h-3 bg-surface-container rounded w-1/2 mb-4"></div>
 <div className="h-8 bg-surface-container rounded w-1/3"></div>
 </div>
 ))}
 </div>
 ) : error ? (
 <div className="glass-panel bg-error/5 border border-error/20 rounded-xl p-8 text-center text-error flex flex-col items-center gap-2">
 <CloudOff size={32} />
 <p className="font-headline font-bold text-lg">{error}</p>
 <p className="text-on-surface-variant text-sm mt-1">Required to display evaluation metrics.</p>
 </div>
 ) : (
 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
 <div className="glass-panel p-6 rounded-xl border border-outline-variant/10 shadow-sm flex flex-col justify-center items-center group hover:border-primary/50 transition-colors">
 <span className="font-label text-[10px] font-bold uppercase tracking-widest text-outline mb-2 group-hover:text-primary transition-colors">Total Evaluations</span>
 <span className="font-headline text-4xl font-extrabold text-on-surface ">{totalEvals}</span>
 </div>
 <div className="glass-panel p-6 rounded-xl border border-outline-variant/10 shadow-sm flex flex-col justify-center items-center group hover:border-error/50 transition-colors">
 <span className="font-label text-[10px] font-bold uppercase tracking-widest text-outline mb-2 group-hover:text-error transition-colors">Hallucination Rate</span>
 <span className="font-headline text-4xl font-extrabold text-error ">{hallucinationRate}%</span>
 </div>
 <div className="glass-panel p-6 rounded-xl border border-outline-variant/10 shadow-sm flex flex-col justify-center items-center group hover:border-tertiary/50 transition-colors">
 <span className="font-label text-[10px] font-bold uppercase tracking-widest text-outline mb-2 group-hover:text-tertiary transition-colors">Acceptable Explanations</span>
 <span className="font-headline text-4xl font-extrabold text-tertiary ">{acceptableRate}%</span>
 </div>
 </div>
 )}
 </motion.div>
 </section>

 {/* Section 2: Results Display */}
 {!loading && !error && (
 <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
 {/* Scatter Plot */}
 <motion.div 
 initial={{ opacity: 0, scale: 0.95 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: 0.2 }}
 className="lg:col-span-4 glass-panel p-8 rounded-2xl shadow-sm border border-outline-variant/20 flex flex-col justify-between relative overflow-hidden"
 >
 <div>
 <h3 className="font-headline text-xl font-bold mb-2 text-on-surface tracking-tight">Hallucination vs Grounding</h3>
 <p className="text-xs text-on-surface-variant mb-6 font-mono tracking-wide">Each point represents one evaluated explanation.</p>

 <div className="w-full h-48 border-l-2 border-b-2 border-outline-variant/30 relative mt-4">
 <span className="absolute -left-8 top-1/2 -rotate-90 text-[10px] font-bold uppercase text-outline tracking-wider">Hallucination</span>
 <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-bold uppercase text-outline tracking-wider">Grounding</span>

 {evaluations.length === 0 ? (
 <div className="absolute inset-0 flex items-center justify-center">
 <p className="text-on-surface-variant text-sm">No data points.</p>
 </div>
 ) : (
 evaluations.map((ev, idx) => {
 const x = (ev.factual_grounding_score || 0) * 100;
 const y = (ev.hallucination_score || 0) * 100;
 const isRejected = ev.status === 'rejected';
 return (
 <motion.div
 initial={{ opacity: 0, scale: 0 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: 0.3 + (idx * 0.05) }}
 key={idx}
 className={`absolute ${isRejected ? 'w-3 h-3 bg-error shadow-[0_0_8px_rgba(255, 68, 68,0.8)] border border-red-200' : 'w-2 h-2 bg-tertiary shadow-[0_0_5px_rgba(244, 114, 182,0.6)]'} rounded-full cursor-pointer hover:scale-150 transition-transform`}
 style={{ left: `${x}%`, bottom: `${100 - y}%` }}
 title={`Grounding: ${(ev.factual_grounding_score || 0).toFixed(2)}, Hallucination: ${(ev.hallucination_score || 0).toFixed(2)}`}
 />
 );
 })
 )}
 </div>
 </div>
 <div className="mt-8 pt-6 border-t border-outline-variant/10 flex items-center gap-6 text-xs font-mono font-bold font-label uppercase tracking-widest">
 <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_5px_rgba(244, 114, 182,0.6)]"></span> Acceptable</div>
 <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-error shadow-[0_0_5px_rgba(255, 68, 68,0.6)]"></span> Rejected</div>
 </div>
 </motion.div>

 {/* Findings Card */}
 <motion.div 
 initial={{ opacity: 0, x: 20 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.25 }}
 className={`lg:col-span-8 glass-panel p-8 rounded-2xl shadow-sm border ${rejectedCount > 0 ? 'border-error/20' : 'border-outline-variant/20'} flex flex-col gap-6 relative overflow-hidden`}
 >
 {rejectedCount > 0 && <div className="absolute top-0 right-0 w-64 h-64 bg-primary/-[60px] pointer-events-none" />}
 
 <div className="flex justify-between items-start relative z-10">
 <div>
 <h3 className="font-headline text-xl font-bold tracking-tight text-on-surface">Analysis Summary</h3>
 <p className="text-on-surface-variant text-sm mt-1 font-mono">
 {rejectedCount > 0
 ? `Found ${rejectedCount} rejected evaluation${rejectedCount > 1 ? 's' : ''}.`
 : 'All evaluations passed.'}
 </p>
 </div>
 {rejectedCount > 0 && (
 <div className="bg-error/10 border border-error/20 text-error px-4 py-1.5 rounded-full text-xs font-bold font-label flex items-center gap-1.5 shadow-[0_0_10px_rgba(255, 68, 68,0.1)]">
 <AlertTriangle size={16} />
 HALLUCINATION DETECTED
 </div>
 )}
 </div>
 <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
 <div className="space-y-4">
 <h4 className="font-label text-xs font-bold text-outline uppercase tracking-widest border-b border-outline-variant/20 pb-2">
 Issues Found
 </h4>
 {latestRejection?.issues_found && Array.isArray(latestRejection.issues_found) ? (
 <ul className="space-y-3">
 {latestRejection.issues_found.map((issue, idx) => (
 <li key={idx} className="flex items-start gap-3 bg-surface-container/30 p-3 rounded-lg border border-outline-variant/10">
 <AlertTriangle size={16} className="text-error mt-0.5 shrink-0" />
 <p className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">{issue}</p>
 </li>
 ))}
 </ul>
 ) : latestRejection?.issues_found ? (
 <div className="bg-surface-container/30 p-3 rounded-lg border border-outline-variant/10 flex items-start gap-3">
 <AlertTriangle size={16} className="text-error mt-0.5 shrink-0" />
 <p className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">{latestRejection.issues_found}</p>
 </div>
 ) : (
 <p className="text-sm text-on-surface-variant font-mono">No issues found.</p>
 )}
 </div>
 <div className="space-y-4">
 <h4 className="font-label text-xs font-bold text-outline uppercase tracking-widest border-b border-outline-variant/20 pb-2">
 Latest Rejection Details
 </h4>
 {latestRejection ? (
 <div className="space-y-4">
 <div className="bg-surface-container-highest/50 p-4 rounded-xl border border-outline-variant/10">
 <p className="text-sm text-on-surface italic leading-relaxed">&ldquo;{latestRejection.explanation}&rdquo;</p>
 </div>
 <div className="flex gap-4 text-xs font-mono font-bold tracking-wider">
 <span className="glass-panel px-3 py-1.5 rounded text-outline border-outline-variant/20">Grounding: <strong className="text-tertiary">{((latestRejection.factual_grounding_score || 0) * 100).toFixed(0)}%</strong></span>
 <span className="glass-panel px-3 py-1.5 rounded text-outline border-error/20">Hallucination: <strong className="text-error">{((latestRejection.hallucination_score || 0) * 100).toFixed(0)}%</strong></span>
 </div>
 </div>
 ) : (
 <p className="text-sm text-on-surface-variant font-mono">No rejections in current data.</p>
 )}
 </div>
 </div>
 </motion.div>
 </section>
 )}

 {/* Section 3: Evaluation History */}
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.4 }}
 className="space-y-4"
 >
 <div className="flex justify-between items-end px-1 border-b border-outline-variant/20 pb-4">
 <h3 className="font-headline text-2xl font-bold tracking-tight text-on-surface">Recent Evaluations</h3>
 <span className="text-[10px] uppercase font-bold text-outline tracking-widest">Auto-refreshing every 30s</span>
 </div>

 {loading ? (
 <div className="glass-panel min-h-[300px] flex items-center justify-center rounded-2xl shadow-sm">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading evaluations...</p>
 </div>
 ) : error ? (
 <div className="glass-panel min-h-[300px] border-error/20 bg-error/5 flex flex-col items-center justify-center gap-2 rounded-2xl shadow-sm">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">{error}</p>
 <p className="text-on-surface-variant text-sm">Required to display evaluation history.</p>
 </div>
 ) : evaluations.length === 0 ? (
 <div className="glass-panel min-h-[300px] flex flex-col items-center justify-center gap-2 rounded-2xl shadow-sm">
 <BrainCircuit size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No evaluations available yet.</p>
 </div>
 ) : (
 <div className="glass-panel rounded-2xl overflow-hidden shadow-sm border border-outline-variant/20">
 <table className="w-full text-left border-collapse">
 <thead>
 <tr className="bg-surface-container-high/50 border-b border-surface-container">
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-[0.2em] text-outline w-[15%]">Timestamp</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-[0.2em] text-outline w-[50%]">Generated Explanation</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-[0.2em] text-outline">Scores</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold uppercase tracking-[0.2em] text-outline">Status</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-surface-container/50">
 {evaluations.map((row, idx) => {
 const isRejected = row.status === 'rejected';
 const groundingPct = ((row.factual_grounding_score || 0) * 100).toFixed(0);
 const hallucinationPct = ((row.hallucination_score || 0) * 100).toFixed(0);

 return (
 <motion.tr
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.1 * Math.min(idx, 10) }}
 key={idx}
 className={`hover:bg-primary/5 transition-colors group ${isRejected ? 'bg-error/5 border-l-4 border-error' : 'border-l-4 border-transparent'}`}
 >
 <td className="px-6 py-4 text-xs font-mono font-bold text-on-surface-variant whitespace-nowrap group-hover:text-primary transition-colors">
 {row.timestamp}
 </td>
 <td className="px-6 py-4 text-sm text-on-surface leading-loose">
 <span className="font-medium text-[13px] italic">&ldquo;{row.explanation}&rdquo;</span>
 </td>
 <td className="px-6 py-4">
 <div className="flex flex-col gap-2 font-mono">
 <div className="flex items-center gap-2 text-[10px] uppercase font-bold w-full">
 <span className="text-outline w-12 tracking-widest">Ground</span>
 <span className="text-tertiary bg-tertiary/10 px-2 py-0.5 rounded">{groundingPct}%</span>
 </div>
 <div className="flex items-center gap-2 text-[10px] uppercase font-bold w-full">
 <span className="text-outline w-12 tracking-widest">Halluc</span>
 <span className={`${parseInt(hallucinationPct) > 20 ? 'text-error bg-error/10' : 'text-primary bg-primary/10'} px-2 py-0.5 rounded`}>
 {hallucinationPct}%
 </span>
 </div>
 </div>
 </td>
 <td className="px-6 py-4">
 <span className={`${isRejected ? 'border-error/30 text-error shadow-[0_0_10px_rgba(255, 68, 68,0.1)]' : 'border-tertiary/30 text-tertiary shadow-[0_0_10px_rgba(244, 114, 182,0.1)]'} glass-panel border px-3 py-1.5 rounded-full text-[10px] font-bold flex flex-col w-max uppercase tracking-wider`}>
 <span className="flex items-center gap-1.5">
 {isRejected ? <AlertTriangle size={14} /> : <CheckCircle size={14} />}
 {isRejected ? 'REJECTED: HALLUCINATION' : 'ACCEPTABLE'}
 </span>
 </span>
 </td>
 </motion.tr>
 );
 })}
 </tbody>
 </table>
 </div>
 )}
 </motion.section>
 </motion.main>
 );
}
