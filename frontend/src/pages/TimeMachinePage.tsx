import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Clock,
    Play,
    TrendingUp,
    Activity,
    AlertOctagon,
    Loader2,
    Film,
    ArrowRight,
    History,
    Zap
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const TimeMachinePage = () => {
    interface Scenario {
        title: string;
        analysis: string;
        video_url: string | null;
        domain_reports?: Record<string, string>;
    }

    const [mode, setMode] = useState<'landing' | 'simulation'>('landing');
    const [query, setQuery] = useState('');
    const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');
    const [simId, setSimId] = useState<string | null>(null);
    const [resultUrl, setResultUrl] = useState<string | null>(null);
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [logs, setLogs] = useState<string[]>([]);
    // Polling logic
    useEffect(() => {
        let interval: any;
        if (status === 'generating' && simId) {
            interval = setInterval(async () => {
                try {
                    const res = await fetch(`http://localhost:8000/climate-time-machine/status/${simId}`);
                    const data = await res.json();

                    if (data.status === 'completed') {
                        setResultUrl(data.url);
                        if (data.scenarios) {
                            setScenarios(data.scenarios);
                        }
                        setStatus('complete');
                        setLogs(prev => [...prev, "Simulation finalized. Rendering video..."]);
                        clearInterval(interval);
                    } else if (data.status === 'failed') {
                        setStatus('error');
                        setLogs(prev => [...prev, `Simulation failed: ${data.error}`]);
                        clearInterval(interval);
                    } else {
                        // Real-time logs from backend
                        if (data.logs && Array.isArray(data.logs)) {
                            // Deduplicate logs or just set them? Backend appends, so we can just set.
                            setLogs(data.logs);
                        }
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 5000);
        }
        return () => clearInterval(interval);
    }, [status, simId]);

    const PRESETS = [
        "Catastrophic flash flooding in Times Square, NYC (2050)",
        "Amazon Rainforest completely drying out due to 3°C warming",
        "Downtown Mumbai submerged by 2m sea level rise",
        "Wildfire engulfing the Hollywood Sign, Los Angeles"
    ];

    const handleSimulate = async () => {
        if (!query) return;
        setStatus('generating');
        setResultUrl(null);
        setLogs(["Initiating Digital Twin Protocol..."]);
        setScenarios([]);

        try {
            const res = await fetch('http://localhost:8000/climate-time-machine/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_description: query, years: 5 })
            });
            const data = await res.json();

            // Extract ID
            const match = data.video_url.match(/simulation_([a-f0-9-]+)\.gif/);
            if (match) {
                setSimId(match[1]);
            } else {
                // Fallback attempt to parse ID if URL format changes
                const msgMatch = data.message.match(/ID: ([a-f0-9-]+)/);
                if (msgMatch) setSimId(msgMatch[1]);
            }

        } catch (e) {
            setStatus('error');
            setLogs(prev => [...prev, "Critical API Failure."]);
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white p-4 md:p-8 pb-32 overflow-y-auto custom-scrollbar font-sans selection:bg-purple-500/30 relative">

            {/* Background Grid */}
            <div className="fixed inset-0 pointer-events-none opacity-20"
                style={{
                    backgroundImage: 'linear-gradient(rgba(168, 85, 247, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(168, 85, 247, 0.1) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }}
            />

            {/* Header */}
            <header className="flex items-center gap-4 mb-12 relative z-10">
                <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20 shadow-[0_0_15px_-3px_rgba(168,85,247,0.3)]">
                    <Clock className="text-purple-500" size={24} />
                </div>
                <div>
                    <h1 className="text-3xl font-black tracking-tighter">TEMPORAL <span className="text-gray-600">ENGINE</span></h1>
                    <p className="text-xs text-gray-400 font-mono tracking-widest">CLIMATE PREDICTION & BACKCASTING NODE</p>
                </div>
            </header>

            <AnimatePresence mode="wait">
                {mode === 'landing' ? (
                    <motion.div
                        key="landing"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="max-w-6xl mx-auto relative z-10"
                    >
                        <div className="text-center mb-16">
                            <h2 className="text-5xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-gray-800 mb-6 tracking-tight">
                                PREDICT THE FUTURE.
                            </h2>
                            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
                                Our Digital Twin engine simulates hyper-localized climate scenarios using generative agentic reasoning.
                                Visualize cascading effects before they happen.
                            </p>
                        </div>

                        {/* Feature Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                            {[
                                {
                                    icon: TrendingUp,
                                    title: "Predictive Modeling",
                                    desc: "Simulate complex environmental chain reactions (e.g., how a 2°C rise impacts local agriculture).",
                                    color: "text-blue-400",
                                    border: "border-blue-500/20",
                                    bg: "bg-blue-500/5"
                                },
                                {
                                    icon: Film,
                                    title: "Visual Generation",
                                    desc: "Generate frame-by-frame satellite imagery of potential futures using generative video models.",
                                    color: "text-purple-400",
                                    border: "border-purple-500/20",
                                    bg: "bg-purple-500/5"
                                },
                                {
                                    icon: AlertOctagon,
                                    title: "Policy Stress-Testing",
                                    desc: "Test mitigation strategies against extreme 'Black Swan' events to ensure resilience.",
                                    color: "text-amber-400",
                                    border: "border-amber-500/20",
                                    bg: "bg-amber-500/5"
                                }
                            ].map((card, i) => (
                                <motion.div
                                    key={i}
                                    whileHover={{ y: -10 }}
                                    className={`p-8 rounded-2xl border ${card.border} ${card.bg} backdrop-blur-xl group relative overflow-hidden`}
                                >
                                    <div className={`absolute -top-10 -right-10 w-32 h-32 ${card.bg} rounded-full blur-[50px] group-hover:opacity-100 transition-opacity opacity-0`} />

                                    <div className={`w-12 h-12 rounded-lg bg-black border border-white/10 flex items-center justify-center mb-6 ${card.color}`}>
                                        <card.icon size={24} />
                                    </div>
                                    <h3 className="text-xl font-bold mb-3">{card.title}</h3>
                                    <p className="text-gray-400 text-sm leading-relaxed">{card.desc}</p>
                                </motion.div>
                            ))}
                        </div>

                        <div className="text-center">
                            <button
                                onClick={() => setMode('simulation')}
                                className="group relative inline-flex items-center gap-3 px-8 py-4 bg-white text-black font-black text-lg rounded-full overflow-hidden hover:scale-105 transition-transform shadow-[0_0_40px_-10px_rgba(168,85,247,0.5)]"
                            >
                                <span className="relative z-10 flex items-center gap-2">LAUNCH SIMULATOR <ArrowRight size={20} /></span>
                                <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </button>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key="simulation"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="max-w-[95vw] mx-auto relative z-10"
                    >
                        {/* Simulation Cockpit */}
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 ring-1 ring-white/10 bg-[#0a0a0a] rounded-3xl p-2 shadow-2xl h-[85vh]">

                            {/* LEFT: CONFIGURATION */}
                            <div className="lg:col-span-3 flex flex-col gap-4 p-6 border-r border-white/5 bg-[#0c0c0c] rounded-l-2xl">
                                <div>
                                    <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
                                        <Zap size={18} className="text-purple-500" /> SEQUENCE CONFIG
                                    </h2>
                                    <p className="text-gray-500 text-xs">Define initial parameters.</p>
                                </div>

                                <div className="space-y-4 flex-1 flex flex-col">
                                    <div className="flex flex-wrap gap-2 mb-2">
                                        {PRESETS.map((preset, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setQuery(preset)}
                                                className="text-[9px] bg-white/5 hover:bg-white/10 active:bg-purple-500/20 border border-white/5 rounded-full px-2 py-1 text-gray-400 transition-colors truncate max-w-full text-left"
                                            >
                                                {preset}
                                            </button>
                                        ))}
                                    </div>

                                    <textarea
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        placeholder="Describe the climate event to simulate..."
                                        className="w-full h-32 bg-[#050505] border border-white/10 rounded-xl p-3 text-white placeholder-gray-700 focus:border-purple-500 outline-none resize-none font-mono text-xs leading-relaxed focus:bg-white/5 transition-all"
                                    />

                                    <button
                                        onClick={handleSimulate}
                                        disabled={status === 'generating'}
                                        className="w-full py-4 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-900/50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_-5px_rgba(168,85,247,0.5)]"
                                    >
                                        {status === 'generating' ? <Loader2 className="animate-spin" /> : <Play size={18} fill="currentColor" />}
                                        {status === 'generating' ? "RUNNING SIMULATION..." : "RUN SIMULATION"}
                                    </button>
                                </div>

                                {/* Logs Terminal */}
                                <div className="flex-1 bg-black border border-white/10 rounded-xl p-3 font-mono text-[10px] overflow-hidden relative min-h-[150px]">
                                    <div className="absolute top-0 left-0 w-full h-6 bg-white/5 border-b border-white/5 flex items-center px-3 gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                        <div className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                                        <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                        <span className="ml-2 text-gray-500">root@climate_node:~#</span>
                                    </div>
                                    <div className="mt-6 space-y-1 text-gray-400 overflow-y-auto h-full pb-4 custom-scrollbar">
                                        {logs.map((log, i) => (
                                            <div key={i} className="flex gap-2">
                                                <span className="opacity-30 text-purple-500">➜</span>
                                                <span className={log.includes("Critical") ? "text-red-500" : "text-gray-300"}>{log}</span>
                                            </div>
                                        ))}
                                        {logs.length === 0 && <span className="opacity-30 animate-pulse">_Waiting for command inputs...</span>}
                                        {status === 'generating' && <span className="h-4 w-2 bg-purple-500 animate-pulse inline-block align-middle ml-1" />}
                                    </div>
                                    <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 pointer-events-none bg-[length:100%_4px,3px_100%] opacity-20" />
                                </div>
                            </div>

                            {/* RIGHT: VIEWPORT */}
                            <div className="lg:col-span-9 bg-black rounded-2xl relative overflow-hidden h-full border-l border-white/5">
                                <div className="absolute top-4 left-4 z-20 flex gap-2">
                                    <div className="bg-black/50 backdrop-blur px-3 py-1 rounded text-[10px] font-bold border border-white/10 text-gray-400">
                                        CAM-01
                                    </div>
                                    <div className="bg-black/50 backdrop-blur px-3 py-1 rounded text-[10px] font-bold border border-white/10 text-red-500 flex items-center gap-1">
                                        <div className="w-1 h-1 bg-red-500 rounded-full animate-pulse" /> REC
                                    </div>
                                </div>

                                {status === 'idle' && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center opacity-30">
                                        <div className="w-32 h-32 border border-dashed border-white/20 rounded-full flex items-center justify-center animate-spin-slow">
                                            <Film size={32} className="text-white/50" />
                                        </div>
                                        <p className="mt-8 font-mono text-xs tracking-[0.2em] text-gray-500">STANDBY MODE</p>
                                    </div>
                                )}

                                {status === 'generating' && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-30">
                                        <div className="relative">
                                            <div className="w-24 h-24 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                                            <div className="absolute inset-0 flex items-center justify-center font-black text-purple-500 text-xs">
                                                AI
                                            </div>
                                        </div>
                                        <p className="mt-6 text-purple-400 font-mono text-xs animate-pulse tracking-widest">GENERATING VISUALIZATION...</p>
                                    </div>
                                )}

                                {status === 'complete' && resultUrl && (
                                    <div className="h-full flex flex-col overflow-y-auto custom-scrollbar">
                                        {/* Main Combined Video */}
                                        <div className="w-full h-1/2 min-h-[300px] shrink-0 relative bg-black border-b border-white/10">
                                            <video
                                                src={resultUrl}
                                                controls // Changed to standard webm if combined, but we use GIF now. Img tag better for GIF looping control?
                                                // Actually video tag works for some gifs but img is safer for pure gif.
                                                // Let's use img for GIF
                                                poster="/placeholder_monitor.png"
                                                className="w-full h-full object-contain"
                                            />
                                            {/* Fallback for GIF if video tag issues: simple img */}
                                            <img src={resultUrl} className="absolute inset-0 w-full h-full object-contain z-10" alt="Simulation Result" />
                                        </div>

                                        {/* Scenarios Grid */}
                                        <div className="flex-1 p-6 space-y-6">
                                            <h3 className="text-xl font-bold sticky top-0 bg-black/80 backdrop-blur z-20 py-2">
                                                <Activity className="inline mr-2 text-purple-500" />
                                                Scenario Breakdown
                                            </h3>

                                            <div className="grid grid-cols-1 gap-6">
                                                {scenarios.map((scenario, idx) => (
                                                    <div key={idx} className="bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-purple-500/50 transition-colors">
                                                        <div className="grid grid-cols-1 md:grid-cols-3">

                                                            {/* Scenario Visual */}
                                                            <div className="bg-black relative aspect-video md:aspect-auto">
                                                                {scenario.video_url ? (
                                                                    <img src={scenario.video_url} className="w-full h-full object-cover" alt={scenario.title} />
                                                                ) : (
                                                                    <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">NO VISUAL</div>
                                                                )}
                                                            </div>

                                                            {/* Scenario Details */}
                                                            <div className="col-span-2 p-4 flex flex-col gap-3">
                                                                <div>
                                                                    <h4 className="font-bold text-lg text-purple-200">{scenario.title}</h4>
                                                                    <p className="text-xs text-gray-400 font-mono mt-1">SCENARIO ID: {idx + 1}</p>
                                                                </div>

                                                                <div className="prose prose-invert prose-sm max-w-none text-gray-300 text-xs leading-relaxed">
                                                                    <ReactMarkdown>{scenario.analysis}</ReactMarkdown>
                                                                </div>

                                                                {/* Domain Reports Accordion/List */}
                                                                {scenario.domain_reports && (
                                                                    <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                                                                        {Object.entries(scenario.domain_reports).map(([agent, report], i) => (
                                                                            <div key={i} className="bg-black/40 border border-white/5 rounded p-2 text-[10px]">
                                                                                <strong className="text-purple-400 block mb-1">{agent}</strong>
                                                                                <p className="line-clamp-3 hover:line-clamp-none transition-all cursor-help" title={report}>{report}</p>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Decorative Grid overlay on Viewport */}
                                <div className="absolute inset-0 pointer-events-none opacity-30"
                                    style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}
                                />
                            </div>
                        </div>

                        <button
                            onClick={() => setMode('landing')}
                            className="mt-8 text-gray-500 hover:text-white text-xs flex items-center gap-2 transition-colors uppercase tracking-widest"
                        >
                            <History size={14} /> // Return to Main Menu
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default TimeMachinePage;
