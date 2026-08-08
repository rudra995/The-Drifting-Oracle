import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Settings } from 'lucide-react';
import { fetchApi } from '../api';

export default function QuickPrediction({ onPredictionResult }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    AMT_INCOME_TOTAL: 200000.0,
    AMT_CREDIT_x: 500000.0,
    AMT_ANNUITY: 25000.0,
    CNT_CHILDREN: 0,
    CNT_FAM_MEMBERS: 2.0,
    DAYS_EMPLOYED: -1500.0,
    EXT_SOURCE_1: 0.5,
    EXT_SOURCE_2: 0.5,
    EXT_SOURCE_3: 0.5,
    REGION_POPULATION_RELATIVE: 0.03,
    REGION_RATING_CLIENT: 2,
    FLAG_EMP_PHONE: 1,
    FLAG_WORK_PHONE: 0,
    age: 35.0,
    income_credit_ratio: 0.4,
    annuity_ratio: 0.05,
    CODE_GENDER_M: 1,
    CODE_GENDER_XNA: 0,
    FLAG_OWN_CAR_Y: 0,
    FLAG_OWN_REALTY_Y: 1,
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: field.startsWith('FLAG_') || field === 'CNT_CHILDREN' || field === 'REGION_RATING_CLIENT' || field === 'CODE_GENDER_M' || field === 'CODE_GENDER_XNA' || field === 'FLAG_OWN_CAR_Y' || field === 'FLAG_OWN_REALTY_Y'
        ? parseInt(value) || 0
        : parseFloat(value) || 0,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await fetchApi('/predict', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
      if (result && result.status === 'success') {
        onPredictionResult(result);
        setIsExpanded(false);
      }
    } catch (error) {
      console.error('Prediction failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: 'AMT_INCOME_TOTAL', label: 'Annual Income', type: 'number', group: 'Financials' },
    { key: 'AMT_CREDIT_x', label: 'Credit Amount', type: 'number', group: 'Financials' },
    { key: 'AMT_ANNUITY', label: 'Annuity', type: 'number', group: 'Financials' },
    { key: 'income_credit_ratio', label: 'Income/Credit Ratio', type: 'number', group: 'Financials' },
    { key: 'annuity_ratio', label: 'Annuity Ratio', type: 'number', group: 'Financials' },
    { key: 'age', label: 'Age', type: 'number', group: 'Demographics' },
    { key: 'CNT_CHILDREN', label: 'Children Count', type: 'number', group: 'Demographics' },
    { key: 'CNT_FAM_MEMBERS', label: 'Family Members', type: 'number', group: 'Demographics' },
    { key: 'CODE_GENDER_M', label: 'Gender: Male (1/0)', type: 'number', group: 'Demographics' },
    { key: 'REGION_RATING_CLIENT', label: 'Region Rating', type: 'number', group: 'Demographics' },
    { key: 'DAYS_EMPLOYED', label: 'Days Employed', type: 'number', group: 'Employment' },
    { key: 'FLAG_EMP_PHONE', label: 'Has Employer Phone (1/0)', type: 'number', group: 'Employment' },
    { key: 'FLAG_WORK_PHONE', label: 'Has Work Phone (1/0)', type: 'number', group: 'Employment' },
    { key: 'EXT_SOURCE_1', label: 'External Source 1', type: 'number', group: 'Risk Scores' },
    { key: 'EXT_SOURCE_2', label: 'External Source 2', type: 'number', group: 'Risk Scores' },
    { key: 'EXT_SOURCE_3', label: 'External Source 3', type: 'number', group: 'Risk Scores' },
    { key: 'REGION_POPULATION_RELATIVE', label: 'Region Population', type: 'number', group: 'Geography' },
    { key: 'FLAG_OWN_CAR_Y', label: 'Owns Car (1/0)', type: 'number', group: 'Assets' },
    { key: 'FLAG_OWN_REALTY_Y', label: 'Owns Real Estate (1/0)', type: 'number', group: 'Assets' },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-2xl overflow-hidden"
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-8 py-4 border-b border-outline-variant/10 flex items-center justify-between cursor-pointer hover:bg-surface-container/30 transition-colors"
      >
        <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
          <Settings className="text-primary w-5 h-5" />
          Single Loan Prediction
        </h3>
        <div className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          <svg className="w-5 h-5 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>

      {isExpanded && (
        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          {/* Quick Input Section */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {fields.slice(0, 8).map((field) => (
              <div key={field.key}>
                <label className="text-xs font-bold uppercase tracking-widest text-outline mb-2 block">
                  {field.label}
                </label>
                <input
                  type={field.type}
                  value={formData[field.key]}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/30 rounded-lg px-3 py-2 text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
                />
              </div>
            ))}
          </div>

          {/* Advanced Fields - Collapsible */}
          <details className="border-t border-outline-variant/10 pt-6">
            <summary className="cursor-pointer font-bold text-primary flex items-center gap-2 hover:opacity-80">
              <span>+</span> Advanced Fields
            </summary>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
              {fields.slice(8).map((field) => (
                <div key={field.key}>
                  <label className="text-xs font-bold uppercase tracking-widest text-outline mb-2 block">
                    {field.label}
                  </label>
                  <input
                    type={field.type}
                    value={formData[field.key]}
                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                    className="w-full bg-surface-container-highest border border-outline-variant/30 rounded-lg px-3 py-2 text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
                  />
                </div>
              ))}
            </div>
          </details>

          {/* Submit Button */}
          <div className="flex gap-4 justify-end pt-6 border-t border-outline-variant/10">
            <button
              type="button"
              onClick={() => setIsExpanded(false)}
              className="px-6 py-2 rounded-lg border border-outline-variant/30 text-on-surface font-semibold hover:bg-surface-container/50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="oracle-glow text-white px-8 py-2 rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/20 active:scale-95 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              <Send size={16} />
              {loading ? 'Predicting...' : 'Get Prediction'}
            </button>
          </div>
        </form>
      )}
    </motion.section>
  );
}
