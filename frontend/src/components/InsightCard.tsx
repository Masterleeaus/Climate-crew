import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, AlertTriangle, Loader2 } from 'lucide-react';

interface InsightCardProps {
    agentId: string;
    status: 'pending' | 'success' | 'error';
    data?: string;
    delay?: number;
}

const InsightCard: React.FC<InsightCardProps> = ({ agentId, status, data, delay = 0 }) => {

    // Format agent name (e.g., "air_quality" -> "Air Quality")
    const title = agentId.replace(/_/g, ' ').toUpperCase();

    // Icon selection
    const getIcon = () => {
        if (status === 'pending') return <Loader2 className="w-5 h-5 animate-spin text-neon-blue" />;
        if (status === 'error') return <AlertTriangle className="w-5 h-5 text-red-500" />;
        return <Bot className="w-5 h-5 text-neon-green" />;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: delay }}
            className={`relative group glass-card flex flex-col h-72 min-w-[320px] overflow-hidden transition-all hover:-translate-y-1 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)] ${status === 'error' ? 'border-red-500/30 bg-red-900/10' : 'border-white/10 hover:border-neon-blue/30'}`}
        >
            {/* Header/Banner */}
            <div className={`h-1 w-full ${status === 'success' ? 'bg-gradient-to-r from-neon-green to-emerald-600' : status === 'error' ? 'bg-red-500' : 'bg-neon-blue animate-pulse'}`} />

            <div className="p-5 flex flex-col h-full">
                {/* Title Section */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${status === 'success' ? 'bg-neon-green/10 text-neon-green' : 'bg-white/5 text-gray-400'}`}>
                            {getIcon()}
                        </div>
                        <div>
                            <h3 className="text-xs font-black tracking-[0.2em] text-gray-400 uppercase">{title}</h3>
                            <p className="text-[10px] text-gray-500 font-mono">ID: {agentId.substring(0, 4).toUpperCase()}</p>
                        </div>
                    </div>
                    {status === 'success' && (
                        <span className="text-[10px] bg-neon-green/10 text-neon-green px-2 py-0.5 rounded border border-neon-green/20">ONLINE</span>
                    )}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar relative">
                    {status === 'pending' ? (
                        <div className="space-y-3 mt-2 opacity-50">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-2 bg-white/10 rounded animate-pulse" style={{ width: `${Math.random() * 40 + 60}%` }} />
                            ))}
                            <div className="flex items-center gap-2 mt-4 text-xs text-neon-blue animate-pulse">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                <span>Analyzing satellite data...</span>
                            </div>
                        </div>
                    ) : status === 'error' ? (
                        <div className="flex flex-col items-center justify-center h-full text-center p-4">
                            <AlertTriangle className="w-8 h-8 text-red-500 mb-2 opacity-80" />
                            <p className="text-sm text-red-300">Connection Terminated</p>
                            <p className="text-xs text-red-400/50 mt-1">Agent failed to respond.</p>
                        </div>
                    ) : (
                        <div className="markdown-prose text-sm text-gray-200 leading-relaxed font-light">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    strong: ({ node, ...props }) => <span className="text-neon-blue font-semibold" {...props} />,
                                    a: ({ node, ...props }) => <a className="text-neon-purple underline decoration-dotted underline-offset-4 hover:text-white transition-colors" target="_blank" {...props} />,
                                    ul: ({ node, ...props }) => <ul className="list-disc list-inside pl-1 space-y-1 my-2 text-gray-300" {...props} />,
                                    h3: ({ node, ...props }) => <h3 className="text-white font-medium uppercase tracking-wider text-xs mt-4 mb-2 border-b border-white/10 pb-1" {...props} />,
                                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />
                                }}
                            >
                                {data?.replace(/"/g, '') || ''}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

export default InsightCard;
