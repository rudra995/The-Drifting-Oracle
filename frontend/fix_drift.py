import sys

with open("src/pages/DriftDetectionPage.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add current variables
text = text.replace(
    "  const latestEntry = Array.isArray(historyData) && historyData.length > 0 ? historyData[0] : null;\n  const features = latestEntry?.drift_features || [];",
    "  const latestEntry = Array.isArray(historyData) && historyData.length > 0 ? historyData[0] : null;\n  const features = latestEntry?.drift_features || [];\n  \n  const currentDriftStatus = latestEntry ? (latestEntry.drift_detected ? 'CRITICAL' : 'STABLE') : 'STABLE';\n  const currentPsiScore = latestEntry ? latestEntry.overall_psi : null;\n  const currentMessage = latestEntry ? (latestEntry.drift_detected ? 'Significant population stability shifts observed.' : 'System operating normally.') : 'Awaiting data...';"
)

# 2. Add || historyLoading logic
text = text.replace("{psiLoading ? (", "{psiLoading || historyLoading ? (")

# 3. Replace condition checks and interpolations
text = text.replace("psiData?.status === 'CRITICAL' ", "currentDriftStatus === 'CRITICAL' ")
text = text.replace("psiData?.status === 'CRITICAL'?", "currentDriftStatus === 'CRITICAL'?")
text = text.replace("psiData?.status === 'CRITICAL' ?", "currentDriftStatus === 'CRITICAL' ?")
text = text.replace("psiData.psi?.toFixed", "currentPsiScore?.toFixed")
text = text.replace("psiData?.message || 'System operating normally.' ", "currentMessage ")
text = text.replace("{psiData?.message || 'System operating normally.'}", "{currentMessage}")
text = text.replace(
    "{psiData?.psi != null ? psiData.psi.toFixed(4) : '—'}",
    "{currentPsiScore != null ? currentPsiScore.toFixed(4) : '—'}"
)
text = text.replace(
    "<span className=\"text-sm font-bold text-on-surface\">0.250</span>",
    "<span className=\"text-sm font-bold text-on-surface\">{psiData?.threshold != null ? psiData.threshold.toFixed(3) : '0.250'}</span>"
)
text = text.replace(
    "{psiData?.status || '—'}",
    "{currentDriftStatus}"
)

# Fix possible lingering replacements
text = text.replace("psiData?.status === 'CRITICAL'", "currentDriftStatus === 'CRITICAL'")

with open("src/pages/DriftDetectionPage.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Success")
