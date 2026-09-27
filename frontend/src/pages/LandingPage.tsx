import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    ArrowRight,
    Database,
    FlaskConical,
    Globe2,
    Microscope,
    Network,
    SearchCheck,
    ShieldCheck
} from 'lucide-react';

const researchStages = [
    'Question',
    'Hypotheses',
    'Independent Research',
    'Evidence',
    'Challenge',
    'Replication',
    'Validation'
];

const capabilities = [
    {
        icon: Microscope,
        title: 'Specialist Research Crew',
        description: 'Coordinate climate, ocean, atmosphere, biodiversity, carbon, geospatial, hazard and research-method agents around a shared scientific question.'
    },
    {
        icon: Network,
        title: 'Evidence Graph',
        description: 'Connect claims to sources, datasets, observations, methods, assumptions, contradictions and replication history instead of reducing research to a generated answer.'
    },
    {
        icon: SearchCheck,
        title: 'Adversarial Validation',
        description: 'Challenge important findings through criticism, competing explanations, falsification attempts, replication, uncertainty analysis and novelty review.'
    },
    {
        icon: Globe2,
        title: 'Earth Observatory',
        description: 'Bring Earth-observation and environmental data into the same research workspace as literature, models, simulations and agent reasoning.'
    },
    {
        icon: Database,
        title: 'Research Memory',
        description: 'Preserve hypotheses, evidence, rejected explanations and unresolved questions across long-running projects while keeping memory distinct from verified evidence.'
    },
    {
        icon: ShieldCheck,
        title: 'Traceable Discovery',
        description: 'Advance findings toward discovery candidates only with visible provenance, uncertainty and validation history, keeping human and expert review in the loop.'
    }
];

const LandingPage = () => {
    const navigate = useNavigate();
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();

        const points = Array.from({ length: 80 }, () => ({
            x: Math.random(),
            y: Math.random(),
            speed: 0.00005 + Math.random() * 0.00012,
            radius: 0.5 + Math.random() * 1.4
        }));

        let frame = 0;
        let animationFrame = 0;
        const draw = () => {
            frame += 1;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            points.forEach((point) => {
                point.y -= point.speed * 16;
                if (point.y < -0.02) point.y = 1.02;

                const x = point.x * canvas.width;
                const y = point.y * canvas.height;
                ctx.beginPath();
                ctx.fillStyle = `rgba(34, 211, 238, ${0.18 + (Math.sin(frame * 0.01 + point.x * 8) + 1) * 0.08})`;
                ctx.arc(x, y, point.radius, 0, Math.PI * 2);
                ctx.fill();
            });

            animationFrame = requestAnimationFrame(draw);
        };

        draw();
        window.addEventListener('resize', resize);
        return () => {
            cancelAnimationFrame(animationFrame);
            window.removeEventListener('resize', resize);
        };
    }, []);

    return (
        <div className="relative min-h-screen overflow-hidden bg-black text-white font-sans selection:bg-cyan-400 selection:text-black">
            <canvas ref={canvasRef} className="fixed inset-0 z-0 opacity-70 pointer-events-none" aria-hidden="true" />
            <div className="fixed inset-0 z-0 bg-[radial-gradient(circle_at_50%_20%,rgba(6,182,212,0.14),transparent_38%),radial-gradient(circle_at_85%_65%,rgba(124,58,237,0.08),transparent_30%)] pointer-events-none" />

            <div className="relative z-10">
                <header className="px-6 md:px-10 py-5 flex justify-between items-center border-b border-white/10 bg-black/60 backdrop-blur-xl">
                    <button onClick={() => navigate('/')} className="flex items-center gap-3 text-left" aria-label="Climate Crew home">
                        <div className="w-10 h-10 rounded-xl border border-cyan-400/30 bg-cyan-400/10 flex items-center justify-center shadow-[0_0_24px_rgba(34,211,238,0.12)]">
                            <Globe2 className="text-cyan-300 w-6 h-6" />
                        </div>
                        <div>
                            <div className="text-xl md:text-2xl font-black tracking-[0.12em]">CLIMATE <span className="text-cyan-300">CREW</span></div>
                            <div className="text-[9px] md:text-[10px] uppercase tracking-[0.28em] text-gray-500">Climate Research Agent Team</div>
                        </div>
                    </button>
                    <button
                        onClick={() => navigate('/app/research')}
                        className="px-4 md:px-6 py-2.5 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400 hover:text-black transition-all uppercase tracking-[0.18em] text-[10px] md:text-xs font-bold rounded-lg"
                    >
                        Open Research
                    </button>
                </header>

                <main>
                    <section className="min-h-[78vh] flex items-center px-6 md:px-10 py-20">
                        <div className="w-full max-w-7xl mx-auto grid lg:grid-cols-[1.15fr_0.85fr] gap-14 items-center">
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/5 text-cyan-200 text-xs uppercase tracking-[0.18em] mb-7">
                                    <FlaskConical size={14} /> Evidence-driven multi-agent research
                                </div>
                                <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-black tracking-tight leading-[0.94] max-w-5xl">
                                    Investigate climate problems with a <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 to-cyan-500">scientific agent team.</span>
                                </h1>
                                <p className="mt-8 text-lg md:text-xl text-gray-300 max-w-3xl leading-relaxed">
                                    Climate Crew coordinates specialised researchers, Earth-observation data, literature, datasets, models and simulations through a research process built for evidence, challenge, replication and validation.
                                </p>
                                <p className="mt-4 text-base text-gray-500 max-w-2xl leading-relaxed">
                                    Agent agreement is not treated as scientific truth. Claims advance because their evidence survives scrutiny.
                                </p>
                                <div className="mt-10 flex flex-col sm:flex-row gap-4">
                                    <button
                                        onClick={() => navigate('/app/research')}
                                        className="group px-7 py-4 bg-cyan-400 text-black font-black tracking-[0.12em] uppercase text-sm rounded-lg hover:bg-cyan-300 transition-colors flex items-center justify-center gap-3"
                                    >
                                        Start Research <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                    </button>
                                    <button
                                        onClick={() => navigate('/app/globe')}
                                        className="px-7 py-4 border border-white/15 bg-white/[0.03] text-white font-bold tracking-[0.12em] uppercase text-sm rounded-lg hover:border-cyan-400/40 hover:bg-cyan-400/5 transition-colors"
                                    >
                                        Earth Observatory
                                    </button>
                                </div>
                            </div>

                            <div className="relative">
                                <div className="absolute inset-0 bg-cyan-400/10 blur-[100px] rounded-full" />
                                <div className="relative border border-white/10 bg-white/[0.035] backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-2xl">
                                    <div className="flex items-center justify-between mb-8">
                                        <div>
                                            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Research lifecycle</p>
                                            <h2 className="text-xl font-bold mt-1">Evidence before consensus</h2>
                                        </div>
                                        <Network className="text-cyan-300" />
                                    </div>
                                    <div className="space-y-2">
                                        {researchStages.map((stage, index) => (
                                            <div key={stage} className="flex items-center gap-4 p-3 rounded-xl border border-white/[0.06] bg-black/30">
                                                <div className="w-8 h-8 shrink-0 rounded-full border border-cyan-400/25 bg-cyan-400/10 text-cyan-200 flex items-center justify-center font-mono text-xs">
                                                    {String(index + 1).padStart(2, '0')}
                                                </div>
                                                <span className="font-medium text-gray-200">{stage}</span>
                                                {index < researchStages.length - 1 && <div className="ml-auto text-gray-700">↓</div>}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="border-y border-white/10 bg-white/[0.02] px-6 md:px-10 py-20">
                        <div className="max-w-7xl mx-auto">
                            <div className="max-w-3xl mb-12">
                                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-3">Research architecture</p>
                                <h2 className="text-3xl md:text-5xl font-black">A research system, not a chatbot.</h2>
                                <p className="mt-5 text-gray-400 text-lg leading-relaxed">
                                    Each investigation can become a durable research project with hypotheses, claims, evidence, contradictions, methods, uncertainty and replication history that remain inspectable as the work evolves.
                                </p>
                            </div>

                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                                {capabilities.map(({ icon: Icon, title, description }) => (
                                    <article key={title} className="p-6 rounded-2xl border border-white/10 bg-black/35 hover:border-cyan-400/30 transition-colors">
                                        <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center mb-5">
                                            <Icon className="w-5 h-5 text-cyan-300" />
                                        </div>
                                        <h3 className="text-lg font-bold mb-3">{title}</h3>
                                        <p className="text-sm leading-relaxed text-gray-400">{description}</p>
                                    </article>
                                ))}
                            </div>
                        </div>
                    </section>

                    <section className="px-6 md:px-10 py-24">
                        <div className="max-w-5xl mx-auto text-center">
                            <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-4">From investigation to discovery</p>
                            <h2 className="text-4xl md:text-6xl font-black">Discover carefully.</h2>
                            <p className="mt-6 text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed">
                                Climate Crew is designed to preserve disagreement, expose uncertainty and make the path from observation to discovery candidate auditable. The goal is faster research without pretending confidence is evidence.
                            </p>
                            <button
                                onClick={() => navigate('/app/research')}
                                className="mt-10 inline-flex items-center gap-3 px-8 py-4 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400 hover:text-black transition-all rounded-lg font-bold uppercase tracking-[0.14em] text-sm"
                            >
                                Enter Climate Crew <ArrowRight size={18} />
                            </button>
                        </div>
                    </section>
                </main>

                <footer className="border-t border-white/10 px-6 md:px-10 py-6 bg-black/70">
                    <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-3 md:items-center md:justify-between text-xs text-gray-500">
                        <span>Climate Crew — evidence-driven multi-agent climate research and discovery.</span>
                        <span>Investigate independently · Challenge aggressively · Preserve the evidence · Discover carefully</span>
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default LandingPage;
