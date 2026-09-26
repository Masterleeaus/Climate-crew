import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    agentColor?: string;
}

export default function ChatMessage({ role, content, agentColor = 'cyan' }: ChatMessageProps) {
    const isUser = role === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex gap-3 mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            {!isUser && (
                <div className={`flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-${agentColor}-500/20 to-${agentColor}-600/10 border border-${agentColor}-500/30 flex items-center justify-center`}>
                    <Bot className={`w-4 h-4 text-${agentColor}-400`} />
                </div>
            )}

            <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
                <div
                    className={`
            rounded-2xl px-4 py-3
            ${isUser
                            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                            : `bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 text-gray-100`
                        }
          `}
                >
                    {isUser ? (
                        <p className="text-sm leading-relaxed">{content}</p>
                    ) : (
                        <div className="prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    // Customize markdown rendering
                                    h1: ({ node, ...props }) => <h1 className="text-xl font-bold mb-2 text-white" {...props} />,
                                    h2: ({ node, ...props }) => <h2 className="text-lg font-bold mb-2 text-white" {...props} />,
                                    h3: ({ node, ...props }) => <h3 className="text-base font-bold mb-1 text-white" {...props} />,
                                    p: ({ node, ...props }) => <p className="mb-2 leading-relaxed text-gray-200" {...props} />,
                                    ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-200" {...props} />,
                                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-200" {...props} />,
                                    li: ({ node, ...props }) => <li className="text-sm text-gray-200" {...props} />,
                                    code: ({ node, inline, ...props }: any) =>
                                        inline ? (
                                            <code className={`px-1.5 py-0.5 rounded bg-${agentColor}-500/20 text-${agentColor}-300 font-mono text-xs`} {...props} />
                                        ) : (
                                            <code className="block p-3 rounded-lg bg-black/40 border border-gray-700 text-gray-300 font-mono text-xs overflow-x-auto mb-2" {...props} />
                                        ),
                                    pre: ({ node, ...props }) => <pre className="mb-2 overflow-x-auto" {...props} />,
                                    blockquote: ({ node, ...props }) => (
                                        <blockquote className={`border-l-4 border-${agentColor}-500/50 pl-4 italic text-gray-300 mb-2`} {...props} />
                                    ),
                                    a: ({ node, ...props }) => (
                                        <a className={`text-${agentColor}-400 hover:text-${agentColor}-300 underline`} target="_blank" rel="noopener noreferrer" {...props} />
                                    ),
                                    table: ({ node, ...props }) => (
                                        <div className="overflow-x-auto mb-2">
                                            <table className="min-w-full border border-gray-700 rounded-lg" {...props} />
                                        </div>
                                    ),
                                    thead: ({ node, ...props }) => <thead className="bg-gray-800/50" {...props} />,
                                    th: ({ node, ...props }) => <th className="px-3 py-2 text-left text-xs font-semibold text-gray-300 border-b border-gray-700" {...props} />,
                                    td: ({ node, ...props }) => <td className="px-3 py-2 text-sm text-gray-200 border-b border-gray-800" {...props} />,
                                    strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                                    em: ({ node, ...props }) => <em className="italic text-gray-300" {...props} />,
                                }}
                            >
                                {content}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>

            {isUser && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 flex items-center justify-center">
                    <User className="w-4 h-4 text-blue-400" />
                </div>
            )}
        </motion.div>
    );
}
