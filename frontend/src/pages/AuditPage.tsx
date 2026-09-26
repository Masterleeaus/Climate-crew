import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldCheck,
    Search,
    FileText,
    Download,
    AlertTriangle,
    Loader2,
    Globe,
    MapPin,
    Scan,
    Terminal,
    Cpu,
    Satellite,
    Wifi
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AuditPage = () => {
    const [status, setStatus] = useState<'idle' | 'processing' | 'complete' | 'error'>('idle');
    // loadingStage removed as unused
    // PRE-FILLED FOR CONVENIENCE (User Experience improvement)
    const [query, setQuery] = useState('Amazon Biomass Conservation Unit 4');
    const [lat, setLat] = useState('-3.4653');
    const [lon, setLon] = useState('-62.2159');
    const [result, setResult] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // Log simulation helper
    const addLog = (msg: string) => setLogs(prev => [...prev.slice(-4), `> ${msg}`]);

    useEffect(() => {
        let interval: any;
        if (status === 'processing') {
            const stages = [
                "Establishing secureuplink to Sentinel-2...",
                "Acquiring multi-spectral imagery...",
                "Detecting thermal anomalies (FIRMS)...",
                "Cross-referencing deforestation alerts...",
                "Deploying deep research agents...",
                "Synthesizing legal frameworks...",
                "Generating ISO-14064 compliant artifacts..."
            ];
            let i = 0;
            addLog("Initializing Audit Protocol...");
            interval = setInterval(() => {
                if (i < stages.length) {
                    addLog(stages[i]);
                    // setLoadingStage removed
                    i++;
                }
            }, 9000);
        }
        return () => clearInterval(interval);
    }, [status]);

    const handleVerify = async () => {
        setErrorMessage(null);
        if (!query || !lat || !lon) {
            setErrorMessage("MISSING COORDINATES. TARGET LOCK FAILED.");
            return;
        }

        setStatus('processing');
        setLogs([]);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/audit/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    latitude: parseFloat(lat),
                    longitude: parseFloat(lon)
                })
            });

            if (!response.ok) throw new Error("Verification failed check server logs.");

            const data = await response.json();
            setResult(data);
            addLog("AUDIT COMPLETE. DATA VERIFIED.");
            setStatus('complete');
        } catch (error) {
            console.error(error);
            addLog("CRITICAL ERROR: CONNECTION LOST.");
            setStatus('error');
            setErrorMessage("UPLINK FAILURE: AGENT SERVER UNREACHABLE");
        }
    };

    return (
        <div className="min-h-screen bg-[#020202] text-white p-4 lg:p-12 overflow-hidden flex flex-col font-sans">

            {/* Navbar / Header */}
            <header className="flex justify-between items-center mb-12 border-b border-white/5 pb-6">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-neon-blue/10 rounded-xl flex items-center justify-center border border-neon-blue/20">
                        <ShieldCheck className="text-neon-blue" size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-black tracking-tighter">CLIMATEX <span className="text-gray-600">AUDIT</span></h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest">SENTINEL VERIFICATION NODE v4.2</p>
                    </div>
                </div>
                <div className="flex items-center gap-6 text-xs font-mono text-gray-500">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${status === 'processing' ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
                        SYSTEM {status === 'processing' ? 'BUSY' : 'READY'}
                    </div>
                    <div className="flex items-center gap-2">
                        <Wifi size={14} /> UPLINK STABLE
                    </div>
                </div>
            </header>

            {/* Main Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">

                {/* LEFT COLUMN: CONTROLS */}
                <div className="lg:col-span-5 space-y-6">
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-[#0a0a0a] border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden group"
                    >
                        {/* Decorative Gradient */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-neon-blue/5 rounded-full blur-[80px] -mr-32 -mt-32 pointer-events-none transition-opacity group-hover:opacity-100 opacity-50" />

                        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-8 flex items-center gap-2">
                            <Satellite size={16} /> Target Parameters
                        </h2>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Project Identity</label>
                                <div className="relative group/input">
                                    <Search className="absolute left-4 top-4 text-gray-600 group-focus-within/input:text-neon-blue transition-colors" size={18} />
                                    <input
                                        type="text"
                                        value={query}
                                        disabled={status === 'processing'}
                                        onChange={(e) => setQuery(e.target.value)}
                                        placeholder="e.g. Amazon Biomass Conservation Unit 4"
                                        className="w-full bg-black border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white placeholder-gray-700 focus:border-neon-blue/50 focus:bg-white/5 outline-none transition-all font-medium disabled:opacity-50"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Latitude</label>
                                    <div className="relative group/input">
                                        <MapPin className="absolute left-4 top-4 text-gray-600 group-focus-within/input:text-neon-blue transition-colors" size={18} />
                                        <input
                                            type="text"
                                            value={lat}
                                            disabled={status === 'processing'}
                                            onChange={(e) => setLat(e.target.value)}
                                            placeholder="-3.46"
                                            className="w-full bg-black border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white font-mono focus:border-neon-blue/50 focus:bg-white/5 outline-none transition-all disabled:opacity-50"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Longitude</label>
                                    <div className="relative group/input">
                                        <Globe className="absolute left-4 top-4 text-gray-600 group-focus-within/input:text-neon-blue transition-colors" size={18} />
                                        <input
                                            type="text"
                                            value={lon}
                                            disabled={status === 'processing'}
                                            onChange={(e) => setLon(e.target.value)}
                                            placeholder="-62.21"
                                            className="w-full bg-black border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white font-mono focus:border-neon-blue/50 focus:bg-white/5 outline-none transition-all disabled:opacity-50"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-8 border-t border-white/5">
                            <button
                                onClick={handleVerify}
                                disabled={status === 'processing'}
                                className="relative w-full overflow-hidden group/btn bg-white text-black font-black text-lg py-5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99]"
                            >
                                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-neon-blue via-cyan-400 to-neon-blue opacity-0 group-hover/btn:opacity-20 transition-opacity" />
                                {status === 'processing' ? (
                                    <span className="flex items-center justify-center gap-3">
                                        <Loader2 className="animate-spin" size={20} /> INITIALIZING...
                                    </span>
                                ) : (
                                    <span className="flex items-center justify-center gap-3">
                                        <Scan size={20} /> INITIATE AUDIT PROTOCOL
                                    </span>
                                )}
                            </button>
                        </div>
                    </motion.div>

                    {/* Quick Stats / Info */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="grid grid-cols-2 gap-4"
                    >
                        <div className="bg-[#0a0a0a] border border-white/10 rounded-xl p-4 flex flex-col justify-between h-32">
                            <Satellite className="text-gray-600 mb-2" size={20} />
                            <div>
                                <div className="text-2xl font-bold text-white">Sentinel-2</div>
                                <div className="text-[10px] uppercase text-gray-500 font-bold">Optical Satellite</div>
                            </div>
                        </div>
                        <div className="bg-[#0a0a0a] border border-white/10 rounded-xl p-4 flex flex-col justify-between h-32">
                            <Cpu className="text-gray-600 mb-2" size={20} />
                            <div>
                                <div className="text-2xl font-bold text-white">Deep Research</div>
                                <div className="text-[10px] uppercase text-gray-500 font-bold">Autonomous Agent</div>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* RIGHT COLUMN: HOLOGRAPHIC OUTPUT */}
                <div className="lg:col-span-7 relative h-full min-h-[500px]">
                    <AnimatePresence mode="wait">

                        {/* IDLE STATE */}
                        {status === 'idle' && (
                            <motion.div
                                key="idle"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, filter: 'blur(10px)' }}
                                className="absolute inset-0 flex flex-col items-center justify-center text-center opacity-30"
                            >
                                <div className="w-64 h-64 border border-white/10 rounded-full flex items-center justify-center mb-8 relative animate-spin-slow-reverse">
                                    <div className="w-[90%] h-[90%] border border-dashed border-white/20 rounded-full animate-spin-slow" />
                                    <Globe size={64} className="text-white/20" />
                                </div>
                                <h3 className="text-xl font-mono text-gray-500">WAITING FOR TARGET ACQUISITION...</h3>
                            </motion.div>
                        )}

                        {/* PROCESSING STATE */}
                        {status === 'processing' && (
                            <motion.div
                                key="processing"
                                initial={{ opacity: 0, x: 50 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -50 }}
                                className="absolute inset-0 bg-black/50 rounded-2xl border border-neon-blue/30 p-8 flex flex-col font-mono"
                            >
                                <div className="flex justify-between items-center mb-6 border-b border-neon-blue/20 pb-4">
                                    <span className="text-neon-blue font-bold flex items-center gap-2"><Terminal size={16} /> LIVE TERMINAL OUTPUT</span>
                                    <span className="text-xs text-neon-blue/50 animate-pulse">ENCRYPTED CONNECTION</span>
                                </div>
                                <div className="flex-1 overflow-y-auto space-y-2 text-sm">
                                    {logs.map((log, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="text-gray-300"
                                        >
                                            <span className="text-neon-blue mr-2">[{new Date().toLocaleTimeString()}]</span>
                                            {log}
                                        </motion.div>
                                    ))}
                                    <div className="h-4 w-2 bg-neon-blue animate-pulse inline-block ml-1" />
                                </div>
                            </motion.div>
                        )}

                        {/* RESULT STATE */}
                        {status === 'complete' && result && (
                            <motion.div
                                key="result"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="absolute inset-0 bg-[#0c0c0c] rounded-2xl border border-emerald-500/30 flex flex-col shadow-2xl overflow-hidden font-sans"
                            >
                                {/* Header Bar */}
                                <div className="bg-[#111] p-6 border-b border-white/5 flex justify-between items-center bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]">
                                    <div className="flex items-center gap-3">
                                        <div className="bg-emerald-500/20 p-2 rounded-lg">
                                            <ShieldCheck className="text-emerald-500" size={24} />
                                        </div>
                                        <div>
                                            <h2 className="text-lg font-bold text-white tracking-tight">AUDIT CERTIFICATE</h2>
                                            <div className="text-[10px] text-gray-400 font-mono flex gap-3">
                                                <span>ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}</span>
                                                <span className="text-gray-600">|</span>
                                                <span>{new Date().toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <div className="text-4xl font-black text-white leading-none tracking-tighter" style={{ textShadow: "0 0 20px rgba(16, 185, 129, 0.5)" }}>
                                            {result.compliance_score}
                                        </div>
                                        <div className="text-[10px] uppercase text-emerald-500 font-bold tracking-widest">Trust Score</div>
                                    </div>
                                </div>

                                {/* Scrollable Content */}
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8">

                                    {/* Abstract */}
                                    <div className="mb-8">
                                        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                                            <FileText size={14} /> Mission Abstract
                                        </h3>
                                        <h1 className="text-2xl font-bold text-white mb-2">{query}</h1>
                                        <div className="flex gap-2 mb-4">
                                            <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-mono text-gray-400 border border-white/5">LAT: {lat}</span>
                                            <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-mono text-gray-400 border border-white/5">LON: {lon}</span>
                                        </div>
                                    </div>

                                    {/* Artificial Intelligence Analysis */}
                                    <div className="mb-8 p-6 bg-[#151515] rounded-xl border border-white/5 relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-4 opacity-10">
                                            <Cpu size={64} />
                                        </div>
                                        <h3 className="text-xs font-bold text-neon-blue uppercase tracking-widest mb-4 flex items-center gap-2 border-b border-white/5 pb-2">
                                            <Terminal size={14} /> Agent Intelligence Report
                                        </h3>
                                        <div className="prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-headings:text-white prose-strong:text-white prose-ul:list-disc prose-li:marker:text-neon-blue">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {result.summary}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                </div>

                                {/* Footer Action */}
                                <div className="p-6 bg-[#111] border-t border-white/5 flex gap-4">
                                    <a
                                        href={result.pdf_url}
                                        target="_blank"
                                        download
                                        className="flex-1 bg-white text-black font-bold py-4 rounded-xl hover:bg-emerald-400 hover:scale-[1.01] transition-all flex items-center justify-center gap-3 shadow-lg group"
                                    >
                                        <Download size={18} className="group-hover:animate-bounce" />
                                        <span>DOWNLOAD SIGNED REPORT</span>
                                    </a>
                                    <button
                                        onClick={() => { setStatus('idle'); setQuery(''); setLogs([]); }}
                                        className="px-6 py-4 bg-white/5 text-gray-400 font-bold rounded-xl hover:bg-white/10 hover:text-white transition-colors text-xs uppercase tracking-widest flex items-center gap-2"
                                    >
                                        <Scan size={16} /> New Audit
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {/* ERROR STATE */}
                        {status === 'error' && (
                            <motion.div
                                key="error"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="absolute inset-0 flex flex-col items-center justify-center text-center p-8 border border-red-900/50 rounded-2xl bg-red-950/10"
                            >
                                <AlertTriangle className="text-red-500 mb-4" size={48} />
                                <h3 className="text-xl font-bold text-red-500 mb-2">VERIFICATION FAILED</h3>
                                <p className="text-gray-400 mb-6">{errorMessage || "The system could not establish a connection with the audit node."}</p>
                                <button
                                    onClick={() => setStatus('idle')}
                                    className="px-6 py-2 bg-red-500/20 text-red-500 border border-red-500/50 rounded-lg hover:bg-red-500 hover:text-white transition-all"
                                >
                                    RETRY
                                </button>
                            </motion.div>
                        )}

                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default AuditPage;
