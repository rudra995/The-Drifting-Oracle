import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Info, AlertTriangle, CheckCircle, CloudOff, Filter, Download, BarChart2, History, LayoutGrid, Activity } from 'lucide-react';
import { fetchApi } from '../api';

export default function DriftDetectionPage() {
 const [psiData, setPsiData] = useState(null);
 const [psiLoading, setPsiLoading] = useState(true);
 const [psiError, setPsiError] = useState(null);

 const [historyData, setHistoryData] = useState(null);
 const [historyLoading, setHistoryLoading] = useState(true);
 const [historyError, setHistoryError] = useState(null);

 useEffect(() => {
 fetchApi('/psi')
 .then(setPsiData)
 .catch((err) => setPsiError(err.message))
 .finally(() => setPsiLoading(false));

 fetchApi('/api/v1/drift-history')
 .then(setHistoryData)
 .catch((err) => setHistoryError(err.message))
 .finally(() => setHistoryLoading(false));
 }, []);

 // Derive feature breakdown from the latest drift history entry
 const latestEntry = Array.isArray(historyData) && historyData.length > 0 ? historyData[0] : null;
 const features = latestEntry?.drift_features || [];
  
  const currentDriftStatus = latestEntry ? (latestEntry.drift_detected ? 'CRITICAL' : 'STABLE') : 'STABLE';
  const currentPsiScore = latestEntry ? latestEntry.overall_psi : null;
  const currentMessage = latestEntry ? (latestEntry.drift_detected ? 'Significant population stability shifts observed.' : 'System operating normally.') : 'Awaiting data...';

 return (
 <motion.main 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ duration: 0.8 }}
 className="max-w-360 mx-auto p-8 space-y-12"
 >
 {/* Header & Control Panel */}
 <section className="space-y-8">
 <div className="flex flex-col gap-2">
 <h1 className="font-headline text-4xl font-semibold tracking-tight text-on-surface bg-clip-text text-transparent bg-gradient-to-r from-on-surface to-on-surface-variant">
 Drift Detection
 </h1>
 <p className="font-label text-sm tracking-widest text-outline uppercase font-medium">
 Statistical Integrity Monitor • Real-time Validation
 </p>
 </div>

 {/* System State Panel */}
 <motion.div 
 initial={{ opacity: 0, y: 10 }}
 animate={{ opacity: 1, y: 0 }}
 className="glass-panel rounded-2xl p-8 space-y-6 shadow-sm border border-outline-variant/20 relative overflow-hidden"
 >
 {/* subtle glow */}
 <div className="absolute top-0 left-0 w-1/2 h-full bg-primary/5 blur-3xl rounded-full" />
 <div className="flex justify-between items-center bg-surface-container-highest/50 p-3 rounded-xl border border-outline-variant/30 text-sm font-medium text-on-surface-variant relative z-10">
 <span className="flex items-center gap-2">
 <Info size={16} className="text-primary" />
 Data ingestion is automated. System continuously monitors incoming batches.
 </span>
 {psiLoading || historyLoading ? (
 <span className="bg-surface-container px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider animate-pulse">
 Loading...
 </span>
 ) : psiError ? (
 <span className="bg-error/10 text-error px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider">
 Offline
 </span>
 ) : currentDriftStatus === 'CRITICAL' ? (
 <span className="bg-error/10 text-error px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
 <span className="w-2 h-2 mr-1 rounded-full bg-error animate-pulse"></span> Drift Detected
 </span>
 ) : (
 <span className="bg-tertiary/10 text-tertiary px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
 <span className="w-2 h-2 mr-1 rounded-full bg-tertiary"></span> Stable
 </span>
 )}
 </div>
 </motion.div>
 </section>

 {/* Results Banner & PSI Score */}
 <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
 {/* Drift Status Banner */}
 <motion.div 
 initial={{ opacity: 0, scale: 0.98 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: 0.1 }}
 className="lg:col-span-8 glass-panel rounded-2xl p-10 flex flex-col items-start gap-6 border-l-8 overflow-hidden relative"
 style={{ borderLeftColor: currentDriftStatus === 'CRITICAL' ? 'rgb(255, 68, 68)' : 'rgb(236, 72, 153)' }}
 >
 {currentDriftStatus === 'CRITICAL' && (
 <div className="absolute top-0 right-0 w-64 h-64 bg-primary/-[80px] rounded-full pointer-events-none" />
 )}
 {psiLoading || historyLoading ? (
 <div className="flex items-center gap-4 relative z-10">
 <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
 <span className="text-on-surface-variant font-medium">Analyzing drift status...</span>
 </div>
 ) : psiError ? (
 <div className="flex flex-col gap-4 relative z-10">
 <div className="flex items-center gap-4">
 <CloudOff size={32} className="text-error" />
 <h2 className="font-headline text-2xl font-bold text-error">{psiError}</h2>
 </div>
 <p className="text-on-surface-variant">Unable to fetch PSI data from the backend.</p>
 </div>
 ) : currentDriftStatus === 'CRITICAL' ? (
 <>
 <div className="absolute -right-4 -top-4 opacity-5 pointer-events-none">
 <AlertTriangle size={240} />
 </div>
 <div className="flex items-center gap-4 relative z-10">
 <div className="bg-error/20 border border-error/30 p-3 rounded-2xl flex items-center justify-center shadow-[0_0_15px_rgba(255, 68, 68,0.3)]">
 <AlertTriangle className="text-error p-1" size={32} />
 </div>
 <h2 className="font-headline text-3xl font-extrabold text-error tracking-tight ">
 DRIFT DETECTED
 </h2>
 </div>
 <div className="space-y-4 max-w-2xl relative z-10">
 <p className="text-on-surface leading-relaxed font-medium">
 Significant population stability shifts observed. Current model predictions may be
 compromised due to covariate shift. PSI score: <span className="font-bold text-error">{currentPsiScore?.toFixed(4)}</span>
 </p>
 <div className="bg-error-container/10 backdrop-blur-md rounded-xl p-5 border border-error/20">
 <p className="font-label text-xs text-error font-bold uppercase tracking-widest mb-2 flex items-center gap-2">
 <Activity size={14} /> Recommendation
 </p>
 <p className="text-sm font-semibold text-on-surface">
 Initiate Champion-Challenger re-validation protocol and investigate data source pipeline integrity.
 </p>
 </div>
 </div>
 </>
 ) : (
 <div className="flex items-center gap-4 relative z-10">
 <div className="bg-accent/20 border border-accent/20 p-3 rounded-2xl flex items-center justify-center shadow-[0_0_15px_rgba(236, 72, 153,0.2)]">
 <CheckCircle className="text-accent" size={32} />
 </div>
 <div>
 <h2 className="font-headline text-3xl font-extrabold text-on-surface tracking-tight">
 NO DRIFT DETECTED
 </h2>
 <p className="text-on-surface-variant mt-1">
 {currentMessage}
 </p>
 </div>
 </div>
 )}
 </motion.div>

 {/* PSI Score Card */}
 <motion.div 
 initial={{ opacity: 0, scale: 0.98 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: 0.2 }}
 className="lg:col-span-4 h-full glass-panel rounded-2xl p-8 flex flex-col justify-between group relative overflow-hidden"
 >
 {/* Subtly animated glow on the card background */}
 <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
 <div className="space-y-2 relative z-10">
 <p className="font-label text-xs font-bold uppercase tracking-[0.2em] text-outline flex items-center gap-2">
 <BarChart2 size={16} className="text-primary" /> Overall PSI Score
 </p>
 {psiLoading || historyLoading ? (
 <div className="text-4xl font-headline font-bold text-on-surface-variant animate-pulse pt-2">
 Loading...
 </div>
 ) : psiError ? (
 <div className="text-lg font-headline font-bold text-error">
 {psiError}
 </div>
 ) : (
 <div className={`text-6xl font-headline font-bold tracking-tighter pt-2 -lg ${
 currentDriftStatus === 'CRITICAL' ? 'text-error' : 'text-accent'
 }`}>
 {currentPsiScore != null ? currentPsiScore.toFixed(4) : '—'}
 </div>
 )}
 </div>
 {!psiLoading && !psiError && psiData && (
 <div className="mt-8 space-y-4 relative z-10">
 <div className="flex justify-between items-end border-b border-outline-variant/20 pb-2">
 <span className="text-xs font-medium text-outline">Threshold</span>
 <span className="text-sm font-bold text-on-surface">{psiData?.threshold != null ? psiData.threshold.toFixed(3) : '0.250'}</span>
 </div>
 <div className="flex justify-between items-end border-b border-outline-variant/20 pb-2">
 <span className="text-xs font-medium text-outline">Status</span>
 <span className={`text-sm font-bold uppercase tracking-widest ${
 currentDriftStatus === 'CRITICAL' ? 'text-error' : 'text-accent'
 }`}>
 {currentDriftStatus}
 </span>
 </div>
 </div>
 )}
 </motion.div>
 </section>

 {/* Feature Stability Breakdown */}
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.3 }}
 className="space-y-6"
 >
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
 <h3 className="font-headline text-2xl font-bold tracking-tight">
 Feature Stability Breakdown
 </h3>
 <div className="flex gap-4">
 <button className="bg-surface-container-high border border-outline-variant/30 px-4 py-2 rounded-xl text-xs font-bold text-on-surface-variant flex items-center gap-2 hover:bg-surface-container-highest hover:text-on-surface transition-colors cursor-pointer">
 <Filter size={16} /> Filter High Drift
 </button>
 <button className="bg-surface-container-high border border-outline-variant/30 px-4 py-2 rounded-xl text-xs font-bold text-on-surface-variant flex items-center gap-2 hover:bg-surface-container-highest hover:text-on-surface transition-colors cursor-pointer">
 <Download size={16} /> Export Report
 </button>
 </div>
 </div>

 {historyLoading ? (
 <div className="glass-panel rounded-2xl shadow-sm p-8 flex items-center justify-center">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading feature data...</p>
 </div>
 ) : historyError ? (
 <div className="glass-panel rounded-2xl shadow-sm p-8 flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">{historyError}</p>
 <p className="text-on-surface-variant text-sm">Required to display feature stability breakdown.</p>
 </div>
 ) : features.length === 0 ? (
 <div className="glass-panel rounded-2xl shadow-sm p-8 flex flex-col items-center justify-center gap-2">
 <LayoutGrid size={32} className="text-on-surface-variant" />
 <p className="text-on-surface-variant font-medium">No feature drift data available yet.</p>
 </div>
 ) : (
 <div className="glass-panel rounded-2xl shadow-sm overflow-hidden border border-outline-variant/20">
 <table className="w-full text-left border-collapse">
 <thead className="bg-surface-container-high text-on-surface-variant font-label text-[10px] uppercase tracking-widest font-bold">
 <tr>
 <th className="px-6 py-4">Feature Name</th>
 <th className="px-6 py-4">PSI Value</th>
 <th className="px-6 py-4 text-right">Status</th>
 </tr>
 </thead>
 <tbody className="text-sm divide-y divide-outline-variant/10 font-bold">
 {features.map((f) => {
 const isCritical = f.psi_score > 0.1;
 return (
 <tr key={f.feature_name} className={`${isCritical ? 'bg-error/5 hover:bg-error/10' : 'hover:bg-primary-container/10'} transition-colors group`}>
 <td className="px-6 py-4 font-mono text-on-surface group-hover:text-primary transition-colors">{f.feature_name}</td>
 <td className={`px-6 py-4 font-mono ${isCritical ? 'text-error' : 'text-accent'}`}>
 {typeof f.psi_score === 'number' ? f.psi_score.toFixed(4) : f.psi_score}
 </td>
 <td className="px-6 py-4 text-right">
 <span className={`${isCritical ? 'bg-error/10 border-error/30 text-error' : 'bg-accent/10 border-accent/20 text-accent'} border text-[10px] px-3 py-1.5 rounded-full uppercase tracking-widest`}>
 {isCritical ? 'Critical' : 'Stable'}
 </span>
 </td>
 </tr>
 );
 })}
 </tbody>
 </table>
 </div>
 )}
 </motion.section>

 {/* Bottom: PSI Magnitude & Audit Trail */}
 <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 {/* PSI Magnitude Chart */}
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.4 }}
 className="glass-panel rounded-2xl p-8 shadow-sm space-y-6 flex flex-col justify-between"
 >
 <div className="flex justify-between items-start border-b border-surface-container/30 pb-4">
 <h4 className="font-headline text-xl font-bold tracking-tight text-on-surface flex items-center gap-2">
 <BarChart2 className="text-primary w-5 h-5" />
 PSI Magnitude by Feature
 </h4>
 </div>
 {historyLoading ? (
 <div className="h-64 flex items-center justify-center">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading...</p>
 </div>
 ) : historyError ? (
 <div className="h-64 flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold text-sm">{historyError}</p>
 </div>
 ) : features.length === 0 ? (
 <div className="h-64 flex flex-col items-center justify-center gap-2">
 <BarChart2 size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No data available.</p>
 </div>
 ) : (
 <>
 <div className="h-64 flex items-end gap-3 px-2 border-b border-surface-container pb-2">
 {features.map((f, i) => {
 const heightPct = Math.min((f.psi_score / 0.5) * 100, 100);
 const significant = f.psi_score > 0.1;
 return (
 <div
 key={f.feature_name}
 className={`flex-1 ${significant ? 'bg-error/10 hover:bg-error/20' : 'bg-primary/10 hover:bg-primary/20'} rounded-t-md flex flex-col justify-end items-center group relative cursor-crosshair transition-colors`}
 style={{ height: `${heightPct}%` }}
 >
 <motion.div
 initial={{ height: 0 }}
 animate={{ height: '100%' }}
 transition={{ delay: 0.5 + i * 0.05, duration: 0.8 }}
 className={`${significant ? 'bg-error shadow-[0_0_10px_rgba(255, 68, 68,0.4)]' : 'bg-primary/80 shadow-[0_0_10px_rgba(236, 72, 153,0.2)]'} w-full rounded-t-sm transition-all`}
 ></motion.div>
 <span className="absolute -bottom-6 text-[10px] font-bold text-outline uppercase tracking-[0.1em] truncate w-full text-center">
 {f.feature_name}
 </span>
 </div>
 );
 })}
 </div>
 <div className="pt-8 flex justify-center gap-6">
 <div className="flex items-center gap-2">
 <div className="w-3 h-3 bg-error rounded-sm shadow-[0_0_5px_rgba(255, 68, 68,0.5)]"></div>
 <span className="text-[10px] font-bold text-on-surface uppercase tracking-widest">
 Significant (&gt;0.1)
 </span>
 </div>
 <div className="flex items-center gap-2">
 <div className="w-3 h-3 bg-primary rounded-sm shadow-[0_0_5px_rgba(236, 72, 153,0.3)]"></div>
 <span className="text-[10px] font-bold text-on-surface uppercase tracking-widest">
 Insignificant (&lt;0.1)
 </span>
 </div>
 </div>
 </>
 )}
 </motion.div>

 {/* Audit Trail / History */}
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.5 }}
 className="glass-panel rounded-2xl p-8 shadow-sm space-y-6 flex flex-col justify-between"
 >
 <div className="flex justify-between items-start border-b border-surface-container/30 pb-4">
 <h4 className="font-headline text-xl font-bold tracking-tight flex items-center gap-2">
 <History className="text-primary w-5 h-5" />
 Audit Trail / History
 </h4>
 </div>
 {historyLoading ? (
 <div className="h-48 flex items-center justify-center">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading...</p>
 </div>
 ) : historyError ? (
 <div className="h-48 flex flex-col items-center justify-center gap-2">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold text-sm">{historyError}</p>
 </div>
 ) : !Array.isArray(historyData) || historyData.length === 0 ? (
 <div className="h-48 flex flex-col items-center justify-center gap-2">
 <History size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No audit history available.</p>
 </div>
 ) : (
 <>
 <div className="space-y-1">
 <div className="grid grid-cols-3 font-label text-[10px] uppercase font-bold tracking-widest text-outline-variant py-2 px-2 border-b border-outline-variant/10">
 <div>Date</div>
 <div>PSI</div>
 <div className="text-right">Result</div>
 </div>
 {historyData.map((row, i) => {
 const drifted = row.drift_detected;
 return (
 <motion.div
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.6 + i * 0.05 }}
 key={i}
 className="grid grid-cols-3 items-center text-sm py-4 px-2 border-b border-outline-variant/5 hover:bg-surface-container-highest/20 transition-colors"
 >
 <div className="text-outline font-mono text-xs">{row.timestamp || '—'}</div>
 <div className={`font-mono font-bold ${drifted ? 'text-error' : 'text-accent'}`}>
 {row.overall_psi != null ? (typeof row.overall_psi === 'number' ? row.overall_psi.toFixed(4) : row.overall_psi) : '—'}
 </div>
 <div className="text-right">
 <span className={`${drifted ? 'text-error border-error/20 bg-error/10' : 'text-accent border-accent/20 bg-accent/10'} font-bold text-[10px] uppercase border px-2 py-1 rounded-md tracking-wider`}>
 {drifted ? 'Failed' : 'Passed'}
 </span>
 </div>
 </motion.div>
 );
 })}
 </div>
 <button className="w-full text-center text-primary font-bold text-xs uppercase tracking-widest pt-2 hover:underline hover:text-accent transition-colors cursor-pointer">
 View Full Audit History
 </button>
 </>
 )}
 </motion.div>
 </section>
 </motion.main>
 );
}
