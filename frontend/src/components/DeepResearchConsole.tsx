import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, FileText, Terminal, ArrowRight } from 'lucide-react';

const DeepResearchConsole = ({ onClose }: { onClose: () => void }) => {
    const [topic, setTopic] = useState('');
    const [isResearching, setIsResearching] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);

    const handleResearch = () => {
        setIsResearching(true);
        setLogs(["Initializing Deep Research Agent...", "Connecting to Tavily API...", "Planning research strategy..."]);
        // Simulation of steps
        setTimeout(() => setLogs(prev => [...prev, "Searching for: " + topic]), 1500);
        setTimeout(() => setLogs(prev => [...prev, "Found 12 relevant sources.", "Analyzing content..."]), 3000);
        setTimeout(() => setLogs(prev => [...prev, "Generating final report..."]), 5000);
        setTimeout(() => {
            setIsResearching(false);
            setLogs(prev => [...prev, "Research Complete."]);
        }, 7000);
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-10">
            <button onClick={onClose} className="absolute top-6 right-6 text-white/50 hover:text-white">CLOSE</button>

            <div className="w-full max-w-5xl grid grid-cols-2 gap-8 h-[80vh]">
                {/* Left: Control & Output */}
                <div className="flex flex-col gap-6">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Deep <span className="text-neon-purple">Research</span></h1>
                        <p className="text-gray-400">Autonomous multi-step research pipeline.</p>
                    </div>

                    <div className="glass-card p-6">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-2">Research Topic</label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                placeholder="e.g., Impact of sea level rise on Indonesian palm oil..."
                                className="flex-1 bg-black/40 border border-white/10 rounded px-4 py-3 text-white focus:border-neon-purple focus:outline-none transition-colors"
                            />
                            <button
                                onClick={handleResearch}
                                disabled={!topic || isResearching}
                                className="bg-neon-purple/20 border border-neon-purple text-neon-purple px-6 py-2 rounded font-bold hover:bg-neon-purple hover:text-black transition-all disabled:opacity-50 flex items-center gap-2"
                            >
                                {isResearching ? 'RUNNING...' : 'START'} <ArrowRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 glass-card p-6 font-mono text-sm overflow-hidden flex flex-col">
                        <div className="flex items-center gap-2 text-gray-400 mb-4 pb-2 border-b border-white/10">
                            <Terminal className="w-4 h-4" />
                            <span>Execution Logs</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2 text-green-400/80 custom-scrollbar">
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                >
                                    <span className="text-gray-600 mr-2">[{new Date().toLocaleTimeString()}]</span>
                                    {log}
                                </motion.div>
                            ))}
                            {isResearching && <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }} className="w-2 h-4 bg-green-500/50 inline-block align-middle ml-1" />}
                        </div>
                    </div>
                </div>

                {/* Right: Report Preview */}
                <div className="glass-card p-8 flex flex-col border-neon-purple/30 bg-gradient-to-br from-glass-100 to-neon-purple/5">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-neon-purple/20 flex items-center justify-center">
                                <FileText className="w-5 h-5 text-neon-purple" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white">Generated Report</h3>
                                <p className="text-xs text-gray-400">PDF Output Preview</p>
                            </div>
                        </div>
                        {logs.includes("Research Complete.") && (
                            <button className="text-xs bg-white text-black px-3 py-1 rounded font-bold hover:bg-gray-200">
                                DOWNLOAD PDF
                            </button>
                        )}
                    </div>

                    <div className="flex-1 bg-white/5 rounded-lg p-8 relative overflow-hidden">
                        {!logs.includes("Research Complete.") ? (
                            <div className="absolute inset-0 flex items-center justify-center flex-col gap-4 text-gray-500">
                                <Search className="w-12 h-12 opacity-20" />
                                <p>Waiting for research data...</p>
                            </div>
                        ) : (
                            <div className="prose prose-invert prose-sm">
                                <h1>Research Report: {topic}</h1>
                                <p className="lead">Executive summary generated by DeepResearchAgent.</p>
                                <hr className="border-white/10" />
                                <h3>Key Findings</h3>
                                <ul>
                                    <li>Significant correlation found between variable A and B.</li>
                                    <li>Projected impact suggests a 15% increase by 2030.</li>
                                </ul>
                                <h3>Methodology</h3>
                                <p>Analyzed 150+ sources using iterative search refinement.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeepResearchConsole;
