import { motion } from 'framer-motion';
import { User } from 'lucide-react';

export default function ProfilePage() {
 return (
 <motion.main 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5 }}
 className="p-8 max-w-400 mx-auto space-y-8 relative z-10"
 >
 {/* Decorative blurs */}
 <div className="fixed top-20 right-20 w-[300px] h-[300px] bg-primary/10 rounded-full blur-[80px] pointer-events-none" />

 <section className="rounded-2xl glass-panel p-6 md:p-8">
 <h1 className="text-3xl font-headline font-bold tracking-tight text-on-surface">User Profile</h1>
 <p className="mt-2 text-on-surface-variant">Account information for the current operator.</p>
 </section>

 <section className="rounded-2xl glass-panel p-6 md:p-8">
 <div className="flex items-start gap-6">
 <div className="h-20 w-20 rounded-full border border-primary/30 bg-primary/10 flex items-center justify-center shadow-[0_0_15px_rgba(236, 72, 153,0.2)]">
 <User className="text-primary" size={36} />
 </div>
 <div className="space-y-2 pt-2">
 <div>
 <p className="text-[10px] uppercase font-bold tracking-widest text-outline">Name</p>
 <p className="text-xl font-headline font-bold text-on-surface">Naman Aryan</p>
 </div>
 <div>
 <p className="text-[10px] uppercase font-bold tracking-widest text-outline pt-2">Email</p>
 <p className="text-base font-mono text-on-surface-variant font-medium">namanaryan08@gmail.com</p>
 </div>
 </div>
 </div>
 </section>
 </motion.main>
 );
}