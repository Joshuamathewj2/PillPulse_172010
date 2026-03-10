import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Pill } from 'lucide-react';

export default function SplashScreen({ onComplete }: { onComplete: () => void }) {
    const [isVisible, setIsVisible] = useState(true);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // Progress bar animation
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    return 100;
                }
                return prev + 1;
            });
        }, 20); // 100 steps * 20ms = 2s total fill time

        // Total duration is 3 seconds (2s fill + some buffer)
        // We'll fade out at 2.8s to finish exactly at 3s
        const timer = setTimeout(() => {
            setIsVisible(false);
            setTimeout(onComplete, 500); // Wait for fade out animation
        }, 2800);

        return () => {
            clearInterval(interval);
            clearTimeout(timer);
        };
    }, [onComplete]);

    // Background particles
    const particles = Array.from({ length: 15 }).map((_, i) => ({
        id: i,
        size: Math.random() * 8 + 4,
        x: Math.random() * 100,
        y: Math.random() * 100,
        duration: Math.random() * 3 + 2,
        delay: Math.random() * 2,
        symbol: Math.random() > 0.5 ? '+' : '•'
    }));

    const brandName = "PillPulse";

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                    className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#030213] overflow-hidden"
                >
                    {/* Background Particles */}
                    <div className="absolute inset-0 pointer-events-none opacity-20">
                        {particles.map((p) => (
                            <motion.div
                                key={p.id}
                                initial={{ y: '110vh', x: `${p.x}vw`, opacity: 0 }}
                                animate={{ 
                                    y: '-10vh', 
                                    opacity: [0, 0.5, 0],
                                }}
                                transition={{ 
                                    duration: p.duration, 
                                    repeat: Infinity, 
                                    delay: p.delay,
                                    ease: "linear"
                                }}
                                className="absolute text-teal-400 font-bold"
                                style={{ fontSize: p.size }}
                            >
                                {p.symbol}
                            </motion.div>
                        ))}
                    </div>

                    {/* Logo and Branding Container */}
                    <div className="relative flex flex-col items-center">
                        {/* Logo Animation */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.5 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="w-24 h-24 mb-6 rounded-3xl shadow-2xl shadow-teal-500/20 overflow-hidden border border-white/10"
                        >
                            <img src="/logo.png" alt="PillPulse" className="w-full h-full object-cover" />
                        </motion.div>

                        {/* Title - Typewriter Effect */}
                        <div className="flex mb-2">
                            {brandName.split("").map((char, i) => (
                                <motion.span
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.8 + (i * 0.08), duration: 0.3 }}
                                    className="text-4xl font-black text-white tracking-tighter"
                                >
                                    {char}
                                </motion.span>
                            ))}
                        </div>

                        {/* Tagline */}
                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 1.6, duration: 0.8 }}
                            className="text-teal-400/80 text-sm font-medium tracking-widest uppercase mb-8"
                        >
                            Your Smart Medicine Guardian
                        </motion.p>

                        {/* Pulsing Icon */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ 
                                opacity: 1,
                                scale: [1, 1.2, 1],
                            }}
                            transition={{ 
                                opacity: { delay: 1.8, duration: 0.5 },
                                scale: { repeat: Infinity, duration: 0.8, ease: "easeInOut" }
                            }}
                            className="mb-8"
                        >
                            <Pill className="w-8 h-8 text-teal-400 fill-teal-400/20" />
                        </motion.div>

                        {/* Progress Bar Container */}
                        <div className="w-64 h-1.5 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm border border-white/5">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                className="h-full bg-gradient-to-r from-blue-500 to-teal-400"
                            />
                        </div>
                    </div>

                    {/* Footer decoration */}
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.3 }}
                        transition={{ delay: 2, duration: 1 }}
                        className="absolute bottom-12 text-[10px] text-gray-500 font-bold uppercase tracking-[0.3em]"
                    >
                        Secure Healthcare AI
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
