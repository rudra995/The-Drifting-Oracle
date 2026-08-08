export default function Footer() {
 return (
 <footer className="mt-20 border-t border-outline-variant/20 py-12 px-8 flex flex-col sm:flex-row justify-between items-center gap-4 glass-panel rounded-none bg-surface/30 relative z-10 shadow-[0_-4px_30px_rgba(0,0,0,0.3)]">
 <div className="flex items-center gap-6">
        <span className="font-headline text-lg font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
 Drifting Oracle
 </span>
 <span className="text-xs font-mono text-outline font-medium tracking-wide">
 © 2024 Editorial Intelligence Systems Inc.
 </span>
 </div>
 <div className="flex gap-8 text-[10px] font-bold text-outline uppercase tracking-[0.2em]">
 <a className="hover:text-primary transition-colors cursor-pointer" href="#">
 API Documentation
 </a>
 <a className="hover:text-primary transition-colors cursor-pointer" href="#">
 Privacy Shield
 </a>
 <a className="hover:text-primary transition-colors cursor-pointer" href="#">
 Support Portal
 </a>
 </div>
 </footer>
 );
}
