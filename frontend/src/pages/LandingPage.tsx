import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Globe,
    Shield,
    ArrowRight,
    Cpu,
    Activity
} from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Matrix/Sci-fi Background Animation
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const columns = Math.floor(canvas.width / 20);
        const drops: number[] = new Array(columns).fill(0);

        const chars = '0123456789ABCDEF';

        const draw = () => {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#0ff'; // Cyan color
            ctx.font = '15px monospace';

            for (let i = 0; i < drops.length; i++) {
                const text = chars[Math.floor(Math.random() * chars.length)];
                const x = i * 20;
                const y = drops[i] * 20;

                ctx.fillText(text, x, y);

                if (y > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        };

        const interval = setInterval(draw, 33);

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener('resize', handleResize);

        return () => {
            clearInterval(interval);
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <div className="relative min-h-screen w-full bg-black text-white overflow-hidden font-sans selection:bg-cyan-500 selection:text-black">

            {/* Background Canvas */}
            <canvas
                ref={canvasRef}
                className="absolute inset-0 z-0 opacity-20"
            />

            {/* Gradient Overlay */}
            <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/0 via-black/50 to-black pointer-events-none" />

            {/* Content Container */}
            <div className="relative z-20 flex flex-col min-h-screen">

                {/* Header */}
                <header className="px-8 py-6 flex justify-between items-center border-b border-white/10 backdrop-blur-sm bg-black/30">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-full bg-cyan-500 flex items-center justify-center shadow-[0_0_15px_cyan]">
                            <Globe className="text-black w-6 h-6 animate-pulse" />
                        </div>
                        <h1 className="text-2xl font-black tracking-[0.2em]">
                            CLIMATEX<span className="text-cyan-400">.AI</span>
                        </h1>
                    </div>
                    <button
                        onClick={() => navigate('/app')}
                        className="px-6 py-2 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-500 hover:text-black transition-all duration-300 uppercase tracking-widest text-xs font-bold rounded-sm shadow-[0_0_10px_rgba(6,182,212,0.2)] hover:shadow-[0_0_20px_cyan]"
                    >
                        Access Terminal
                    </button>
                </header>

                {/* Hero Section */}
                <main className="flex-1 flex flex-col items-center justify-center text-center px-4 relative">

                    {/* Glowing Orb/Centerpiece */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-[100px] -z-10 animate-pulse" />

                    <h2 className="text-6xl md:text-8xl font-black mb-6 tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white via-cyan-200 to-cyan-500 drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
                        PLANETARY<br />INTELLIGENCE
                    </h2>

                    <p className="text-xl md:text-2xl text-gray-400 max-w-2xl mb-12 leading-relaxed">
                        Advanced multi-agent systems for global environmental monitoring, audit, and intervention.
                    </p>

                    <button
                        onClick={() => navigate('/app')}
                        className="group relative px-8 py-4 bg-transparent overflow-hidden rounded-none border-2 border-cyan-500 transition-all duration-300 hover:shadow-[0_0_30px_cyan]"
                    >
                        <div className="absolute inset-0 w-0 bg-cyan-500 transition-all duration-[250ms] ease-out group-hover:w-full opacity-10"></div>
                        <span className="relative flex items-center gap-3 text-cyan-400 group-hover:text-white font-bold tracking-[0.2em] text-lg">
                            INITIALIZE SYSTEM <ArrowRight className="group-hover:translate-x-1 transition-transform" />
                        </span>
                    </button>

                    {/* Stats/Grid */}
                    <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl px-4">
                        {[
                            { icon: Cpu, label: "Active Agents", value: "20+", color: "text-purple-400" },
                            { icon: Activity, label: "Data Streams", value: "12MB/s", color: "text-green-400" },
                            { icon: Shield, label: "Global Coverage", value: "100%", color: "text-yellow-400" }
                        ].map((stat, idx) => (
                            <div key={idx} className="p-6 border border-white/10 bg-white/5 backdrop-blur-md hover:border-cyan-500/50 transition-colors group">
                                <stat.icon className={`w-8 h-8 mb-4 ${stat.color} group-hover:animate-bounce`} />
                                <div className="text-4xl font-mono font-bold mb-2">{stat.value}</div>
                                <div className="text-sm text-gray-400 uppercase tracking-widest">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </main>

                {/* Footer ticker */}
                <footer className="w-full border-t border-white/10 bg-black/80 backdrop-blur text-xs text-gray-500 py-3 overflow-hidden whitespace-nowrap">
                    <div className="inline-block animate-[marquee_20s_linear_infinite]">
                        SYSTEM STATUS: ONLINE // SECTOR 7: STABLE // ATMOSPHERIC SENSORS: CALIBRATING // DEEP RESEARCH MODULES: ACTIVE // CARBON AUDIT: IN PROGRESS //
                        SYSTEM STATUS: ONLINE // SECTOR 7: STABLE // ATMOSPHERIC SENSORS: CALIBRATING // DEEP RESEARCH MODULES: ACTIVE // CARBON AUDIT: IN PROGRESS //
                    </div>
                </footer>
            </div>

            <style>{`
                @keyframes marquee {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
            `}</style>
        </div>
    );
};

export default LandingPage;
