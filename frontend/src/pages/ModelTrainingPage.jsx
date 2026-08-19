import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { fetchApi } from '../api';
import { Database, Search, CloudOff, Target, FlaskConical, Network, Boxes } from 'lucide-react';

export default function ModelTrainingPage() {
 const [models, setModels] = useState(null);
 const [modelsLoading, setModelsLoading] = useState(true);
 const [modelsError, setModelsError] = useState(null);

 const [health, setHealth] = useState(null);
 const [healthLoading, setHealthLoading] = useState(true);
 const [healthError, setHealthError] = useState(null);

 useEffect(() => {
 fetchApi('/api/v1/models')
 .then(setModels)
 .catch((err) => setModelsError(err.message))
 .finally(() => setModelsLoading(false));

 fetchApi('/api/health')
 .then(setHealth)
 .catch((err) => setHealthError(err.message))
 .finally(() => setHealthLoading(false));
 }, []);

 const modelList = Array.isArray(models) ? models : [];

 // Derive type styling
 const getTypeStyle = (type) => {
 const t = (type || '').toLowerCase();
 if (t === 'champion' || t === 'baseline') return { bg: 'bg-primary/20 border-primary/30', color: 'text-primary', shadow: 'shadow-[0_0_10px_rgba(236, 72, 153,0.3)]' };
 if (t === 'challenger') return { bg: 'bg-accent/20 border-accent/30', color: 'text-accent', shadow: 'shadow-[0_0_10px_rgba(236, 72, 153,0.3)]' };
 return { bg: 'bg-surface-container-highest border-outline-variant/30', color: 'text-on-surface-variant' };
 };

 const getStatusStyle = (status) => {
 const s = (status || '').toLowerCase();
 if (s === 'active') return { dot: 'bg-tertiary animate-pulse shadow-[0_0_8px_rgba(244, 114, 182,0.8)]', text: 'text-tertiary', bold: true };
 if (s === 'evaluation') return { dot: null, text: 'text-on-surface-variant font-medium', bold: false };
 return { dot: null, text: 'text-on-surface-variant font-medium', bold: false };
 };

 return (
 <motion.main 
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 transition={{ duration: 0.8 }}
 className="max-w-360 mx-auto px-8 py-10 space-y-12 relative z-10"
 >
 {/* Decorative blurs */}
 <div className="fixed top-20 right-20 w-[400px] h-[400px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
 <div className="fixed bottom-20 left-20 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />
 {/* Header Section */}
 <header className="space-y-2">
 <span className="font-label text-[10px] uppercase tracking-[0.2em] text-primary flex items-center gap-2 font-bold">
 <Network size={14} /> Workspace / Machine Learning
 </span>
 <h1 className="font-headline text-4xl font-semibold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-on-surface to-on-surface-variant">
 Model Registry / Lifecycle
 </h1>
 <p className="text-on-surface-variant max-w-2xl leading-relaxed py-2">
 Automated overview of all champion and challenger models actively managed by the system.
 Data ingestion and retraining pipelines are triggered automatically upon detected drift.
 </p>
 </header>

 {/* Training Panels: Asymmetric Grid */}
 <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 {/* Active Baseline Model */}
 <motion.div 
 initial={{ opacity: 0, y: 15 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.1 }}
 className="glass-panel rounded-2xl p-8 space-y-6 relative overflow-hidden group"
 >
 <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
 <div className="absolute top-8 right-8 opacity-10 group-hover:opacity-30 group-hover:scale-110 transition-all text-primary pointer-events-none">
 <Target size={120} strokeWidth={1} />
 </div>
 <div className="space-y-1 relative z-10">
 <h2 className="font-headline text-2xl font-bold text-on-surface flex items-center gap-2">
 Active Baseline Model
 </h2>
 <p className="text-sm text-on-surface-variant font-label tracking-widest uppercase mt-1">
 Establish the ground-truth performance metrics.
 </p>
 </div>
 <div className="space-y-4 relative z-10">
 {healthLoading ? (
 <div className="glass-panel border-outline-variant/10 rounded-xl p-4 border-l-4 border-l-outline animate-pulse">
 <p className="text-sm text-on-surface-variant">Loading model info...</p>
 </div>
 ) : healthError ? (
 <div className="bg-error/10 border-error/20 rounded-xl p-4 border-l-4 border-l-error">
 <p className="text-sm font-bold text-error">{healthError}</p>
 </div>
 ) : (
 <div className="glass-panel bg-surface-container/30 rounded-xl p-5 border-l-4 border-l-tertiary">
 <h3 className="text-sm font-bold mb-2 text-on-surface flex items-center gap-2">
 <Database size={16} className="text-tertiary" /> System Managed
 </h3>
 <p className="text-xs text-on-surface-variant leading-loose font-mono uppercase tracking-widest">
 Model loaded: <strong className="text-on-surface">{health?.model_loaded ? 'Yes' : 'No'}</strong> • 
 Features: <strong className="text-on-surface">{health?.features_count ?? '—'}</strong> • 
 Baseline: <strong className="text-on-surface">{health?.baseline_loaded ? 'Loaded' : 'Not loaded'}</strong>
 </p>
 </div>
 )}
 </div>
 </motion.div>

 {/* Standby Challenger Model */}
 <motion.div 
 initial={{ opacity: 0, y: 15 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.2 }}
 className="glass-panel rounded-2xl p-8 space-y-6 relative overflow-hidden group border border-accent/20 bg-accent/5 backdrop-blur-xl"
 >
 <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
 <div className="absolute top-8 right-8 opacity-10 group-hover:opacity-30 group-hover:-rotate-12 group-hover:scale-110 transition-all text-accent pointer-events-none">
 <FlaskConical size={120} strokeWidth={1} />
 </div>
 <div className="space-y-1 relative z-10">
 <h2 className="font-headline text-2xl font-bold text-on-surface flex items-center gap-2 ">
 Standby Challenger Model
 </h2>
 <p className="text-sm text-on-surface-variant font-label tracking-widest uppercase mt-1">
 Test experimental features against production logic.
 </p>
 </div>
 <div className="space-y-4 relative z-10">
 {healthLoading ? (
 <div className="glass-panel border-outline-variant/10 rounded-xl p-6 border border-outline-variant/20 flex flex-col items-center animate-pulse">
 <p className="text-sm text-on-surface-variant">Loading status...</p>
 </div>
 ) : healthError ? (
 <div className="bg-error/10 border-error/20 rounded-xl p-4 border-l-4 border-l-error">
 <p className="text-sm font-bold text-error">{healthError}</p>
 </div>
 ) : (
 <div className="glass-panel bg-surface-container/30 rounded-xl p-5 border-l-4 border-l-accent">
 <h3 className="text-sm font-bold mb-2 text-on-surface flex items-center gap-2">
 <Database size={16} className="text-accent" /> Challenger Status
 </h3>
 <p className="text-xs text-on-surface-variant leading-loose font-mono uppercase tracking-widest">
  Ready to switch when drift threshold exceeded
 </p>
 </div>
 )}
 </div>
 </motion.div>
 </section>

 {/* Model Registry Table Section */}
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.3 }}
 className="space-y-6"
 >
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
 <div className="space-y-1">
 <h3 className="font-headline text-2xl font-bold text-on-surface tracking-tight">Model Registry Table</h3>
 <p className="text-sm text-on-surface-variant">
 Version history and technical architecture of trained artifacts.
 </p>
 </div>
 <div className="flex gap-4">
 <div className="glass-panel px-4 py-2 rounded-xl flex items-center gap-2 focus-within:border-primary/50 transition-colors">
 <Search size={16} className="text-on-surface-variant" />
 <input
 className="bg-transparent border-none focus:ring-0 text-sm font-medium p-0 w-48 text-on-surface placeholder:text-outline"
 placeholder="Filter by ID..."
 type="text"
 />
 </div>
 </div>
 </div>

 {modelsLoading ? (
 <div className="glass-panel min-h-[300px] flex flex-col items-center justify-center rounded-2xl shadow-sm">
 <p className="text-on-surface-variant font-label text-sm animate-pulse">Loading models...</p>
 </div>
 ) : modelsError ? (
 <div className="glass-panel border-error/20 bg-error/5 min-h-[300px] flex flex-col items-center justify-center gap-2 rounded-2xl shadow-sm">
 <CloudOff size={32} className="text-error" />
 <p className="text-error font-headline font-bold">{modelsError}</p>
 <p className="text-on-surface-variant text-sm">Required to display model registry.</p>
 </div>
 ) : modelList.length === 0 ? (
 <div className="glass-panel min-h-[300px] flex flex-col items-center justify-center gap-2 rounded-2xl shadow-sm">
 <Boxes size={32} className="text-on-surface-variant/50" />
 <p className="text-on-surface-variant font-medium">No models registered yet.</p>
 </div>
 ) : (
 <div className="glass-panel rounded-2xl shadow-sm overflow-hidden border border-outline-variant/20">
 <table className="w-full text-left border-collapse">
 <thead className="bg-surface-container-high/50 border-b border-surface-container">
 <tr>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Model ID</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Version</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Training Date</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Type</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Status</th>
 <th className="px-6 py-4 font-label text-[11px] font-bold text-outline uppercase tracking-[0.2em]">Metrics</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-surface-container/50">
 {modelList.map((model, i) => {
 const typeStyle = getTypeStyle(model.type);
 const statusStyle = getStatusStyle(model.status);
 return (
 <motion.tr 
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: 0.1 * Math.min(i, 10) }}
 key={model.model_id} 
 className="hover:bg-primary/5 transition-colors group cursor-default"
 >
 <td className="px-6 py-5">
 <span className="font-headline font-bold text-on-surface group-hover:text-primary transition-colors">{model.model_id}</span>
 </td>
 <td className="px-6 py-5 text-sm font-semibold text-on-surface font-mono">{model.version ?? '—'}</td>
 <td className="px-6 py-5 text-sm text-on-surface-variant font-mono">{model.training_date ?? '—'}</td>
 <td className="px-6 py-5">
 <span className={`${typeStyle.bg} ${typeStyle.color} ${typeStyle.shadow} border px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider`}>
 {model.type ?? '—'}
 </span>
 </td>
 <td className="px-6 py-5">
 {statusStyle.dot ? (
 <div className={`flex items-center gap-2 ${statusStyle.text}`}>
 <span className={`w-2 h-2 rounded-full ${statusStyle.dot}`}></span>
 <span className="text-xs font-bold uppercase tracking-wider">{model.status}</span>
 </div>
 ) : (
 <span className={`text-xs uppercase tracking-wider ${statusStyle.text}`}>{model.status ?? '—'}</span>
 )}
 </td>
 <td className="px-6 py-5 text-sm font-mono text-outline-variant font-bold leading-relaxed">
 {model.metrics ? (
 <div className="flex items-center gap-3">
 {model.metrics.auc != null && <span className="group-hover:text-on-surface transition-colors">AUC: <span className="text-primary">{model.metrics.auc}</span></span>}
 {model.metrics.precision != null && <span className="group-hover:text-on-surface transition-colors">P: <span className="text-tertiary">{model.metrics.precision}</span></span>}
 {model.metrics.recall != null && <span className="group-hover:text-on-surface transition-colors">R: <span className="text-accent">{model.metrics.recall}</span></span>}
 </div>
 ) : '—'}
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
