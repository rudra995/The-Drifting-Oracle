import { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
 import { 
  CloudUpload, TableProperties, ShieldCheck, Activity, ArrowRightLeft, 
  BrainCircuit, Zap, CheckCircle2, FileText, Info, PieChart, 
  ListOrdered, AlertTriangle, CheckCircle, Database, Brain
} from 'lucide-react';
import { fetchApi } from '../api';

/* ── Loading pipeline steps shown during inference ── */
const LOADING_STEPS = [
 { icon: CloudUpload, label: 'Uploading dataset…', duration: 800 },
 { icon: TableProperties, label: 'Parsing CSV columns…', duration: 900 },
 { icon: ShieldCheck, label: 'Validating schema integrity…', duration: 700 },
 { icon: Activity, label: 'Computing multi-feature PSI…', duration: 1000 },
 { icon: ArrowRightLeft, label: 'Evaluating model switch criteria…', duration: 800 },
 { icon: BrainCircuit, label: 'Loading selected model weights…', duration: 900 },
 { icon: Zap, label: 'Running batch predict_proba…', duration: 1200 },
 { icon: CheckCircle2, label: 'Finalizing risk labels…', duration: 700 },
];

export default function UploadPage() {
 const [csvFile, setCsvFile] = useState(null);
 const [uploading, setUploading] = useState(false);
 const [uploadError, setUploadError] = useState(null);
 const [uploadResult, setUploadResult] = useState(null);
 const [dragActive, setDragActive] = useState(false);
 const fileInputRef = useRef(null);
 const resultsRef = useRef(null);

 // Loading animation state
 const [loadingPhase, setLoadingPhase] = useState(-1);
 const [loadingProgress, setLoadingProgress] = useState(0);

 // Auto-scroll to results when they appear
 useEffect(() => {
 if (uploadResult && !uploading && resultsRef.current) {
 const timer = setTimeout(() => {
 resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
 }, 150);
 return () => clearTimeout(timer);
 }
 }, [uploadResult, uploading]);

 // Run the step-by-step loading animation
 const runLoadingAnimation = useCallback(() => {
 return new Promise((resolve) => {
 let currentStep = 0;
 const totalSteps = LOADING_STEPS.length;

 const advanceStep = () => {
 if (currentStep >= totalSteps) {
 resolve();
 return;
 }
 setLoadingPhase(currentStep);
 setLoadingProgress(Math.round(((currentStep + 1) / totalSteps) * 100));

 setTimeout(() => {
 currentStep++;
 advanceStep();
 }, LOADING_STEPS[currentStep].duration);
 };

 advanceStep();
 });
 }, []);

 const handleFileChange = (event) => {
 const file = event.target.files?.[0] ?? null;
 setUploadError(null);
 setUploadResult(null);

 if (!file) {
 setCsvFile(null);
 return;
 }

 if (!file.name.toLowerCase().endsWith('.csv')) {
 setCsvFile(null);
 setUploadError('Please select a valid .csv file.');
 return;
 }

 setCsvFile(file);
 };

 const handleDrag = (e) => {
 e.preventDefault();
 e.stopPropagation();
 if (e.type === 'dragenter' || e.type === 'dragover') {
 setDragActive(true);
 } else if (e.type === 'dragleave') {
 setDragActive(false);
 }
 };

 const handleDrop = (e) => {
 e.preventDefault();
 e.stopPropagation();
 setDragActive(false);
 setUploadError(null);
 setUploadResult(null);

 const file = e.dataTransfer.files?.[0];
 if (!file) return;

 if (!file.name.toLowerCase().endsWith('.csv')) {
 setUploadError('Please drop a valid .csv file.');
 return;
 }

 setCsvFile(file);
 };

 const handleCsvUpload = async (event) => {
 event.preventDefault();

 if (!csvFile) {
 setUploadError('Choose a CSV file before uploading.');
 return;
 }

 setUploading(true);
 setUploadError(null);
 setUploadResult(null);
 setLoadingPhase(0);
 setLoadingProgress(0);

 try {
 const formData = new FormData();
 formData.append('file', csvFile);

 const [result] = await Promise.all([
 fetchApi('/predict_batch', {
 method: 'POST',
 body: formData,
 }),
 runLoadingAnimation(),
 ]);

 if (result?.status !== 'success') {
 throw new Error(result?.error || 'Batch prediction failed.');
 }

 await new Promise((r) => setTimeout(r, 400));
 setUploadResult(result);
 } catch (err) {
 setUploadError(err.message || 'Upload failed.');
 } finally {
 setUploading(false);
 setLoadingPhase(-1);
 setLoadingProgress(0);
 }
 };

 const clearFile = () => {
 setCsvFile(null);
 setUploadError(null);
 setUploadResult(null);
 if (fileInputRef.current) fileInputRef.current.value = '';
 };

 const formatFileSize = (bytes) => {
 if (bytes < 1024) return `${bytes} B`;
 if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
 return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
 };

 const currentStep = loadingPhase >= 0 ? LOADING_STEPS[loadingPhase] : null;

 // Predictions table: show first N rows
 const [showAllPredictions, setShowAllPredictions] = useState(false);
 const visiblePredictions = uploadResult?.predictions
 ? showAllPredictions
 ? uploadResult.predictions
 : uploadResult.predictions.slice(0, 20)
 : [];

 return (
 <main className="max-w-360 mx-auto px-8 py-10 space-y-10 relative z-10">
 {/* Header */}
 <motion.header 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5 }}
 className="space-y-2"
 >
 <span className="font-label text-[10px] uppercase tracking-[0.2em] text-accent font-bold">
 Workspace / Inference
 </span>
 <h1 className="font-headline text-4xl font-semibold text-on-surface tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-on-surface to-on-surface-variant">
 Upload &amp; Predict
 </h1>
 <p className="text-on-surface-variant max-w-2xl leading-relaxed text-sm">
 Upload a CSV file with applicant data to generate batch predictions. The system
 computes multi-feature PSI drift scores and automatically selects the best model.
 </p>
 </motion.header>

 {/* ─── LOADING OVERLAY ─── */}
 {uploading && currentStep && (
 <section className="bg-surface-container-low rounded-xl border border-outline-variant/20 shadow-lg overflow-hidden">
 <div className="h-1.5 bg-surface-container-highest">
 <div
 className="h-full bg-linear-to-r from-primary via-tertiary to-primary rounded-r-full transition-all duration-700 ease-out"
 style={{ width: `${loadingProgress}%` }}
 />
 </div>

 <div className="p-10 flex flex-col items-center gap-8">
 <div className="relative">
 <div className="w-20 h-20 rounded-3xl bg-primary-container flex items-center justify-center animate-[pulse_2s_cubic-bezier(0.4,0,0.6,1)_infinite] border border-primary/20 shadow-[0_0_30px_rgba(99,102,241,0.3)]">
 {currentStep && <currentStep.icon className="text-primary w-10 h-10" />}
 </div>
 <div className="absolute -inset-2 border-2 border-primary/20 border-t-accent rounded-full animate-spin" />
 </div>

 <div className="text-center space-y-2">
 <p className="font-headline text-xl font-bold text-on-surface transition-all duration-300" key={loadingPhase}>
 {currentStep.label}
 </p>
 <p className="text-sm text-on-surface-variant">
 Step {loadingPhase + 1} of {LOADING_STEPS.length}
 </p>
 </div>

 <div className="flex items-center gap-2">
 {LOADING_STEPS.map((_, i) => (
 <div
 key={i}
 className={`h-2 rounded-full transition-all duration-500 ${
 i < loadingPhase ? 'w-2 bg-tertiary' : i === loadingPhase ? 'w-8 bg-primary' : 'w-2 bg-outline-variant/30'
 }`}
 />
 ))}
 </div>

 <div className="w-full max-w-md space-y-1.5">
 {LOADING_STEPS.slice(0, loadingPhase + 1).map((step, i) => (
 <motion.div 
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 key={i} 
 className={`flex items-center gap-2.5 text-sm py-1 transition-all duration-300 ${i < loadingPhase ? 'opacity-50' : 'opacity-100'}`}
 >
 {i < loadingPhase ? <CheckCircle2 className="w-4 h-4 text-accent" /> : <div className="w-4 h-4 border-2 border-primary rounded-full border-t-transparent animate-spin" />}
 <span className={i < loadingPhase ? 'text-on-surface-variant line-through' : 'text-on-surface font-semibold'}>
 {step.label}
 </span>
 </motion.div>
 ))}
 </div>

 <p className="text-xs text-outline font-label">
 Processing <strong>{csvFile?.name}</strong> • {loadingProgress}% complete
 </p>
 </div>
 </section>
 )}

 {/* ─── UPLOAD SECTION (hidden during loading) ─── */}
 {!uploading && (
 <motion.section 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.1 }}
 className="grid grid-cols-1 lg:grid-cols-5 gap-8"
 >
 <div className="lg:col-span-3 space-y-6">
 <div className="glass-panel rounded-2xl p-8 space-y-6 relative overflow-hidden">
 <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
 <div className="space-y-1 relative z-10">
 <h2 className="font-headline text-2xl font-bold text-on-surface">Batch CSV Inference</h2>
 <p className="text-sm text-on-surface-variant">
 Upload a CSV to run drift-aware predictions. The system computes PSI across 7 features and selects the best model automatically.
 </p>
 </div>

 <form onSubmit={handleCsvUpload} className="space-y-4">
 <div
 onDragEnter={handleDrag}
 onDragLeave={handleDrag}
 onDragOver={handleDrag}
 onDrop={handleDrop}
 onClick={() => fileInputRef.current?.click()}
 className={`relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 cursor-pointer transition-all duration-300 ${
 dragActive
 ? 'border-tertiary bg-tertiary/5 scale-[1.01]'
 : csvFile
 ? 'border-tertiary/40 bg-tertiary/5'
 : 'border-outline-variant/30 bg-surface-container-highest/50 hover:border-primary/40 hover:bg-primary/5'
 }`}
 >
 <input ref={fileInputRef} id="batch-csv" type="file" accept=".csv,text/csv" onChange={handleFileChange} className="hidden" />

 {csvFile ? (
 <>
 <div className="w-14 h-14 rounded-2xl bg-accent-container flex items-center justify-center">
 <FileText className="w-7 h-7 text-accent" />
 </div>
 <div className="text-center">
 <p className="font-headline font-bold text-on-surface">{csvFile.name}</p>
 <p className="text-xs text-on-surface-variant mt-1">{formatFileSize(csvFile.size)} • CSV file ready</p>
 </div>
 <button type="button" onClick={(e) => { e.stopPropagation(); clearFile(); }} className="text-xs font-bold text-error hover:underline mt-1">Remove file</button>
 </>
 ) : (
 <>
 <div className="w-14 h-14 rounded-2xl bg-surface-container-high border border-outline-variant/50 flex items-center justify-center">
 <CloudUpload className="w-7 h-7 text-on-surface-variant group-hover:text-primary transition-colors" />
 </div>
 <div className="text-center">
 <p className="font-headline font-semibold text-on-surface">Drag &amp; drop your CSV here</p>
 <p className="text-xs text-on-surface-variant mt-1.5">or <span className="text-primary font-bold">click to browse</span> • Only .csv files</p>
 </div>
 </>
 )}
 </div>

 <div className="flex items-center gap-3">
 <button type="submit" disabled={!csvFile} className="h-12 rounded-xl oracle-glow px-8 text-sm font-bold uppercase tracking-widest text-on-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:filter-none transition-all duration-200 flex items-center gap-2">
 <Zap className="w-5 h-5 fill-current" />
 Upload &amp; Predict
 </button>
 {csvFile && <span className="text-xs text-on-surface-variant">Ready to process <strong>{csvFile.name}</strong></span>}
 </div>
 </form>

 {uploadError && (
 <div className="rounded-lg border-l-4 border-error bg-error/10 px-5 py-4 flex items-start gap-3">
 <span className="material-symbols-outlined text-error text-xl mt-0.5">error</span>
 <div>
 <p className="text-sm font-bold text-error">Upload Failed</p>
 <p className="text-sm text-error/80 mt-0.5">{uploadError}</p>
 </div>
 </div>
 )}
 </div>
 </div>

 {/* Instructions Panel */}
 <div className="lg:col-span-2 space-y-6">
 <div className="glass-panel rounded-2xl p-8 space-y-5">
 <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
 <Info size={20} className="text-primary" />
 Pipeline Flow
 </h3>
 <ol className="space-y-4 text-sm text-on-surface-variant">
 {[
 { Icon: CloudUpload, title: 'Upload CSV', desc: 'Upload raw applicant data — engineered features are computed server-side.' },
 { Icon: Activity, title: 'PSI Drift Detection', desc: 'Incoming data vs training baseline across 7 numeric features.' },
 { Icon: ArrowRightLeft, title: 'Model Selection', desc: 'PSI < 0.25 → Champion | PSI ≥ 0.25 → Challenger' },
 { Icon: BrainCircuit, title: 'predict_proba', desc: 'Probability scores + risk labels: Low / Medium / High' },
 ].map((step, i) => (
 <li key={i} className="flex gap-3">
 <div className="w-9 h-9 rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-center justify-center shrink-0 mt-0.5">
 <step.Icon size={18} className="text-primary" />
 </div>
 <div>
 <p className="font-bold text-on-surface text-sm">{step.title}</p>
 <p className="text-xs leading-relaxed mt-0.5">{step.desc}</p>
 </div>
 </li>
 ))}
 </ol>
 </div>

 <div className="glass-panel rounded-2xl p-8 space-y-3">
 <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
 <TableProperties size={20} className="text-accent" />
 Input Columns
 </h3>
 <div className="flex flex-wrap gap-2">
 {['AMT_INCOME_TOTAL', 'AMT_CREDIT_x', 'AMT_ANNUITY', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS', 'DAYS_EMPLOYED', 'EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3', 'REGION_POPULATION_RELATIVE'].map((col) => (
 <span key={col} className="bg-surface-container-highest px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold text-on-surface-variant">{col}</span>
 ))}
 </div>
 <p className="text-xs text-on-surface-variant mt-2">
 Engineered features (income_credit_ratio, annuity_ratio, age) are computed automatically.
 </p>
 </div>
 </div>
 </motion.section>
 )}

 {/* ─── RESULTS SECTION ─── */}
 {uploadResult && !uploading && (
 <motion.section 
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.6, delay: 0.1, staggerChildren: 0.1 }}
 ref={resultsRef} 
 className="space-y-6 scroll-mt-6"
 >
 {/* Success Banner */}
 <motion.div 
 initial={{ opacity: 0, scale: 0.95 }}
 animate={{ opacity: 1, scale: 1 }}
 className={`glass-panel rounded-2xl px-6 py-4 flex items-center gap-4 ${
 uploadResult.drift_detected
 ? 'bg-error/5 border-error/20'
 : 'bg-tertiary/5 border-tertiary/20'
 }`}>
 <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border ${
 uploadResult.drift_detected ? 'bg-error/10 border-error/20' : 'bg-primary/10 border-primary/20'
 }`}>
 {uploadResult.drift_detected ? (
 <AlertTriangle className="text-error" />
 ) : (
 <CheckCircle className="text-primary" />
 )}
 </div>
 <div>
 <p className="font-headline font-bold text-on-surface">
 {uploadResult.drift_detected ? 'Drift Detected — Model Switched' : 'Prediction Complete'}
 </p>
 <p className="text-sm text-on-surface-variant">
 {uploadResult.total_rows} rows processed using <strong>{uploadResult.model_used}</strong> model
 {uploadResult.drift_detected && <span className="text-error font-bold"> • PSI = {uploadResult.psi}</span>}
 </p>
 </div>
 </motion.div>

 {/* Summary KPI Cards */}
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.2 }}
 className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
 >
 {[
 { label: 'Total Rows', value: uploadResult.total_rows ?? '—', Icon: Database, color: 'text-primary', bg: 'bg-primary-container/30 border-primary/20' },
 { label: 'Avg Probability', value: uploadResult.avg_probability ?? '—', Icon: PieChart, color: 'text-secondary', bg: 'bg-secondary-container/30 border-secondary/20' },
 { label: 'PSI Score', value: uploadResult.psi ?? '—', Icon: Activity, color: uploadResult.drift_detected ? 'text-error' : 'text-accent', bg: uploadResult.drift_detected ? 'bg-error-container/20 border-error/20' : 'bg-accent-container/20 border-accent/20' },
 { label: 'Model Used', value: uploadResult.model_used ?? '—', Icon: BrainCircuit, color: 'text-primary', bg: 'bg-primary-container/30 border-primary/20' },
 ].map((card) => (
 <motion.div 
 whileHover={{ y: -4 }}
 key={card.label} 
 className="glass-panel rounded-2xl p-6 flex items-start gap-4 overflow-hidden relative group"
 >
 {/* Subtle background glow on hover */}
 <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
 
 <div className={`w-12 h-12 rounded-xl ${card.bg} border flex items-center justify-center shrink-0 z-10`}>
 <card.Icon className={card.color} size={22} />
 </div>
 <div className="z-10">
 <p className="text-xs font-bold uppercase tracking-widest text-outline">{card.label}</p>
 <p className="font-headline text-2xl font-bold text-on-surface mt-1">{card.value}</p>
 </div>
 </motion.div>
 ))}
 </motion.div>

 {/* AI Assessment Card */}
 {uploadResult.explanation && (
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.25 }}
 className="glass-panel rounded-2xl p-8 bg-primary-container/20 border-l-4 border-primary"
 >
 <div className="flex items-start gap-4">
 <Brain className="text-primary w-6 h-6 mt-1 shrink-0" />
 <div className="flex-1">
 <h3 className="font-headline font-bold text-on-surface mb-2 flex items-center gap-2">
 Batch AI Assessment
 {uploadResult.explanation_llm && (
 <span className="text-xs px-2 py-1 bg-primary/10 border border-primary/20 rounded-full text-primary font-mono">
 {uploadResult.explanation_llm}
 </span>
 )}
 </h3>
 <p className="text-on-surface leading-relaxed italic">
 "{uploadResult.explanation}"
 </p>
 </div>
 </div>
 </motion.div>
 )}

 {/* Per-Feature PSI Breakdown + Risk Distribution */}
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.3 }}
 className="grid grid-cols-1 lg:grid-cols-2 gap-6"
 >
 {/* PSI Per Feature */}
 {uploadResult.psi_per_feature && Object.keys(uploadResult.psi_per_feature).length > 0 && (
 <div className="glass-panel rounded-2xl p-8 space-y-4">
 <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
 <Activity className="text-primary w-5 h-5" />
 PSI Per Feature
 </h3>
 <div className="space-y-3">
 {Object.entries(uploadResult.psi_per_feature).map(([feat, score]) => (
 <div key={feat} className="space-y-1">
 <div className="flex justify-between text-sm">
 <span className="font-mono text-on-surface-variant">{feat}</span>
 <span className={`font-bold font-mono ${score >= 0.25 ? 'text-error' : score >= 0.1 ? 'text-yellow-600' : 'text-tertiary'}`}>{score}</span>
 </div>
 <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
 <div
 className={`h-full rounded-full transition-all duration-500 ${score >= 0.25 ? 'bg-error' : score >= 0.1 ? 'bg-yellow-500' : 'bg-tertiary'}`}
 style={{ width: `${Math.min(score / 0.5 * 100, 100)}%` }}
 />
 </div>
 </div>
 ))}
 </div>
 <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-wider text-outline pt-2 border-t border-outline-variant/10">
 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-tertiary" />Stable (&lt;0.1)</span>
 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />Warning (0.1-0.25)</span>
 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-error" />Drift (≥0.25)</span>
 </div>
 </div>
 )}

 {/* Risk Distribution */}
 {uploadResult.risk_distribution && (
 <div className="glass-panel rounded-2xl p-8 space-y-4">
 <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
 <PieChart className="text-primary w-5 h-5" />
 Risk Distribution
 </h3>
 <div className="grid grid-cols-3 gap-4">
 {[
 { label: 'Low', count: uploadResult.risk_distribution.Low ?? 0, color: 'text-accent', bg: 'bg-accent/10', ring: 'border-accent/40' },
 { label: 'Medium', count: uploadResult.risk_distribution.Medium ?? 0, color: 'text-yellow-500', bg: 'bg-yellow-500/10', ring: 'border-yellow-500/40' },
 { label: 'High', count: uploadResult.risk_distribution.High ?? 0, color: 'text-error', bg: 'bg-error/10', ring: 'border-error/40' },
 ].map((risk) => {
 const total = uploadResult.total_rows || 1;
 const pct = Math.round((risk.count / total) * 100);
 return (
 <div key={risk.label} className={`${risk.bg} rounded-xl p-5 text-center border-l-4 ${risk.ring}`}>
 <p className={`font-headline text-3xl font-bold ${risk.color}`}>{risk.count}</p>
 <p className="text-xs font-bold uppercase tracking-wider text-outline mt-1">{risk.label} Risk</p>
 <p className="text-xs text-on-surface-variant mt-0.5">{pct}%</p>
 </div>
 );
 })}
 </div>

 {/* Summary details */}
 <div className="space-y-2 text-sm pt-3 border-t border-outline-variant/10">
 {[
 ['Decision', uploadResult.decision],
 ['Default Rate', uploadResult.default_rate],
 ['Drift Detected', uploadResult.drift_detected ? 'Yes' : 'No'],
 ].map(([label, value]) => (
 <div key={label} className="flex justify-between py-1">
 <span className="text-on-surface-variant">{label}</span>
 <span className="font-bold text-on-surface font-mono">{value ?? '—'}</span>
 </div>
 ))}
 </div>
 </div>
 )}
 </motion.div>

 {/* System Message */}
 {uploadResult.message && (
 <motion.div 
 initial={{ opacity: 0, y: 10 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.4 }}
 className="bg-primary-container/20 rounded-xl p-4 border-l-4 border-primary shadow-sm"
 >
 <p className="text-sm text-on-surface leading-relaxed flex items-start gap-2">
 <Info size={18} className="text-primary mt-0.5 shrink-0" />
 <span><strong className="text-primary">System:</strong> {uploadResult.message}</span>
 </p>
 </motion.div>
 )}

 {/* Predictions Table */}
 {uploadResult.predictions && uploadResult.predictions.length > 0 && (
 <motion.div 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.5 }}
 className="glass-panel rounded-2xl overflow-hidden"
 >
 <div className="px-8 py-5 border-b border-outline-variant/10 flex items-center justify-between">
 <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
 <ListOrdered className="text-primary w-5 h-5" />
 Per-Row Predictions
 </h3>
 <span className="text-xs text-on-surface-variant">
 Showing {visiblePredictions.length} of {uploadResult.predictions.length} rows
 </span>
 </div>

 <div className="overflow-x-auto">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-surface-container-highest/50">
 <th className="px-6 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-outline">ID</th>
 <th className="px-6 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-outline">Probability</th>
 <th className="px-6 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-outline">Risk Label</th>
 <th className="px-6 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-outline">Decision</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-outline-variant/10">
 {visiblePredictions.map((pred) => (
 <tr key={pred.id} className="hover:bg-surface-container/50 transition-colors">
 <td className="px-6 py-3 font-mono font-bold text-on-surface">{pred.id}</td>
 <td className="px-6 py-3 font-mono text-on-surface">
 <div className="flex items-center gap-2">
 <div className="w-16 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
 <div
 className={`h-full rounded-full ${pred.probability >= 0.7 ? 'bg-error' : pred.probability >= 0.3 ? 'bg-yellow-500' : 'bg-tertiary'}`}
 style={{ width: `${pred.probability * 100}%` }}
 />
 </div>
 {pred.probability}
 </div>
 </td>
 <td className="px-6 py-3">
 <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
 pred.risk_label === 'Low' ? 'bg-accent/10 border border-accent/20 text-accent' :
 pred.risk_label === 'Medium' ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-500' :
 'bg-error/10 border border-error/20 text-error'
 }`}>
 {pred.risk_label}
 </span>
 </td>
 <td className="px-6 py-3 text-on-surface-variant">
 {pred.probability >= 0.5 ? 'Reject' : 'Accept'}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {uploadResult.predictions.length > 20 && (
 <div className="px-8 py-4 border-t border-outline-variant/10 text-center">
 <button
 onClick={() => setShowAllPredictions(!showAllPredictions)}
 className="text-sm font-bold text-primary hover:underline"
 >
 {showAllPredictions
 ? `Show first 20 rows`
 : `Show all ${uploadResult.predictions.length} rows`
 }
 </button>
 </div>
 )}
 </motion.div>
 )}
 </motion.section>
 )}
 </main>
 );
}
