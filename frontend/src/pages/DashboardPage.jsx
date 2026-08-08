import { useState } from 'react';
import SystemOverview from '../components/SystemOverview';
import KpiCards from '../components/KpiCards';
import PsiBarChart from '../components/PsiBarChart';
import ScatterPlot from '../components/ScatterPlot';
import EventTimeline from '../components/EventTimeline';
import QuickPrediction from '../components/QuickPrediction';
import PredictionResults from '../components/PredictionResults';

export default function DashboardPage() {
 const [predictionResult, setPredictionResult] = useState(null);

 return (
 <main className="p-8 max-w-400 mx-auto space-y-8 relative">
 {/* Oracle Midnight Background Glows */}
 <div className="fixed -top-20 left-1/4 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none z-0" />
 <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] bg-accent/10 rounded-full blur-[120px] pointer-events-none z-0" />
 
 <div className="relative z-10 space-y-8">
 <SystemOverview />
 <KpiCards />
 
 {/* Single Loan Prediction Section */}
 <div className="space-y-6">
 <QuickPrediction onPredictionResult={setPredictionResult} />
 {predictionResult && <PredictionResults result={predictionResult} />}
 </div>

 {/* System Overview Charts */}
 <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 <PsiBarChart />
 <ScatterPlot />
 </section>
 </div>
 </main>
 );
}
