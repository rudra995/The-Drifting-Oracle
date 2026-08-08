import React, { useEffect, useRef } from 'react';

const AnimatedGrid = () => {
 const canvasRef = useRef(null);
 const animationRef = useRef(null);
 const timeRef = useRef(0);

 useEffect(() => {
 const canvas = canvasRef.current;
 if (!canvas) return;

 const ctx = canvas.getContext('2d', { alpha: false });
 let width = window.innerWidth;
 let height = window.innerHeight;
 canvas.width = width;
 canvas.height = height;

 const handleResize = () => {
 width = window.innerWidth;
 height = window.innerHeight;
 canvas.width = width;
 canvas.height = height;
 };

 window.addEventListener('resize', handleResize);

 const animate = () => {
 // Clear background with deep neutral gray
 ctx.fillStyle = '#0D0D0D';
 ctx.fillRect(0, 0, width, height);

 timeRef.current += 0.002; // Slower, moody movement

 const gridSize = 70;
 
 // ════════════════════════════════════════════════════════
 // MAIN GRID - Subtle visible horizontal lines
 // ════════════════════════════════════════════════════════
 ctx.strokeStyle = '#ec4899'; // Orange accent
 ctx.lineWidth = 0.5;

 for (let i = 0; i < height + gridSize; i += gridSize) {
 const offset = (timeRef.current * 4) % gridSize;
 const y = i - offset;

 const pulse = Math.abs(Math.sin((timeRef.current + i / 500) * 0.6)) * 0.03 + 0.01;
 ctx.globalAlpha = pulse;
 ctx.beginPath();
 ctx.moveTo(0, y);
 ctx.lineTo(width, y);
 ctx.stroke();
 }

 // ════════════════════════════════════════════════════════
 // MAIN GRID - Subtle visible vertical lines
 // ════════════════════════════════════════════════════════
 ctx.strokeStyle = '#f472b6'; // Secondary orange
 ctx.lineWidth = 0.5;

 for (let i = 0; i < width + gridSize; i += gridSize) {
 const offset = (timeRef.current * 3) % gridSize;
 const x = i - offset;

 const pulse = Math.abs(Math.cos((timeRef.current + i / 600) * 0.5)) * 0.03 + 0.01;
 ctx.globalAlpha = pulse;
 ctx.beginPath();
 ctx.moveTo(x, 0);
 ctx.lineTo(x, height);
 ctx.stroke();
 }

 ctx.globalAlpha = 1;
 animationRef.current = requestAnimationFrame(animate);
 };

 animate();

 return () => {
 window.removeEventListener('resize', handleResize);
 if (animationRef.current) {
 cancelAnimationFrame(animationRef.current);
 }
 };
 }, []);

 return (
 <canvas
 ref={canvasRef}
 className="fixed inset-0 w-full h-full pointer-events-none"
 style={{ zIndex: -1, display: 'block' }}
 />
 );
};

export default AnimatedGrid;
