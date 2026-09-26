import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Bot, ExternalLink } from 'lucide-react';
import { newsApi, NewsArticle } from '../services/newsApi';
import ChatMessage from './ChatMessage';

interface NewsChatModalProps {
    article: NewsArticle | null;
    isOpen: boolean;
    onClose: () => void;
}

export default function NewsChatModal({ article, isOpen, onClose }: NewsChatModalProps) {
    const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string }[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    // Get conversation ID from localStorage for this article
    const getStoredConversationId = (articleId: string): string | null => {
        try {
            const stored = localStorage.getItem(`article_chat_${articleId}`);
            return stored || null;
        } catch {
            return null;
        }
    };

    // Store conversation ID in localStorage
    const storeConversationId = (articleId: string, convId: string) => {
        try {
            localStorage.setItem(`article_chat_${articleId}`, convId);
        } catch {
            // Ignore localStorage errors
        }
    };

    useEffect(() => {
        if (isOpen && article) {
            setLoadingHistory(true);
            setInput('');
            
            // Get stored conversation ID for this article
            const storedConvId = getStoredConversationId(article.id);
            
            if (storedConvId) {
                // Load existing conversation history
                newsApi.getConversationHistory(article.id, storedConvId)
                    .then((data) => {
                        if (data.messages && data.messages.length > 0) {
                            // Convert API format to component format
                            const formattedMessages = data.messages.map((msg: any) => ({
                                role: msg.role as 'user' | 'assistant',
                                content: msg.content
                            }));
                            setMessages(formattedMessages);
                            setConversationId(data.conversation_id);
                        } else {
                            // No history, show welcome message
                            setMessages([
                                {
                                    role: 'assistant',
                                    content: `Hello! I can help you understand this article: **"${article.title}"** from ${article.source}.\n\nAsk me anything about the article's content, key points, implications, or related topics.`
                                }
                            ]);
                            setConversationId(storedConvId);
                        }
                    })
                    .catch((err) => {
                        console.error('Error loading conversation history:', err);
                        // Show welcome message on error
                        setMessages([
                            {
                                role: 'assistant',
                                content: `Hello! I can help you understand this article: **"${article.title}"** from ${article.source}.\n\nAsk me anything about the article's content, key points, implications, or related topics.`
                            }
                        ]);
                        setConversationId(storedConvId);
                    })
                    .finally(() => {
                        setLoadingHistory(false);
                    });
            } else {
                // New conversation - show welcome message
                setMessages([
                    {
                        role: 'assistant',
                        content: `Hello! I can help you understand this article: **"${article.title}"** from ${article.source}.\n\nAsk me anything about the article's content, key points, implications, or related topics.`
                    }
                ]);
                setConversationId(null);
                setLoadingHistory(false);
            }
        } else if (!isOpen) {
            // Don't reset messages when closing - keep them for next open
            // Only reset input
            setInput('');
        }
    }, [isOpen, article]);

    const handleSend = async () => {
        if (!input.trim() || !article || loading) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setLoading(true);

        try {
            const response = await newsApi.chatAboutArticle(article.id, {
                message: userMessage,
                article_id: article.id,
                conversation_id: conversationId || undefined
            });

            // Update conversation ID if provided and store it
            if (response.conversation_id) {
                setConversationId(response.conversation_id);
                if (article) {
                    storeConversationId(article.id, response.conversation_id);
                }
            }

            // Add assistant response
            setMessages(prev => [...prev, { role: 'assistant', content: response.answer }]);
        } catch (err) {
            console.error('Error chatting about article:', err);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!article) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="glass-card border border-white/20 rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
                            {/* Header */}
                            <div className="bg-gradient-to-r from-neon-blue/10 to-purple-500/10 p-6 border-b border-white/10">
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className="w-10 h-10 rounded-full bg-neon-blue/20 flex items-center justify-center border border-neon-blue/50">
                                                <Bot size={20} className="text-neon-blue" />
                                            </div>
                                            <div>
                                                <h2 className="text-xl font-bold font-display text-white">
                                                    Chat about Article
                                                </h2>
                                                <p className="text-xs text-green-400 flex items-center gap-1 mt-1">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Online
                                                </p>
                                            </div>
                                        </div>
                                        <div className="mt-3 p-3 bg-black/30 rounded-lg border border-white/5">
                                            <h3 className="text-sm font-bold text-white mb-1 line-clamp-2">
                                                {article.title}
                                            </h3>
                                            <div className="flex items-center gap-2 text-xs text-gray-400">
                                                <span>{article.source}</span>
                                                <span>�</span>
                                                <span>{new Date(article.published_at).toLocaleDateString()}</span>
                                                <a
                                                    href={article.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="ml-auto flex items-center gap-1 text-neon-blue hover:text-cyan-400 transition-colors"
                                                >
                                                    Read full article
                                                    <ExternalLink size={12} />
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                                    >
                                        <X size={18} />
                                    </button>
                                </div>
                            </div>

                            {/* Messages Area */}
                            <div
                                ref={scrollRef}
                                className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar bg-black/20"
                            >
                                {loadingHistory ? (
                                    <div className="flex justify-center items-center h-full">
                                        <div className="text-gray-400 text-sm">Loading conversation history...</div>
                                    </div>
                                ) : (
                                    <>
                                        {messages.map((msg, i) => (
                                            <ChatMessage
                                                key={`${msg.role}-${i}-${msg.content.substring(0, 20)}`}
                                                role={msg.role}
                                                content={msg.content}
                                                agentColor="cyan"
                                            />
                                        ))}
                                        {loading && (
                                            <div className="flex justify-start">
                                                <div className="bg-white/5 p-3 rounded-2xl rounded-tl-none flex gap-1 border border-white/10">
                                                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>

                            {/* Input Area */}
                            <div className="p-4 bg-black/30 border-t border-white/10">
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={handleKeyPress}
                                        placeholder="Ask about the article's content, key points, or implications..."
                                        className="w-full bg-black/50 border border-white/10 rounded-xl py-3 pl-4 pr-12 text-sm text-white placeholder-gray-500 focus:border-neon-blue/50 outline-none transition-colors"
                                        disabled={loading}
                                    />
                                    <button
                                        onClick={handleSend}
                                        disabled={loading || !input.trim()}
                                        className="absolute right-2 top-2 p-2 bg-neon-blue rounded-lg text-black hover:bg-cyan-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Send size={16} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
