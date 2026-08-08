import { useState } from 'react';
import { motion } from 'framer-motion';

export default function SettingsPage() {
 const [emailAlerts, setEmailAlerts] = useState(true);
 const [driftAlerts, setDriftAlerts] = useState(true);
 const [weeklySummary, setWeeklySummary] = useState(false);

 return (
 <motion.main 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5 }}
 className="p-8 max-w-400 mx-auto space-y-8 relative z-10"
 >
 {/* Decorative blurs */}
 <div className="fixed top-20 right-20 w-[300px] h-[300px] bg-accent/10 rounded-full blur-[80px] pointer-events-none" />

 <section className="rounded-2xl glass-panel p-6 md:p-8">
 <h1 className="text-3xl font-headline font-bold tracking-tight text-on-surface">Settings</h1>
 <p className="mt-2 text-on-surface-variant">Manage notifications, dashboard behavior, and preferences.</p>
 </section>

 <section className="rounded-2xl glass-panel p-6 md:p-8 space-y-6">
 <div className="flex items-start justify-between gap-6">
 <div>
 <h2 className="text-lg font-headline font-semibold text-on-surface">Email Alerts</h2>
 <p className="text-sm text-on-surface-variant mt-1">Receive alerts when uploads complete and reports are generated.</p>
 </div>
 <button
 type="button"
 onClick={() => setEmailAlerts((prev) => !prev)}
 className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface ${emailAlerts ? 'bg-primary shadow-[0_0_8px_rgba(236, 72, 153,0.5)]' : 'bg-surface-container-highest border border-outline/30'}`}
 aria-label="Toggle email alerts"
 >
 <span
 className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${emailAlerts ? 'translate-x-6' : 'translate-x-1'}`}
 />
 </button>
 </div>

 <div className="flex items-start justify-between gap-6">
 <div>
 <h2 className="text-lg font-headline font-semibold text-on-surface">Drift Detection Alerts</h2>
 <p className="text-sm text-on-surface-variant mt-1">Notify when PSI or feature drift crosses configured thresholds.</p>
 </div>
 <button
 type="button"
 onClick={() => setDriftAlerts((prev) => !prev)}
 className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface ${driftAlerts ? 'bg-primary shadow-[0_0_8px_rgba(236, 72, 153,0.5)]' : 'bg-surface-container-highest border border-outline/30'}`}
 aria-label="Toggle drift alerts"
 >
 <span
 className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${driftAlerts ? 'translate-x-6' : 'translate-x-1'}`}
 />
 </button>
 </div>

 <div className="flex items-start justify-between gap-6">
 <div>
 <h2 className="text-lg font-headline font-semibold text-on-surface">Weekly Summary</h2>
 <p className="text-sm text-on-surface-variant mt-1">Get a weekly snapshot of model health, drift, and governance events.</p>
 </div>
 <button
 type="button"
 onClick={() => setWeeklySummary((prev) => !prev)}
 className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface ${weeklySummary ? 'bg-primary shadow-[0_0_8px_rgba(236, 72, 153,0.5)]' : 'bg-surface-container-highest border border-outline/30'}`}
 aria-label="Toggle weekly summary"
 >
 <span
 className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${weeklySummary ? 'translate-x-6' : 'translate-x-1'}`}
 />
 </button>
 </div>
 </section>

 <section className="rounded-2xl glass-panel p-6 md:p-8">
 <h2 className="text-lg font-headline font-semibold text-on-surface mb-2">Profile</h2>
 <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
 <div>
 <label className="text-[10px] uppercase font-bold tracking-widest text-outline">Display Name</label>
 <input
 className="mt-2 w-full rounded-xl bg-surface-container/30 px-4 py-3 text-sm font-medium text-on-surface border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
 defaultValue="Oracle Operator"
 />
 </div>
 <div>
 <label className="text-[10px] uppercase font-bold tracking-widest text-outline">Email</label>
 <input
 className="mt-2 w-full rounded-xl bg-surface-container/30 px-4 py-3 text-sm font-medium text-on-surface border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
 defaultValue="operator@driftingoracle.ai"
 />
 </div>
 </div>

 <div className="mt-8 flex gap-4">
 <button type="button" className="px-6 py-2.5 rounded-xl bg-primary text-on-primary font-bold shadow-[0_0_15px_rgba(236, 72, 153,0.4)] hover:shadow-[0_0_20px_rgba(236, 72, 153,0.6)] hover:bg-primary-light transition-all text-sm uppercase tracking-wider">
 Save Changes
 </button>
 <button
 type="button"
 className="px-6 py-2.5 rounded-xl glass-panel text-on-surface-variant hover:text-on-surface transition-colors font-bold text-sm uppercase tracking-wider"
 >
 Reset
 </button>
 </div>
 </section>
 </motion.main>
 );
}