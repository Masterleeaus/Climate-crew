import { motion } from 'framer-motion';
import * as Icons from 'lucide-react';
import { AgentMetadata } from '../services/agents.api';

interface AgentCardProps {
    agent: AgentMetadata;
    onClick: () => void;
}

const colorClasses: Record<string, { bg: string; border: string; badge: string }> = {
    cyan: { bg: 'from-cyan-500/10 to-cyan-600/5', border: 'border-cyan-500/30', badge: 'bg-cyan-500/20 text-cyan-300' },
    orange: { bg: 'from-orange-500/10 to-orange-600/5', border: 'border-orange-500/30', badge: 'bg-orange-500/20 text-orange-300' },
    blue: { bg: 'from-blue-500/10 to-blue-600/5', border: 'border-blue-500/30', badge: 'bg-blue-500/20 text-blue-300' },
    green: { bg: 'from-green-500/10 to-green-600/5', border: 'border-green-500/30', badge: 'bg-green-500/20 text-green-300' },
    emerald: { bg: 'from-emerald-500/10 to-emerald-600/5', border: 'border-emerald-500/30', badge: 'bg-emerald-500/20 text-emerald-300' },
    purple: { bg: 'from-purple-500/10 to-purple-600/5', border: 'border-purple-500/30', badge: 'bg-purple-500/20 text-purple-300' },
    gray: { bg: 'from-gray-500/10 to-gray-600/5', border: 'border-gray-500/30', badge: 'bg-gray-500/20 text-gray-300' },
    red: { bg: 'from-red-500/10 to-red-600/5', border: 'border-red-500/30', badge: 'bg-red-500/20 text-red-300' },
    teal: { bg: 'from-teal-500/10 to-teal-600/5', border: 'border-teal-500/30', badge: 'bg-teal-500/20 text-teal-300' },
    indigo: { bg: 'from-indigo-500/10 to-indigo-600/5', border: 'border-indigo-500/30', badge: 'bg-indigo-500/20 text-indigo-300' },
    violet: { bg: 'from-violet-500/10 to-violet-600/5', border: 'border-violet-500/30', badge: 'bg-violet-500/20 text-violet-300' },
};

export default function AgentCard({ agent, onClick }: AgentCardProps) {
    const Icon = (Icons as any)[agent.icon] || Icons.Bot;
    const colors = colorClasses[agent.color] || colorClasses.cyan;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -8, scale: 1.02 }}
            transition={{ duration: 0.3 }}
            onClick={onClick}
            className={`
        relative overflow-hidden cursor-pointer
        bg-gradient-to-br ${colors.bg}
        border ${colors.border}
        rounded-xl p-6
        backdrop-blur-sm
        hover:shadow-2xl hover:shadow-${agent.color}-500/20
        transition-all duration-300
        group
      `}
        >
            {/* Background gradient effect */}
            <div className={`absolute inset-0 bg-gradient-to-br ${colors.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

            {/* Content */}
            <div className="relative z-10">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-lg bg-gradient-to-br ${colors.bg} border ${colors.border}`}>
                        <Icon className={`w-6 h-6 text-${agent.color}-400`} />
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${colors.badge}`}>
                        {agent.category}
                    </span>
                </div>

                {/* Name */}
                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-${agent.color}-300 transition-colors">
                    {agent.name}
                </h3>

                {/* Description */}
                <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                    {agent.description}
                </p>

                {/* Capabilities */}
                <div className="space-y-1">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Key Capabilities</p>
                    <ul className="space-y-1">
                        {agent.capabilities.slice(0, 3).map((capability, idx) => (
                            <li key={idx} className="text-xs text-gray-400 flex items-center">
                                <span className={`w-1 h-1 rounded-full bg-${agent.color}-400 mr-2`} />
                                {capability}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Hover indicator */}
                <div className="mt-4 flex items-center text-xs text-gray-500 group-hover:text-${agent.color}-400 transition-colors">
                    <span>Click to chat</span>
                    <Icons.ArrowRight className="w-3 h-3 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
            </div>
        </motion.div>
    );
}
