import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Globe,
    Search,
    Activity,
    DollarSign,
    Zap,
    Send,
    Bot,
    Shield,
    TrendingUp,
    Minus,
    AlertTriangle,
    BarChart3,
    Leaf,
    Users,
    Scale,
    ArrowUpRight,
    ArrowDownRight
} from 'lucide-react';
import { climateFinanceApi, ClimateRisk, CarbonPricesResponse, StockQuote } from '../services/climateFinanceApi';

/* ─────────────── Metric Card ─────────────── */
const MetricCard = ({ icon: Icon, label, value, subtext, colorClass, loading }: {
    icon: any; label: string; value: string; subtext?: string; colorClass: string; loading?: boolean;
}) => (
    <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-[#0a0a0a] border border-white/10 p-5 rounded-2xl hover:border-white/20 transition-all group relative overflow-hidden"
    >
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="relative z-10">
            <div className="flex justify-between items-start mb-3">
                <span className="text-gray-500 text-[10px] font-bold uppercase tracking-[0.15em]">{label}</span>
                <div className={`p-2 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors`}>
                    <Icon size={16} className={colorClass} />
                </div>
            </div>
            {loading ? (
                <div className="space-y-2">
                    <div className="h-7 w-24 bg-white/5 rounded animate-pulse" />
                    <div className="h-3 w-32 bg-white/5 rounded animate-pulse" />
                </div>
            ) : (
                <>
                    <h3 className="text-2xl font-black text-white mb-0.5 tracking-tight">{value}</h3>
                    {subtext && <p className="text-xs text-gray-500 font-mono">{subtext}</p>}
                </>
            )}
        </div>
    </motion.div>
);

/* ─────────────── Risk Gauge ─────────────── */
const RiskGauge = ({ score = 0, size = 140 }: { score?: number; size?: number }) => {
    const safeScore = isNaN(score) ? 0 : Math.min(100, Math.max(0, score));
    const radius = (size / 2) - 16;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (safeScore / 100) * circumference;

    let color = '#10b981';
    let label = 'LOW';
    if (safeScore > 60) { color = '#ef4444'; label = 'HIGH'; }
    else if (safeScore > 30) { color = '#f59e0b'; label = 'MODERATE'; }

    return (
        <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
            <svg className="w-full h-full transform -rotate-90">
                <circle cx="50%" cy="50%" r={radius} stroke="#1a1a1a" strokeWidth="10" fill="none" />
                <circle cx="50%" cy="50%" r={radius} stroke="#222" strokeWidth="10" fill="none" strokeDasharray="4 4" />
                <motion.circle
                    cx="50%" cy="50%" r={radius}
                    stroke={color}
                    strokeWidth="10"
                    fill="none"
                    strokeDasharray={circumference}
                    strokeLinecap="round"
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset: offset }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                />
            </svg>
            <div className="absolute flex flex-col items-center">
                <span className="text-3xl font-black text-white">{safeScore}</span>
                <span className="text-[9px] uppercase font-bold tracking-[0.2em]" style={{ color }}>{label}</span>
            </div>
        </div>
    );
};

/* ─────────────── Trend Icon ─────────────── */
const TrendIcon = ({ trend }: { trend: string }) => {
    if (trend === 'rising') return <TrendingUp size={14} className="text-emerald-400" />;
    if (trend === 'volatile') return <Activity size={14} className="text-amber-400" />;
    return <Minus size={14} className="text-gray-500" />;
};

/* ─────────────── Chat Interface ─────────────── */
const ChatInterface = () => {
    const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([
        { role: 'assistant', content: "Hello! I'm your Climate Finance AI. Ask me about stock climate risks, carbon pricing, or regulatory impacts on your portfolio." }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const data = await climateFinanceApi.chat(userMsg);
            setMessages(prev => [...prev, { role: 'assistant', content: data.response || 'No response.' }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Failed to connect to agent.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#060606] border border-white/10 rounded-2xl overflow-hidden">
            {/* Header */}
            <div className="bg-[#0a0a0a] px-5 py-4 border-b border-white/5 flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-neon-blue/20 flex items-center justify-center border border-neon-blue/40">
                    <Bot size={16} className="text-neon-blue" />
                </div>
                <div>
                    <h3 className="text-white font-bold text-sm">Climate Finance AI</h3>
                    <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Online
                    </p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar" ref={scrollRef}>
                {messages.map((msg, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                            msg.role === 'user'
                                ? 'bg-neon-blue text-black font-medium rounded-tr-sm'
                                : 'bg-white/5 text-gray-300 rounded-tl-sm border border-white/5'
                        }`}>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                    </motion.div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white/5 px-4 py-3 rounded-2xl rounded-tl-sm flex gap-1.5">
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="p-3 bg-[#0a0a0a] border-t border-white/5">
                <div className="relative flex items-center gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask about climate risks, carbon prices..."
                        className="flex-1 bg-black border border-white/10 rounded-xl py-3 px-4 text-sm text-white focus:border-neon-blue/50 outline-none transition-colors placeholder-gray-600"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading}
                        className="p-3 bg-neon-blue rounded-xl text-black hover:bg-cyan-400 transition-colors disabled:opacity-50 flex-shrink-0"
                    >
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

/* ─────────────── Main Page ─────────────── */
const ClimateFinancePage = () => {
    const [ticker, setTicker] = useState('AAPL');
    const [riskData, setRiskData] = useState<ClimateRisk | null>(null);
    const [quoteData, setQuoteData] = useState<StockQuote | null>(null);
    const [loadingRisk, setLoadingRisk] = useState(false);
    const [carbonData, setCarbonData] = useState<CarbonPricesResponse | null>(null);
    const [loadingCarbon, setLoadingCarbon] = useState(true);

    const fetchRisk = async () => {
        if (!ticker.trim()) return;
        setLoadingRisk(true);
        try {
            const [risk, quote] = await Promise.allSettled([
                climateFinanceApi.getStockRisk(ticker),
                climateFinanceApi.getStockQuote(ticker)
            ]);
            setRiskData(risk.status === 'fulfilled' ? risk.value : null);
            setQuoteData(quote.status === 'fulfilled' ? quote.value : null);
        } catch (e) {
            console.error(e);
            setRiskData(null);
            setQuoteData(null);
        } finally {
            setLoadingRisk(false);
        }
    };

    const fetchCarbonPrices = async () => {
        setLoadingCarbon(true);
        try {
            const data = await climateFinanceApi.getCarbonPrices();
            setCarbonData(data);
        } catch (e) {
            console.error(e);
            setCarbonData(null);
        } finally {
            setLoadingCarbon(false);
        }
    };

    useEffect(() => {
        fetchCarbonPrices();
        fetchRisk();
    }, []);

    // Compute EU ETS price and global average from real data
    const euEtsPrice = carbonData?.prices?.find(p => p.id === 'EU_ETS');
    const globalAvg = carbonData?.average_usd ?? 0;
    const highestPrice = carbonData?.highest;

    // Price change calculation
    const priceChange = quoteData?.price && quoteData?.previous_close
        ? quoteData.price - quoteData.previous_close
        : null;
    const priceChangePct = priceChange && quoteData?.previous_close
        ? (priceChange / quoteData.previous_close) * 100
        : null;

    return (
        <div className="min-h-screen bg-black text-white p-6 md:p-8 pb-32 overflow-y-auto custom-scrollbar">

            {/* ─── Header ─── */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-8 pb-6 border-b border-white/10">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neon-blue/20 to-purple-500/20 flex items-center justify-center border border-neon-blue/30">
                            <DollarSign className="w-5 h-5 text-neon-blue" />
                        </div>
                        <div>
                            <h1 className="text-3xl md:text-4xl font-black tracking-tight">
                                CLIMATE <span className="text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-purple-400">FINANCE</span>
                            </h1>
                        </div>
                    </div>
                    <p className="text-gray-500 text-sm ml-14">Real-time ESG intelligence and climate risk analytics</p>
                </div>

                {/* Ticker Search */}
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:w-72">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" size={16} />
                        <input
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="Enter Ticker (e.g. MSFT)"
                            className="w-full bg-[#0a0a0a] border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm font-mono text-white focus:border-neon-blue/50 outline-none transition-colors uppercase placeholder-gray-600"
                            onKeyDown={(e) => e.key === 'Enter' && fetchRisk()}
                        />
                    </div>
                    <button
                        onClick={fetchRisk}
                        disabled={loadingRisk}
                        className="px-6 py-3 bg-neon-blue text-black font-bold rounded-xl hover:bg-cyan-400 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                        {loadingRisk ? <Activity className="w-4 h-4 animate-spin" /> : <Search size={16} />}
                        ANALYZE
                    </button>
                </div>
            </header>

            {/* ─── Top Metric Cards (Real Data) ─── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <MetricCard
                    icon={DollarSign}
                    label="EU ETS Carbon Price"
                    value={euEtsPrice ? `$${euEtsPrice.price_usd.toFixed(0)}/t` : '--'}
                    subtext={euEtsPrice ? `€${euEtsPrice.price_local} ${euEtsPrice.currency} | ${euEtsPrice.coverage}` : undefined}
                    colorClass="text-emerald-400"
                    loading={loadingCarbon}
                />
                <MetricCard
                    icon={Globe}
                    label="Global Average Price"
                    value={globalAvg ? `$${globalAvg.toFixed(1)}/t` : '--'}
                    subtext={carbonData ? `Across ${carbonData.count} systems (tCO2e)` : undefined}
                    colorClass="text-amber-400"
                    loading={loadingCarbon}
                />
                <MetricCard
                    icon={TrendingUp}
                    label="Highest Carbon Price"
                    value={highestPrice ? `$${highestPrice.price_usd}/t` : '--'}
                    subtext={highestPrice?.name}
                    colorClass="text-red-400"
                    loading={loadingCarbon}
                />
                <MetricCard
                    icon={BarChart3}
                    label="Active Pricing Systems"
                    value={carbonData ? `${carbonData.count}` : '--'}
                    subtext="ETS & Carbon Tax globally"
                    colorClass="text-violet-400"
                    loading={loadingCarbon}
                />
            </div>

            {/* ─── Main Content ─── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* ─── Left Column ─── */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Stock Price Banner (when data available) */}
                    <AnimatePresence>
                        {quoteData?.price && riskData && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="p-5 rounded-2xl bg-gradient-to-r from-[#0a0a0a] to-[#0d0d1a] border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center border border-white/10">
                                        <span className="text-lg font-black text-white">{riskData.ticker.substring(0, 2)}</span>
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-lg font-black text-white">{riskData.ticker}</h3>
                                            <span className="text-xs text-gray-500 font-mono">{riskData.company}</span>
                                        </div>
                                        <p className="text-xs text-gray-600">{riskData.sector}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <p className="text-2xl font-black text-white font-mono">
                                            ${quoteData.price.toFixed(2)}
                                        </p>
                                        {priceChange !== null && priceChangePct !== null && (
                                            <div className={`flex items-center gap-1 justify-end text-xs font-mono ${priceChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {priceChange >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                                                <span>{priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePct.toFixed(2)}%)</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="hidden sm:grid grid-cols-2 gap-x-6 gap-y-1 text-[10px] text-gray-500 font-mono">
                                        <span>High: ${quoteData.day_high?.toFixed(2) ?? '--'}</span>
                                        <span>52w H: ${quoteData.fifty_two_week_high?.toFixed(2) ?? '--'}</span>
                                        <span>Low: ${quoteData.day_low?.toFixed(2) ?? '--'}</span>
                                        <span>52w L: ${quoteData.fifty_two_week_low?.toFixed(2) ?? '--'}</span>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Risk Analysis Card */}
                    <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-white/10 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-neon-blue/5 to-transparent rounded-bl-full pointer-events-none" />
                        <h2 className="text-lg font-bold mb-6 flex items-center gap-2 relative z-10">
                            <Shield className="text-neon-blue" size={18} />
                             Climate Risk Profile
                            {riskData && <span className="text-neon-blue ml-1">{riskData.ticker}</span>}
                        </h2>

                        {loadingRisk ? (
                            <div className="h-48 flex items-center justify-center">
                                <Activity className="w-5 h-5 animate-spin text-neon-blue mr-3" />
                                <span className="text-gray-500 text-sm">Running ML risk model...</span>
                            </div>
                        ) : riskData ? (
                            <div className="space-y-6">
                                {/* Top row: Gauge + Company Info */}
                                <div className="flex flex-col md:flex-row gap-6 items-start">
                                    <div className="flex-shrink-0 flex flex-col items-center gap-3">
                                        <RiskGauge score={riskData.risk_score} />
                                        <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                                            riskData.risk_level.includes('High') || riskData.risk_level.includes('Very')
                                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                                : riskData.risk_level.includes('Moderate')
                                                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                        }`}>
                                            {riskData.risk_level}
                                        </span>
                                    </div>

                                    <div className="flex-1 space-y-3 min-w-0">
                                        <div className="grid grid-cols-3 gap-3">
                                            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                                                <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-1">Company</p>
                                                <p className="text-sm font-bold text-white truncate">{riskData.company}</p>
                                            </div>
                                            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                                                <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-1">Sector</p>
                                                <p className="text-sm font-bold text-white">{riskData.sector}</p>
                                            </div>
                                            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                                                <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-1">Industry</p>
                                                <p className="text-sm font-bold text-white truncate">{riskData.industry || 'N/A'}</p>
                                            </div>
                                        </div>

                                        {/* Key Risks */}
                                        {riskData.key_risks && riskData.key_risks.length > 0 && (
                                            <div>
                                                <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-2">Key Risk Factors (from data)</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {riskData.key_risks.map((risk, i) => (
                                                        <span key={i} className="px-3 py-1.5 text-xs rounded-lg bg-red-500/10 text-red-300 border border-red-500/15 flex items-center gap-1.5">
                                                            <AlertTriangle size={10} />
                                                            {risk}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Score source */}
                                        {riskData.score_breakdown?.source && (
                                            <p className="text-[10px] text-gray-600 font-mono pt-1 border-t border-white/5">
                                                Scoring: {riskData.score_breakdown.source}
                                                {riskData.historical_volatility != null && (
                                                    <span className="ml-3">Volatility: {(riskData.historical_volatility * 100).toFixed(1)}%</span>
                                                )}
                                            </p>
                                        )}
                                    </div>
                                </div>

                                {/* TCFD Pillar Breakdown */}
                                {riskData.score_breakdown?.pillars && (
                                    <div>
                                        <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-3">TCFD Pillar Breakdown</p>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                            {([
                                                { key: 'physical_risk', label: 'Physical Risk', icon: Activity, desc: 'Volatility & beta' },
                                                { key: 'transition_risk', label: 'Transition Risk', icon: Leaf, desc: 'ESG & carbon exposure' },
                                                { key: 'financial_vulnerability', label: 'Financial Health', icon: Shield, desc: 'Debt, margins & size' },
                                                { key: 'market_sentiment', label: 'Market Signals', icon: BarChart3, desc: 'Valuation & yield' },
                                            ] as const).map(({ key, label, icon: PIcon, desc }) => {
                                                const val = riskData.score_breakdown?.pillars?.[key];
                                                const barColor = val == null ? 'bg-gray-700' : val > 60 ? 'bg-red-500' : val > 35 ? 'bg-amber-500' : 'bg-emerald-500';
                                                return (
                                                    <div key={key} className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <PIcon size={12} className="text-gray-500" />
                                                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">{label}</span>
                                                        </div>
                                                        <div className="flex items-end gap-2 mb-1.5">
                                                            <span className="text-xl font-black text-white">{val ?? '--'}</span>
                                                            <span className="text-[10px] text-gray-600 mb-0.5">/100</span>
                                                        </div>
                                                        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                            <motion.div
                                                                className={`h-full rounded-full ${barColor}`}
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${val ?? 0}%` }}
                                                                transition={{ duration: 0.8, ease: 'easeOut' }}
                                                            />
                                                        </div>
                                                        <p className="text-[9px] text-gray-600 mt-1">{desc}</p>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                {/* Feature Contributions (Statistical) */}
                                {riskData.score_breakdown?.feature_contributions && riskData.score_breakdown.feature_contributions.length > 0 && (
                                    <div>
                                        <p className="text-[10px] text-gray-600 uppercase tracking-wider font-bold mb-3">
                                            Feature Analysis (percentile rank vs reference universe)
                                        </p>
                                        {/* Table header */}
                                        <div className="grid grid-cols-12 gap-1 text-[9px] text-gray-600 uppercase tracking-wider font-bold px-2 mb-1.5">
                                            <span className="col-span-3">Feature</span>
                                            <span className="col-span-2 text-right">Value</span>
                                            <span className="col-span-1 text-right">Pctl</span>
                                            <span className="col-span-1 text-right">Corr</span>
                                            <span className="col-span-4">Risk Impact</span>
                                            <span className="col-span-1 text-right">Score</span>
                                        </div>
                                        <div className="space-y-1">
                                            {riskData.score_breakdown.feature_contributions
                                                .filter(c => c.direction !== 'anchor')
                                                .slice(0, 10)
                                                .map((c, i) => (
                                                <div key={i} className="grid grid-cols-12 gap-1 items-center text-xs px-2 py-1.5 rounded-lg hover:bg-white/[0.02] transition-colors">
                                                    <span className="col-span-3 text-gray-400 truncate">{c.feature}</span>
                                                    <span className="col-span-2 text-gray-500 font-mono text-right">{c.value}</span>
                                                    <span className="col-span-1 text-gray-500 font-mono text-right">
                                                        {c.percentile != null ? `${c.percentile}` : '—'}
                                                    </span>
                                                    <span className={`col-span-1 font-mono text-right ${
                                                        c.correlation != null
                                                            ? c.correlation > 0 ? 'text-red-400/70' : 'text-emerald-400/70'
                                                            : 'text-gray-600'
                                                    }`}>
                                                        {c.correlation != null ? (c.correlation > 0 ? '+' : '') + c.correlation.toFixed(2) : '—'}
                                                    </span>
                                                    <div className="col-span-4 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                        <motion.div
                                                            className={`h-full rounded-full ${c.direction === 'increases' ? 'bg-red-500/70' : 'bg-emerald-500/70'}`}
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${c.risk_impact ?? 0}%` }}
                                                            transition={{ duration: 0.6, delay: i * 0.04 }}
                                                        />
                                                    </div>
                                                    <span className={`col-span-1 text-right font-mono font-bold ${c.direction === 'increases' ? 'text-red-400' : 'text-emerald-400'}`}>
                                                        {c.risk_impact ?? '—'}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                        {/* Volatility anchor */}
                                        {riskData.historical_volatility != null && (
                                            <div className="mt-2 pt-2 border-t border-white/5 flex items-center gap-2 text-[10px] text-gray-600 font-mono px-2">
                                                <Activity size={10} />
                                                <span>Correlation anchor: Realised Volatility = {(riskData.historical_volatility * 100).toFixed(1)}%</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="h-48 flex flex-col items-center justify-center text-center">
                                <Search className="w-8 h-8 text-white/10 mb-3" />
                                <p className="text-gray-500 text-sm">Enter a ticker symbol above to analyze climate risk</p>
                            </div>
                        )}
                    </div>

                    {/* Carbon Pricing Table */}
                    <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-white/10">
                        <div className="flex items-center justify-between mb-5">
                            <h3 className="text-lg font-bold flex items-center gap-2">
                                <Globe size={18} className="text-violet-400" />
                                Global Carbon Pricing
                            </h3>
                            <span className="text-[10px] text-gray-600 font-mono">Source: World Bank</span>
                        </div>

                        {loadingCarbon ? (
                            <div className="space-y-3">
                                {[1, 2, 3, 4, 5].map(i => (
                                    <div key={i} className="h-14 bg-white/5 rounded-xl animate-pulse" />
                                ))}
                            </div>
                        ) : carbonData?.prices && carbonData.prices.length > 0 ? (
                            <div className="space-y-2">
                                {/* Table Header */}
                                <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] text-gray-600 uppercase tracking-wider font-bold">
                                    <span className="col-span-4">System</span>
                                    <span className="col-span-2">Type</span>
                                    <span className="col-span-2 text-right">USD Price</span>
                                    <span className="col-span-2 text-right">Local</span>
                                    <span className="col-span-1 text-center">Trend</span>
                                    <span className="col-span-1"></span>
                                </div>

                                {carbonData.prices.map((cp, i) => (
                                    <motion.div
                                        key={cp.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.04 }}
                                        className="grid grid-cols-12 gap-2 items-center px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-white/10 transition-all group"
                                    >
                                        {/* Name */}
                                        <div className="col-span-4">
                                            <p className="text-sm font-semibold text-white truncate group-hover:text-neon-blue transition-colors">{cp.name}</p>
                                            <p className="text-[10px] text-gray-600">{cp.coverage}</p>
                                        </div>
                                        {/* Type */}
                                        <div className="col-span-2">
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                                                cp.type === 'ETS'
                                                    ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                                                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                            }`}>
                                                {cp.type}
                                            </span>
                                        </div>
                                        {/* USD Price */}
                                        <div className="col-span-2 text-right">
                                            <span className="text-sm font-mono font-bold text-white">${cp.price_usd.toFixed(0)}</span>
                                            <span className="text-[10px] text-gray-600 ml-0.5">/t</span>
                                        </div>
                                        {/* Local Price */}
                                        <div className="col-span-2 text-right">
                                            <span className="text-xs font-mono text-gray-400">{cp.price_local} {cp.currency}</span>
                                        </div>
                                        {/* Trend */}
                                        <div className="col-span-1 flex justify-center">
                                            <TrendIcon trend={cp.trend} />
                                        </div>
                                        {/* Bar indicator */}
                                        <div className="col-span-1 flex justify-end">
                                            <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                <motion.div
                                                    className="h-full rounded-full bg-gradient-to-r from-neon-blue to-violet-500"
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${Math.min(100, (cp.price_usd / 140) * 100)}%` }}
                                                    transition={{ duration: 0.8, delay: i * 0.05 }}
                                                />
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 text-sm text-center py-8">No carbon pricing data available</p>
                        )}
                    </div>
                </div>

                {/* ─── Right Column: Chat + Tips ─── */}
                <div className="lg:col-span-1 flex flex-col gap-6" style={{ height: 'fit-content' }}>
                    <div style={{ height: '700px' }}>
                        <ChatInterface />
                    </div>

                    {/* Quick Insights */}
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-[#0a0a0a] to-[#0d0a14] border border-white/10">
                        <h4 className="font-bold text-white mb-4 text-sm flex items-center gap-2">
                            <Zap size={14} className="text-amber-400" /> Quick Insights
                        </h4>
                        <ul className="space-y-3">
                            {[
                                { icon: Leaf, text: 'EU carbon prices have been rising steadily, reaching $85/tCO2.', color: 'text-emerald-400' },
                                { icon: Shield, text: 'Energy sector stocks carry the highest climate transition risk.', color: 'text-red-400' },
                                { icon: Scale, text: 'Sweden and Switzerland lead with carbon prices over $130/tCO2.', color: 'text-violet-400' },
                                { icon: Users, text: 'Tech stocks show the strongest resilience to carbon regulation.', color: 'text-neon-blue' },
                            ].map((insight, i) => (
                                <li key={i} className="flex gap-3 items-start">
                                    <insight.icon size={14} className={`${insight.color} mt-0.5 flex-shrink-0`} />
                                    <span className="text-xs text-gray-400 leading-relaxed">{insight.text}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ClimateFinancePage;
