import React, { useState, useRef, useEffect } from 'react';
import { Microscope, ArrowRight, BookOpen, Globe, Layers, Cpu, AlertCircle, Download, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// Types
interface Source {
    title: string;
    url: string;
    type: 'web' | 'file' | 'db';
}

interface ResearchResult {
    report: string;
    sources: Source[];
}

const STEPS = [
    'Initializing deep reasoning engine...',
    'Decomposing query into sub-problems...',
    'Traversing knowledge graph...',
    'Cross-referencing academic sources...',
    'Synthesizing final intelligence report...'
];

const DeepResearchPage: React.FC = () => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ResearchResult | null>(null);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);

    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const reportRef = useRef<HTMLDivElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [query]);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setResult(null);
        setCurrentStepIndex(0);

        // UX Simulation
        let stepIdx = 0;
        const interval = setInterval(() => {
            if (stepIdx < STEPS.length - 1) {
                stepIdx++;
                setCurrentStepIndex(stepIdx);
            }
        }, 9000);

        try {
            const res = await fetch('http://localhost:8000/deep-research/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            setResult(data);
        } catch (err) {
            console.error(err);
        } finally {
            clearInterval(interval);
            setLoading(false);
            setCurrentStepIndex(STEPS.length - 1);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    const handleExportPDF = async () => {
        if (!reportRef.current) return;
        const downloadBtn = document.getElementById('download-pdf-btn');
        if (downloadBtn) downloadBtn.innerText = 'Generating...';

        try {
            const element = reportRef.current;
            const canvas = await html2canvas(element, {
                scale: 2,
                backgroundColor: '#ffffff',
                ignoreElements: (element) => element.classList.contains('no-print'),
                onclone: (clonedDoc) => {
                    const clonedElement = clonedDoc.getElementById('report-content');
                    if (clonedElement) {
                        clonedElement.style.color = '#000000';
                        clonedElement.style.background = '#ffffff';
                        clonedElement.style.padding = '40px';
                        const textElements = clonedElement.querySelectorAll('*');
                        textElements.forEach((el) => {
                            if (el instanceof HTMLElement) {
                                el.style.color = '#000000';
                                el.style.borderColor = '#cccccc';
                            }
                        });
                        const links = clonedElement.querySelectorAll('a');
                        links.forEach((el) => el.style.color = '#0066cc');
                    }
                }
            });

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();
            const imgHeight = (canvas.height * pdfWidth) / canvas.width;

            let heightLeft = imgHeight;
            let position = 0;

            pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
            heightLeft -= pdfHeight;

            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
                heightLeft -= pdfHeight;
            }

            pdf.save(`research-report-${Date.now()}.pdf`);
        } catch (error) {
            console.error("PDF Generation failed", error);
        } finally {
            if (downloadBtn) downloadBtn.innerText = 'Export PDF';
        }
    };

    // Compact Header (Result Mode)
    if (result || loading) {
        return (
            <div className="w-full h-full flex flex-col items-center pt-6 px-4 pb-20 max-w-[1600px] mx-auto overflow-y-auto custom-scrollbar">

                {/* Compact Search Bar */}
                <div className="w-full mb-8 sticky top-0 z-50 bg-[#000000]/80 backdrop-blur-xl py-4 border-b border-white/5 no-print">
                    <div className="relative group max-w-3xl mx-auto">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-neon-blue/30 to-purple-600/30 rounded-full opacity-50 blur"></div>
                        <div className="relative flex items-center bg-[#111] rounded-full border border-white/10 px-4 py-2">
                            <p className="flex-1 bg-transparent text-gray-300 truncate font-medium outline-none px-2 text-sm">{query}</p>
                            <div className="h-4 w-[1px] bg-white/10 mx-2"></div>
                            {/* Small status indicator in bar */}
                            <div className="flex items-center gap-2 text-[10px] text-neon-blue font-bold tracking-wider uppercase whitespace-nowrap">
                                {loading ? (
                                    <span className="animate-pulse flex items-center gap-1"><Cpu size={10} /> Processing...</span>
                                ) : (
                                    <span>Done</span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Research Progress Overlay - Only when Loading */}
                {loading && (
                    <div className="w-full max-w-2xl mx-auto mb-10 bg-[#111] border border-neon-blue/30 rounded-xl p-6 shadow-[0_0_30px_rgba(0,243,255,0.1)] animate-fade-in">
                        <div className="flex items-center gap-3 mb-4">
                            <Cpu className="text-neon-blue animate-pulse" size={20} />
                            <h3 className="text-lg font-display font-bold text-white">Neural Reasoning Engine</h3>
                        </div>
                        <div className="space-y-3">
                            {STEPS.map((s, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                    {idx < currentStepIndex ? (
                                        <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/50 text-green-500">
                                            <Check size={12} />
                                        </div>
                                    ) : idx === currentStepIndex ? (
                                        <div className="w-5 h-5 rounded-full border-2 border-neon-blue border-t-transparent animate-spin"></div>
                                    ) : (
                                        <div className="w-5 h-5 rounded-full border border-white/10 bg-white/5"></div>
                                    )}
                                    <span className={`text-sm font-mono ${idx === currentStepIndex ? 'text-neon-blue font-bold' : idx < currentStepIndex ? 'text-gray-400' : 'text-gray-600'}`}>
                                        {s}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Report Content - Wrapped for Ref */}
                {result && !loading && (
                    <div id="report-content" ref={reportRef} className="w-full max-w-6xl space-y-10 animate-fade-in flex-1 mx-auto bg-[#0a0a0a] p-4 lg:p-10 rounded-xl">

                        {/* A. Sources Grid (Citations) */}
                        <div>
                            <h3 className="text-gray-400 text-xs font-bold mb-4 flex items-center gap-2 uppercase tracking-widest pl-1 font-display">
                                <Layers size={14} /> Sources
                            </h3>
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                {result?.sources?.map((source, i) => (
                                    <a
                                        key={i}
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block p-3 bg-[#111] border border-white/10 rounded-lg hover:border-neon-blue/50 transition-all truncate group hover:shadow-[0_0_15px_rgba(0,0,0,0.5)]"
                                    >
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[10px] bg-white/10 text-neon-blue px-1.5 py-0.5 rounded font-mono">[{i + 1}]</span>
                                            <p className="text-[10px] text-gray-500 truncate font-mono">{new URL(source.url).hostname.replace('www.', '')}</p>
                                        </div>
                                        <p className="text-xs text-gray-200 font-medium truncate group-hover:text-neon-blue transition-colors">{source.title}</p>
                                    </a>
                                ))}
                                {(!result?.sources || result.sources.length === 0) && (
                                    <div className="col-span-2 text-xs text-gray-600 italic border border-dashed border-white/10 p-3 rounded flex items-center gap-2"><AlertCircle size={12} /> Exploring internal knowledge base...</div>
                                )}
                            </div>
                        </div>

                        <div className="h-[1px] bg-white/10 w-full" />

                        {/* B. Main Answer */}
                        <div className="flex flex-col gap-12">
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-gray-400 text-xs font-bold flex items-center gap-2 uppercase tracking-widest font-display">
                                        <BookOpen size={14} /> Answer
                                    </h3>
                                    {/* Action Row - Top Right for easier access */}
                                    <div className="flex gap-2 no-print">
                                        <button
                                            id="download-pdf-btn"
                                            onClick={handleExportPDF}
                                            className="flex items-center gap-2 px-3 py-1.5 bg-neon-blue/10 text-neon-blue border border-neon-blue/20 rounded-lg text-xs hover:bg-neon-blue hover:text-black transition-all font-medium font-display"
                                        >
                                            <Download size={14} /> Export PDF
                                        </button>
                                    </div>
                                </div>

                                <div className="prose prose-sm md:prose-lg max-w-none text-gray-300 prose-headings:text-white prose-headings:font-display prose-a:text-neon-blue prose-strong:text-white prose-li:text-gray-300 prose-blockquote:border-l-neon-blue prose-blockquote:bg-white/5 prose-blockquote:py-2 prose-blockquote:px-4 font-body">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {result?.report || ''}
                                    </ReactMarkdown>
                                </div>

                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    // Initial Search Mode
    return (
        <div className="h-full w-full flex flex-col justify-center items-center px-4">
            <div className="text-center mb-10 animate-fade-in-up">
                <h1 className="text-5xl md:text-6xl font-display font-extrabold tracking-tight mb-4 flex items-center justify-center gap-4">
                    <Microscope className="w-12 h-12 md:w-16 md:h-16 text-neon-blue animate-pulse-slow" />
                    DEEP <span className="text-gradient-cyan">RESEARCH</span>
                </h1>
                <p className="text-gray-400 text-lg md:text-xl font-body font-light">Autonomous multi-step reasoning engine.</p>
            </div>

            <div className="w-full max-w-2xl relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-neon-blue via-purple-500 to-pink-500 rounded-2xl opacity-20 blur group-hover:opacity-30 transition duration-1000"></div>
                <div className="relative bg-[#0a0a0a] rounded-2xl border border-white/10 shadow-2xl flex flex-col p-2">
                    <textarea
                        ref={textareaRef}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a complex question..."
                        className="bg-transparent text-white text-lg p-4 w-full focus:outline-none resize-none min-h-[60px] max-h-[200px]"
                        rows={1}
                    />
                    <div className="flex justify-between items-center px-2 pb-1 pt-2">
                        <div className="flex items-center gap-2">
                            <button className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-[10px] font-bold uppercase tracking-wider text-gray-400 transition-colors border border-white/5">
                                <Globe size={10} /> Pro Search
                            </button>
                        </div>
                        <button
                            onClick={handleSearch}
                            disabled={!query.trim()}
                            className={`p-2 rounded-xl transition-all duration-300 ${query.trim() ? 'bg-neon-blue text-black hover:bg-cyan-400 hover:shadow-[0_0_15px_rgba(0,243,255,0.4)]' : 'bg-white/5 text-gray-600 cursor-not-allowed'}`}
                        >
                            <ArrowRight size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeepResearchPage;
