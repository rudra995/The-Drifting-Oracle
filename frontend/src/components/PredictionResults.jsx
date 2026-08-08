import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, TrendingUp, Zap, Brain, Activity } from 'lucide-react';

export default function PredictionResults({ result }) {
  if (!result) return null;

  const isApproved = result.decision === 'Accept Loan';

  return (
    <motion.section
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-6"
    >
      {/* Main Decision Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className={`glass-panel rounded-2xl p-8 border-l-4 ${
          isApproved
            ? 'bg-tertiary/10 border-tertiary'
            : 'bg-error/10 border-error'
        }`}
      >
        <div className="flex items-center gap-6">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
            isApproved
              ? 'bg-tertiary/20'
              : 'bg-error/20'
          }`}>
            {isApproved ? (
              <CheckCircle className="text-tertiary w-8 h-8" />
            ) : (
              <AlertTriangle className="text-error w-8 h-8" />
            )}
          </div>
          <div className="flex-1">
            <h2 className={`font-headline text-3xl font-bold ${
              isApproved ? 'text-tertiary' : 'text-error'
            }`}>
              {result.decision}
            </h2>
            <p className="text-on-surface-variant mt-1">
              Loan application assessment completed
            </p>
          </div>
        </div>
      </motion.div>

      {/* AI Summary Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-panel rounded-2xl p-8 bg-primary-container/20 border-l-4 border-primary"
      >
        <div className="flex items-start gap-4">
          <Brain className="text-primary w-6 h-6 mt-1 shrink-0" />
          <div className="flex-1">
            <h3 className="font-headline font-bold text-on-surface mb-2 flex items-center gap-2">
              AI Assessment
              <span className="text-xs px-2 py-1 bg-primary/10 border border-primary/20 rounded-full text-primary font-mono">
                {result.explanation_llm}
              </span>
            </h3>
            <p className="text-on-surface leading-relaxed italic">
              &ldquo;{result.explanation}&rdquo;
            </p>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Probability */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-primary w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-widest text-outline">
              Default Probability
            </span>
          </div>
          <div>
            <p className="font-headline text-3xl font-bold text-on-surface">
              {(result.probability * 100).toFixed(1)}%
            </p>
            <div className="mt-2 h-2 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  result.probability >= 0.7
                    ? 'bg-error'
                    : result.probability >= 0.3
                    ? 'bg-yellow-500'
                    : 'bg-tertiary'
                }`}
                style={{ width: `${result.probability * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Risk Label */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-primary w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-widest text-outline">
              Risk Classification
            </span>
          </div>
          <div>
            <span className={`inline-block px-4 py-2 rounded-lg font-bold text-sm ${
              result.risk_label === 'Low'
                ? 'bg-accent/10 border border-accent/20 text-accent'
                : result.risk_label === 'Medium'
                ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-500'
                : 'bg-error/10 border border-error/20 text-error'
            }`}>
              {result.risk_label} Risk
            </span>
          </div>
        </div>

        {/* PSI Score */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Activity className="text-primary w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-widest text-outline">
              Population Stability
            </span>
          </div>
          <div>
            <p className="font-headline text-3xl font-bold text-on-surface">
              {result.psi.toFixed(4)}
            </p>
            <p className={`text-xs font-bold mt-2 ${
              result.drift_detected ? 'text-error' : 'text-tertiary'
            }`}>
              {result.drift_detected ? '⚠️ Drift Detected' : '✓ Stable'}
            </p>
          </div>
        </div>

        {/* Model Used */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="text-primary w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-widest text-outline">
              Model Selection
            </span>
          </div>
          <div>
            <span className={`inline-block px-3 py-2 rounded-lg font-bold text-sm ${
              result.model_used === 'Champion'
                ? 'bg-primary/10 border border-primary/20 text-primary'
                : 'bg-secondary/10 border border-secondary/20 text-secondary'
            }`}>
              {result.model_used}
            </span>
            <p className="text-xs text-on-surface-variant mt-2">
              {result.drift_detected && result.model_used === 'Challenger'
                ? 'Challenger model activated due to drift'
                : 'Primary model in use'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* PSI Per Feature Breakdown */}
      {result.psi_per_feature && Object.keys(result.psi_per_feature).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-panel rounded-2xl p-8 space-y-4"
        >
          <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
            <Activity className="text-primary w-5 h-5" />
            Feature-Level Stability
          </h3>
          <div className="space-y-3 max-h-60 overflow-y-auto">
            {Object.entries(result.psi_per_feature)
              .sort((a, b) => b[1] - a[1])
              .map(([feature, score]) => (
                <div key={feature} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-mono text-on-surface-variant">{feature}</span>
                    <span className={`text-xs font-bold font-mono ${
                      score >= 0.25 ? 'text-error' : score >= 0.1 ? 'text-yellow-600' : 'text-tertiary'
                    }`}>
                      {score.toFixed(4)}
                    </span>
                  </div>
                  <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        score >= 0.25 ? 'bg-error' : score >= 0.1 ? 'bg-yellow-500' : 'bg-tertiary'
                      }`}
                      style={{ width: `${Math.min(score / 0.5 * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </motion.div>
      )}

      {/* System Details */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-panel rounded-2xl p-6 border border-outline-variant/20"
      >
        <h4 className="text-xs font-bold uppercase tracking-widest text-outline mb-4">System Details</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-on-surface-variant text-xs">Status</p>
            <p className="font-mono font-bold text-tertiary">{result.status}</p>
          </div>
          <div>
            <p className="text-on-surface-variant text-xs">LLM Used</p>
            <p className="font-mono font-bold text-primary">{result.explanation_llm}</p>
          </div>
          <div>
            <p className="text-on-surface-variant text-xs">Model</p>
            <p className="font-mono font-bold text-on-surface">{result.model_used}</p>
          </div>
          <div>
            <p className="text-on-surface-variant text-xs">Drift Status</p>
            <p className={`font-mono font-bold ${result.drift_detected ? 'text-error' : 'text-tertiary'}`}>
              {result.drift_detected ? 'Detected' : 'Stable'}
            </p>
          </div>
        </div>
      </motion.div>
    </motion.section>
  );
}
