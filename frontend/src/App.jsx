import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import AnimatedGrid from './components/AnimatedGrid';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DriftDetectionPage from './pages/DriftDetectionPage';
import GovernancePage from './pages/GovernancePage';
import ModelTrainingPage from './pages/ModelTrainingPage';
import LlmEvaluationPage from './pages/LlmEvaluationPage';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';

function App() {
 return (
 <BrowserRouter>
 <div className="min-h-screen bg-surface font-body text-on-surface flex flex-col relative">
 <AnimatedGrid />
 <Navbar />
 <div className="flex-1">
 <Routes>
 <Route path="/" element={<DashboardPage />} />
 <Route path="/upload" element={<UploadPage />} />
 <Route path="/drift-detection" element={<DriftDetectionPage />} />
 <Route path="/governance" element={<GovernancePage />} />
 <Route path="/model-training" element={<ModelTrainingPage />} />
 <Route path="/llm-evaluation" element={<LlmEvaluationPage />} />
 <Route path="/settings" element={<SettingsPage />} />
 <Route path="/profile" element={<ProfilePage />} />
 </Routes>
 </div>
 <Footer />
 </div>
 </BrowserRouter>
 );
}

export default App;

