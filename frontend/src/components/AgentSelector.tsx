import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Icons from 'lucide-react';
import { AgentMetadata } from '../services/agents.api';

interface AgentSelectorProps {
    agents: AgentMetadata[];
    isOpen: boolean;
    onSelect: (agent: AgentMetadata) => void;
    onClose: () => void;
    searchTerm: string;
}

export default function AgentSelector({
    agents,
    isOpen,
    onSelect,
    onClose,
    searchTerm
}: AgentSelectorProps) {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [filteredAgents, setFilteredAgents] = useState(agents);
    const selectorRef = useRef<HTMLDivElement>(null);

    // Filter agents based on search term
    useEffect(() => {
        const search = searchTerm.toLowerCase();
        const filtered = agents.filter(agent =>
            agent.name.toLowerCase().includes(search) ||
            agent.description.toLowerCase().includes(search) ||
            agent.category.toLowerCase().includes(search)
        );
        setFilteredAgents(filtered);
        setSelectedIndex(0);
    }, [searchTerm, agents]);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filteredAgents.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (filteredAgents[selectedIndex]) {
                    onSelect(filteredAgents[selectedIndex]);
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, filteredAgents, selectedIndex, onSelect, onClose]);

    // Group agents by category
    const groupedAgents = filteredAgents.reduce((acc, agent) => {
        if (!acc[agent.category]) {
            acc[agent.category] = [];
        }
        acc[agent.category].push(agent);
        return acc;
    }, {} as Record<string, AgentMetadata[]>);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                ref={selectorRef}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute bottom-full left-0 right-0 mb-2 bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden z-50"
                style={{ maxHeight: '400px' }}
            >
                {/* Header */}
                <div className="px-4 py-3 border-b border-gray-700/50 bg-gray-800/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icons.Sparkles className="w-4 h-4 text-cyan-400" />
                            <span className="text-sm font-medium text-gray-300">Select Agent</span>
                        </div>
                        <span className="text-xs text-gray-500">
                            {filteredAgents.length} available
                        </span>
                    </div>
                </div>

                {/* Agent list */}
                <div className="overflow-y-auto" style={{ maxHeight: '320px' }}>
                    {Object.entries(groupedAgents).map(([category, categoryAgents]) => (
                        <div key={category}>
                            {/* Category header */}
                            <div className="px-4 py-2 bg-gray-800/30 sticky top-0 z-10">
                                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    {category}
                                </span>
                            </div>

                            {/* Agents in category */}
                            {categoryAgents.map((agent) => {
                                const globalIndex = filteredAgents.indexOf(agent);
                                const isSelected = globalIndex === selectedIndex;
                                const Icon = (Icons as any)[agent.icon] || Icons.Bot;

                                return (
                                    <motion.div
                                        key={agent.id}
                                        whileHover={{ x: 4 }}
                                        onClick={() => onSelect(agent)}
                                        className={`
                      px-4 py-3 cursor-pointer transition-colors
                      ${isSelected
                                                ? `bg-${agent.color}-500/10 border-l-2 border-${agent.color}-500`
                                                : 'hover:bg-gray-800/30 border-l-2 border-transparent'
                                            }
                    `}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`p-2 rounded-lg bg-${agent.color}-500/10 border border-${agent.color}-500/20 flex-shrink-0`}>
                                                <Icon className={`w-4 h-4 text-${agent.color}-400`} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h4 className="text-sm font-medium text-white mb-0.5">
                                                    {agent.name}
                                                </h4>
                                                <p className="text-xs text-gray-400 line-clamp-1">
                                                    {agent.description}
                                                </p>
                                            </div>
                                            {isSelected && (
                                                <Icons.Check className={`w-4 h-4 text-${agent.color}-400 flex-shrink-0`} />
                                            )}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    ))}

                    {filteredAgents.length === 0 && (
                        <div className="px-4 py-8 text-center">
                            <Icons.Search className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                            <p className="text-sm text-gray-500">No agents found</p>
                        </div>
                    )}
                </div>

                {/* Footer hint */}
                <div className="px-4 py-2 border-t border-gray-700/50 bg-gray-800/30">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>↑↓ Navigate</span>
                        <span>↵ Select</span>
                        <span>ESC Close</span>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
