import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Zap, FileText } from 'lucide-react';
import { fetchApi } from '../api';

export default function SystemOverview() {
 const [health, setHealth] = useState(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState(null);

 useEffect(() => {
 fetchApi('/api/health')
 .then(setHealth)
 .catch((err) => setError(err.message))
 .finally(() => setLoading(false));
 }, []);

 const statusText = loading
 ? 'Loading system status...'
 : error
 ? error
 : health
 ? `Status: ${health.status === 'healthy' ? 'Healthy' : health.status} • Model loaded: ${health.model_loaded ? 'Yes' : 'No'} • Features: ${health.features_count} • Window: ${health.window_size}`
 : 'Unable to fetch system status';

 return (
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4"
 >
 <div>
 <h1 className="font-headline text-4xl font-semibold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent ">
 System Overview
 </h1>
 <p className="text-secondary font-label text-xs uppercase tracking-[0.1em] mt-1">
 {statusText}
 </p>
 </div>
 <div className="flex gap-3">
 <button className="bg-surface-container-high border border-outline-variant/30 text-on-surface px-4 py-2 rounded-xl font-label text-sm font-semibold hover:bg-surface-container-highest transition-all flex items-center gap-2">
 <FileText size={16} className="text-on-surface-variant" />
 Generate Report
 </button>
 <button className="oracle-glow text-white px-6 py-2 rounded-xl font-label text-sm font-semibold hover:shadow-lg hover:shadow-primary/20 active:scale-95 transition-all flex items-center gap-2">
 <Zap size={16} />
 Manual Retrain
 </button>
 </div>
 </motion.section>
 );
}
