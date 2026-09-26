import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import AgentCard from '../components/AgentCard';
import ChatMessage from '../components/ChatMessage';
import AgentSelector from '../components/AgentSelector';
import { AgentMetadata, fetchAgentMetadata, chatWithAgent } from '../services/agents.api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function AgentUplinkPage() {
    const [agents, setAgents] = useState<AgentMetadata[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<AgentMetadata | null>(null);
    const [messages, setMessages] = useState<Record<string, Message[]>>({});
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingAgents, setLoadingAgents] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAgentSelector, setShowAgentSelector] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Load agents on mount
    useEffect(() => {
        loadAgents();
    }, []);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, selectedAgent]);

    const loadAgents = async () => {
        try {
            setLoadingAgents(true);
            const agentData = await fetchAgentMetadata();
            setAgents(agentData);
        } catch (err) {
            setError('Failed to load agents. Please try again.');
            console.error(err);
        } finally {
            setLoadingAgents(false);
        }
    };

    const handleAgentSelect = (agent: AgentMetadata) => {
        setSelectedAgent(agent);
        setShowAgentSelector(false);
        setInput('');
        setError(null);

        // Initialize message history for new agent if not exists
        if (!messages[agent.id]) {
            setMessages(prev => ({
                ...prev,
                [agent.id]: []
            }));
        }
    };

    const handleBackToGrid = () => {
        setSelectedAgent(null);
        setInput('');
        setShowAgentSelector(false);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setInput(value);

        // Show agent selector if user types "/"
        if (value === '/') {
            setShowAgentSelector(true);
        } else if (!value.startsWith('/')) {
            setShowAgentSelector(false);
        }
    };

    const handleSendMessage = async () => {
        if (!input.trim() || !selectedAgent || loading) return;
        if (input === '/') return; // Don't send just the slash

        const userMessage = input.trim();
        setInput('');
        setShowAgentSelector(false);
        setError(null);

        // Add user message to chat
        const newMessages = [
            ...(messages[selectedAgent.id] || []),
            { role: 'user' as const, content: userMessage }
        ];
        setMessages(prev => ({
            ...prev,
            [selectedAgent.id]: newMessages
        }));

        // Get agent response
        setLoading(true);
        try {
            const response = await chatWithAgent(selectedAgent.id, userMessage);
            setMessages(prev => ({
                ...prev,
                [selectedAgent.id]: [
                    ...prev[selectedAgent.id],
                    { role: 'assistant' as const, content: response }
                ]
            }));
        } catch (err) {
            setError('Failed to get response from agent. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const currentMessages = selectedAgent ? messages[selectedAgent.id] || [] : [];

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
            <AnimatePresence mode="wait">
                {!selectedAgent ? (
                    // Agent Grid View
                    <motion.div
                        key="grid"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="container mx-auto px-6 py-8"
                    >
                        {/* Header */}
                        <div className="mb-8">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-600/10 border border-cyan-500/30">
                                    <Sparkles className="w-8 h-8 text-cyan-400" />
                                </div>
                                <div>
                                    <h1 className="text-4xl font-bold text-white">Agent Uplink</h1>
                                    <p className="text-gray-400 mt-1">Connect with specialized climate and analytics agents</p>
                                </div>
                            </div>
                        </div>

                        {/* Loading State */}
                        {loadingAgents && (
                            <div className="flex items-center justify-center py-20">
                                <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                            </div>
                        )}

                        {/* Error State */}
                        {error && !loadingAgents && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
                                <div className="flex items-center gap-2 text-red-400">
                                    <AlertCircle className="w-5 h-5" />
                                    <p>{error}</p>
                                </div>
                            </div>
                        )}

                        {/* Agent Cards */}
                        {!loadingAgents && agents.length > 0 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {agents.map((agent, idx) => (
                                    <motion.div
                                        key={agent.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                    >
                                        <AgentCard agent={agent} onClick={() => handleAgentSelect(agent)} />
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </motion.div>
                ) : (
                    // Chat View
                    <motion.div
                        key="chat"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col h-screen"
                    >
                        {/* Chat Header */}
                        <div className="bg-gray-900/80 backdrop-blur-xl border-b border-gray-800 px-6 py-4">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={handleBackToGrid}
                                    className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 text-gray-400" />
                                </button>
                                <div className={`p-2 rounded-lg bg-gradient-to-br from-${selectedAgent.color}-500/20 to-${selectedAgent.color}-600/10 border border-${selectedAgent.color}-500/30`}>
                                    <Sparkles className={`w-5 h-5 text-${selectedAgent.color}-400`} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">{selectedAgent.name}</h2>
                                    <p className="text-sm text-gray-400">{selectedAgent.description}</p>
                                </div>
                            </div>
                        </div>

                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                            {currentMessages.length === 0 ? (
                                <div className="flex items-center justify-center h-full">
                                    <div className="text-center">
                                        <Sparkles className={`w-16 h-16 text-${selectedAgent.color}-400 mx-auto mb-4 opacity-50`} />
                                        <h3 className="text-xl font-semibold text-gray-300 mb-2">
                                            Start a conversation
                                        </h3>
                                        <p className="text-gray-500 mb-4">
                                            Ask {selectedAgent.name} anything about {selectedAgent.category.toLowerCase()} analysis
                                        </p>
                                        <div className="text-sm text-gray-600 space-y-1">
                                            <p>💡 Tip: Type <code className="px-2 py-1 bg-gray-800 rounded text-cyan-400">/</code> to switch agents</p>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    {currentMessages.map((message, idx) => (
                                        <ChatMessage
                                            key={idx}
                                            role={message.role}
                                            content={message.content}
                                            agentColor={selectedAgent.color}
                                        />
                                    ))}
                                    {loading && (
                                        <div className="flex items-center gap-2 text-gray-400">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span className="text-sm">{selectedAgent.name} is thinking...</span>
                                        </div>
                                    )}
                                </>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Error Display */}
                        {error && (
                            <div className="mx-6 mb-2 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                                <div className="flex items-center gap-2 text-red-400 text-sm">
                                    <AlertCircle className="w-4 h-4" />
                                    <p>{error}</p>
                                </div>
                            </div>
                        )}

                        {/* Input Area */}
                        <div className="bg-gray-900/80 backdrop-blur-xl border-t border-gray-800 px-6 py-4">
                            <div className="relative">
                                {/* Agent Selector */}
                                <AgentSelector
                                    agents={agents}
                                    isOpen={showAgentSelector}
                                    onSelect={handleAgentSelect}
                                    onClose={() => setShowAgentSelector(false)}
                                    searchTerm={input.startsWith('/') ? input.slice(1) : ''}
                                />

                                {/* Input */}
                                <div className="flex gap-3">
                                    <input
                                        ref={inputRef}
                                        type="text"
                                        value={input}
                                        onChange={handleInputChange}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Type your message... (or / to switch agents)"
                                        disabled={loading}
                                        className="flex-1 bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                    />
                                    <button
                                        onClick={handleSendMessage}
                                        disabled={!input.trim() || loading || input === '/'}
                                        className={`
                      px-6 py-3 rounded-xl font-medium transition-all
                      ${input.trim() && input !== '/' && !loading
                                                ? `bg-gradient-to-r from-${selectedAgent.color}-500 to-${selectedAgent.color}-600 hover:from-${selectedAgent.color}-600 hover:to-${selectedAgent.color}-700 text-white shadow-lg shadow-${selectedAgent.color}-500/30`
                                                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                            }
                    `}
                                    >
                                        {loading ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <Send className="w-5 h-5" />
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
