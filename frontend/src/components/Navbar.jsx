import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Settings, User, LogOut } from 'lucide-react';

const navLinks = [
 { label: 'Dashboard', path: '/' },
 { label: 'Upload & Predict', path: '/upload' },
 { label: 'Model Registry', path: '/model-training' },
 { label: 'Drift Detection', path: '/drift-detection' },
 { label: 'LLM Evaluation', path: '/llm-evaluation' },
 { label: 'Governance', path: '/governance' },
];

const notifications = [
 { id: 1, message: 'CSV loaded successfully', time: '2 min ago', type: 'success' },
 { id: 2, message: 'Model retrain completed', time: '15 min ago', type: 'success' },
 { id: 3, message: 'Drift detected in feature_x', time: '1 hour ago', type: 'warning' },
 { id: 4, message: 'Governance event logged', time: '3 hours ago', type: 'info' },
 { id: 5, message: 'Batch prediction finished', time: '5 hours ago', type: 'success' },
];

export default function Navbar() {
 const location = useLocation();
 const [notifOpen, setNotifOpen] = useState(false);
 const [profileOpen, setProfileOpen] = useState(false);

 return (
 <header className="glass-panel sticky top-0 z-50 flex justify-between items-center w-full px-8 py-4 border-b border-outline-variant/30 rounded-none bg-surface/30">
 <div className="flex items-center gap-8">
        <Link to="/" className="text-2xl font-bold tracking-tighter text-on-surface font-headline bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
 Drifting Oracle
 </Link>

 <nav className="hidden md:flex gap-6 items-center">
 {navLinks.map((link) => (
 <Link
 key={link.label}
 to={link.path}
 className={`font-headline font-semibold tracking-tight pb-2 transition-colors duration-200 ${
 location.pathname === link.path
 ? 'text-primary border-b-2 border-primary'
 : 'text-on-surface-variant hover:text-on-surface'
 }`}
 >
 {link.label}
 </Link>
 ))}
 </nav>
 </div>

 <div className="flex items-center gap-4">
 <div className="relative">
 <button
 onClick={() => setNotifOpen((prev) => !prev)}
 className="text-on-surface-variant cursor-pointer p-2 rounded-full hover:bg-primary/10 hover:text-primary transition-colors relative"
 aria-label="Toggle notifications"
 type="button"
 >
 <Bell size={20} />
 <span className="absolute top-1 right-1.5 w-2 h-2 bg-error rounded-full border-2 border-surface animate-pulse"></span>
 </button>

 <AnimatePresence>
 {notifOpen && (
 <motion.div 
 initial={{ opacity: 0, y: 10, scale: 0.95 }}
 animate={{ opacity: 1, y: 0, scale: 1 }}
 exit={{ opacity: 0, y: 10, scale: 0.95 }}
 transition={{ duration: 0.2 }}
 className="absolute right-0 mt-2 w-80 bg-[#121212] border border-outline-variant/50 rounded-xl shadow-[0_0_40px_rgba(0,0,0,0.8)] overflow-hidden"
 >
 <div className="glass-panel px-4 py-3 border-b border-outline-variant/20 rounded-none bg-surface-container/30">
 <h3 className="text-sm font-semibold text-on-surface tracking-wide uppercase font-headline">Notifications</h3>
 </div>

 <div className="max-h-96 overflow-y-auto">
 {notifications.map((notif) => (
 <div
 key={notif.id}
 className="px-4 py-3 border-b border-outline-variant/10 hover:bg-surface-container-highest transition-colors cursor-pointer last:border-b-0"
 >
 <div className="flex items-start gap-3">
 <div
 className={`w-2 h-2 rounded-full mt-1 shrink-0 ${
 notif.type === 'success'
 ? 'bg-pink-400'
 : notif.type === 'warning'
 ? 'bg-error'
 : 'bg-primary'
 }`}
 ></div>
 <div className="flex-1 min-w-0">
 <p className="text-sm text-on-surface">{notif.message}</p>
 <p className="text-xs text-on-surface-variant mt-1">{notif.time}</p>
 </div>
 </div>
 </div>
 ))}
 </div>

 <div className="glass-panel px-4 py-2 border-t border-outline-variant/20 text-center rounded-none bg-surface-container/30">
 <button className="text-xs text-primary hover:text-primary/80 font-bold uppercase tracking-widest" type="button">
 View all
 </button>
 </div>
 </motion.div>
 )}
 </AnimatePresence>
 </div>

 <Link
 to="/settings"
 className="text-on-surface-variant cursor-pointer p-2 rounded-full hover:bg-primary/10 hover:text-primary transition-colors"
 aria-label="Open settings"
 >
 <Settings size={20} />
 </Link>

 <div className="relative">
 <button
 onClick={() => setProfileOpen((prev) => !prev)}
 className="w-10 h-10 rounded-full border border-primary/30 shadow-[0_0_15px_rgba(236, 72, 153,0.2)] glass-panel flex items-center justify-center hover:opacity-100 hover:border-accent hover:shadow-[0_0_20px_rgba(236, 72, 153,0.4)] transition-all"
 aria-label="Open profile menu"
 type="button"
 >
 <User size={18} className="text-accent" />
 </button>

 <AnimatePresence>
 {profileOpen && (
 <motion.div 
 initial={{ opacity: 0, y: 10, scale: 0.95 }}
 animate={{ opacity: 1, y: 0, scale: 1 }}
 exit={{ opacity: 0, y: 10, scale: 0.95 }}
 transition={{ duration: 0.2 }}
 className="absolute right-0 mt-2 w-72 bg-[#121212] border border-outline-variant/50 rounded-xl shadow-[0_0_40px_rgba(0,0,0,0.8)] overflow-hidden"
 >
 <div className="px-4 py-4 border-b border-outline-variant/20 glass-panel rounded-none bg-primary/5">
 <p className="text-[10px] uppercase font-bold tracking-widest text-outline">Signed in as</p>
 <p className="mt-1 text-base font-headline font-bold text-on-surface">Naman Aryan</p>
 <p className="text-xs text-on-surface-variant font-mono">namanaryan08@gmail.com</p>
 </div>

 <div className="py-2">
 <Link
 to="/settings"
 onClick={() => setProfileOpen(false)}
 className="w-full px-4 py-2 text-left text-sm text-on-surface-variant hover:text-accent hover:bg-surface-container-highest transition-colors flex items-center gap-3"
 >
 <Settings size={16} />
 Account Settings
 </Link>
 <button
 type="button"
 onClick={() => setProfileOpen(false)}
 className="w-full px-4 py-2 text-left text-sm text-on-surface-variant hover:text-error hover:bg-error-container transition-colors flex items-center gap-3"
 >
 <LogOut size={16} />
 Sign out
 </button>
 </div>
 </motion.div>
 )}
 </AnimatePresence>
 </div>
 </div>
 </header>
 );
}
