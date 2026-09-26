import React, { useState } from 'react';
import {
    LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Activity, Thermometer, Wind, Droplets, Zap, AlertTriangle, Newspaper, ExternalLink, Clock, MessageCircle } from 'lucide-react';
import { useCachedFetch } from '../hooks/useCachedFetch';
import NewsChatModal from '../components/NewsChatModal';
import { NewsArticle } from '../services/newsApi';

// Helper Component for Metrics
const MetricCard = ({ label, location, coordinates, value, unit, delta, icon: Icon, color, details }: any) => (
    <div className="glass-card p-5 border border-white/10 hover:border-white/30 transition-all group relative overflow-hidden">
        {/* Location Context */}
        <div className="absolute top-0 right-0 bg-white/5 px-2 py-1 rounded-bl-lg">
            <p className="text-[10px] text-gray-400 font-mono">{coordinates}</p>
        </div>

        <div className="flex justify-between items-start mb-4 mt-2">
            <div className={`p-3 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors ${color}`}>
                <Icon size={24} />
            </div>
            <span className={`text-xs font-bold px-2 py-1 rounded bg-white/5 ${delta.includes('+') || delta.includes('Hazardous') || delta.includes('Rising') ? 'text-red-400' : 'text-green-400'}`}>
                {delta}
            </span>
        </div>

        <div>
            <p className="text-gray-400 text-xs uppercase tracking-wider font-bold mb-1 font-display">{label}</p>
            <p className="text-neon-blue font-display font-bold text-sm truncate">{location}</p>
            {/* New Details Structured Grid */}
            {details && (
                <div className="mt-3 pt-2 border-t border-white/10 flex flex-col gap-1">
                    {details.split('|').map((item: string, i: number) => (
                        <div key={i} className="flex items-center gap-2">
                            <div className="w-1 h-1 rounded-full bg-neon-blue/50"></div>
                            <span className="text-xs text-gray-300 font-mono tracking-wide">{item.trim()}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>

        <div className="flex items-baseline gap-2 mt-2">
            <h4 className="text-3xl font-black font-display tracking-tight">{value}</h4>
            <span className="text-xs text-gray-500 font-medium font-body">{unit}</span>
        </div>
    </div>
);

const NewsCard = ({ article, onChatClick }: { article: NewsArticle; onChatClick: (article: NewsArticle) => void }) => {
    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffDays = Math.floor(diffHours / 24);
            
            if (diffHours < 1) return 'Just now';
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return 'Recently';
        }
    };

    const handleChatClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        onChatClick(article);
    };

    return (
        <div className="glass-card p-5 border border-white/10 hover:border-white/30 transition-all group relative overflow-hidden h-full flex flex-col">
            {/* Content */}
            <div className="flex flex-col h-full">
                {/* Source and Date */}
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-neon-blue uppercase tracking-wider font-display">
                        {article.source}
                    </span>
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock size={12} />
                        <span>{formatDate(article.published_at)}</span>
                    </div>
                </div>
                
                {/* Title */}
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-lg font-bold font-display mb-2 line-clamp-2 group-hover:text-neon-blue transition-colors cursor-pointer"
                >
                    {article.title}
                </a>
                
                {/* Summary */}
                {article.summary && (
                    <p className="text-sm text-gray-400 mb-3 line-clamp-2 flex-1">
                        {article.summary.replace(/<[^>]*>/g, '').trim()}
                    </p>
                )}
                
                {/* Tags and Actions */}
                <div className="flex items-center justify-between mt-auto pt-3 border-t border-white/10">
                    {article.tags && article.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                            {article.tags.slice(0, 2).map((tag, i) => (
                                <span
                                    key={i}
                                    className="text-xs px-2 py-1 rounded bg-white/5 text-gray-400 font-mono"
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    )}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleChatClick}
                            className="p-2 rounded-lg bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/30 text-neon-blue transition-colors group/btn"
                            title="Chat about this article"
                        >
                            <MessageCircle size={14} className="group-hover/btn:scale-110 transition-transform" />
                        </button>
                        <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-500 hover:text-neon-blue transition-colors"
                            title="Read full article"
                        >
                            <ExternalLink size={14} />
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

const OverviewPage: React.FC = () => {
    const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
    const [isChatModalOpen, setIsChatModalOpen] = useState(false);

    // Use cached fetch for global summary - shows cached data immediately, refreshes in background
    const {
        data: stats,
        loading,
        isFromCache: statsFromCache,
        isRefreshing: statsRefreshing
    } = useCachedFetch<any>('http://localhost:8000/global/summary', {
        cacheKey: 'global-summary',
        maxAge: 2 * 60 * 1000, // 2 minutes
    });

    // Use cached fetch for news - shows cached data immediately, refreshes in background
    const {
        data: newsData,
        loading: newsLoading,
        isFromCache: newsFromCache,
        isRefreshing: newsRefreshing
    } = useCachedFetch<NewsArticle[]>('http://localhost:8000/news?limit=6', {
        cacheKey: 'news-articles',
        maxAge: 5 * 60 * 1000, // 5 minutes
        transform: (data) => {
            if (Array.isArray(data)) {
                return data;
            }
            console.warn("News data is not an array:", data);
            return [];
        }
    });

    const news = newsData || [];

    const handleChatClick = (article: NewsArticle) => {
        setSelectedArticle(article);
        setIsChatModalOpen(true);
    };

    const handleCloseChat = () => {
        setIsChatModalOpen(false);
        setSelectedArticle(null);
    };

    // Show loading only if we have no cached data
    if (loading && !stats) {
        return <div className="p-10 text-white animate-pulse font-display text-xl">Establishing Satellite Uplink...</div>;
    }

    const metrics = stats?.metrics || [];
    const feed = stats?.ticker_feed || [];
    const charts = stats?.charts || {};

    return (
        <div className="p-8 text-white max-w-[1600px] mx-auto space-y-8 animate-fade-in">

            {/* 1. Header & Live Ticker */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8 border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-5xl font-display font-extrabold tracking-tight flex items-center gap-4">
                        <Zap className="text-neon-blue w-10 h-10 fill-neon-blue animate-pulse-slow" />
                        GLOBAL <span className="text-gradient-cyan">CLIMATE PULSE</span>
                    </h1>
                    <p className="text-gray-400 mt-2 font-mono text-sm">
                        System Status: <span className="text-green-400">ONLINE</span> | 
                        Data Stream: <span className="text-neon-blue animate-pulse">LIVE</span>
                        {(statsFromCache || newsFromCache) && (
                            <span className="ml-2 text-xs text-gray-500">
                                {statsRefreshing || newsRefreshing ? '🔄 Refreshing...' : '📦 Cached'}
                            </span>
                        )}
                    </p>
                </div>
                <div className="flex gap-4">
                    <div className="bg-glass-200 border border-white/10 px-4 py-2 rounded-lg text-right">
                        <p className="text-xs text-gray-400 uppercase font-bold font-display">Global Temp Anomaly</p>
                        <p className="text-2xl font-bold text-red-500 font-mono">+1.45°C</p>
                    </div>
                </div>
            </header>

            {/* 2. Key Metrics Grid (REAL DATA) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    label="Temperature"
                    location={metrics[0]?.location_name || "Arctic Pole"}
                    coordinates={metrics[0]?.coordinates || "75.0°N, 40.0°W"}
                    value={metrics[0]?.value || "--"}
                    unit="Current"
                    delta={metrics[0]?.delta || ""}
                    details={metrics[0]?.details || "Wind: -- | Hum: --"}
                    icon={Thermometer}
                    color="text-blue-300"
                />
                <MetricCard
                    label="Air Quality"
                    location={metrics[1]?.location_name || "New Delhi"}
                    coordinates={metrics[1]?.coordinates || "28.6°N, 77.2°E"}
                    value={metrics[1]?.value || "--"}
                    unit="AQI (PM2.5)"
                    delta={metrics[1]?.delta || ""}
                    details={metrics[1]?.details || "Pollutant: PM2.5"}
                    icon={Wind}
                    color="text-orange-500"
                />
                <MetricCard
                    label="Fire Risk"
                    location={metrics[2]?.location_name || "Amazon Basin"}
                    coordinates={metrics[2]?.coordinates || "3.4°S, 62.2°W"}
                    value={metrics[2]?.value || "--"}
                    unit="Index"
                    delta={metrics[2]?.delta || ""}
                    details={metrics[2]?.details || "7-Day Total: 0"}
                    icon={AlertTriangle}
                    color="text-red-500"
                />
                <MetricCard
                    label="Marine Status"
                    location={metrics[3]?.location_name || "GBR Reef"}
                    coordinates={metrics[3]?.coordinates || "18.2°S, 147.6°E"}
                    value={metrics[3]?.value || "--"}
                    unit="Bleaching"
                    delta={metrics[3]?.delta || ""}
                    details={metrics[3]?.details || "Region: West Pacific"}
                    icon={Droplets}
                    color="text-cyan-400"
                />
            </div>

            {/* 3. Main Content Area - Charts Left, News Right */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Left Side: Charts */}
                <div className="xl:col-span-2 space-y-8" id="charts-section">
                    {/* Main Visualization Layer */}
                    <div className="grid grid-cols-1 gap-8 min-h-[400px]">
                        {/* Chart A: Temperature Anomaly */}
                        <div className="glass-card p-6 border border-white/10 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-blue-500/5 group-hover:bg-blue-500/10 transition-colors" />
                            <h3 className="text-xl font-display font-bold mb-6 flex items-center gap-2 relative z-10">
                                <Activity className="w-5 h-5 text-neon-blue" />
                                Temperature Trajectory (Global Avg)
                            </h3>
                            <div className="h-[300px] w-full relative z-10">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={charts.temp_anomaly || []}>
                                        <defs>
                                            <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                        <XAxis dataKey="year" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} unit="°C" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid #333', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                        />
                                        <Area type="monotone" dataKey="value" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorTemp)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Secondary Visualization Layer */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-[300px]">
                        {/* Chart C: Emissions */}
                        <div className="glass-card p-6 border border-white/10 relative overflow-hidden">
                            <h3 className="text-lg font-display font-bold mb-4 text-gray-300">GHG Emissions (Last 12 Months)</h3>
                            <div className="h-[250px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={charts.emissions || []}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                        <XAxis dataKey="month" stroke="#666" fontSize={12} tickLine={false} />
                                        <YAxis stroke="#666" fontSize={12} tickLine={false} />
                                        <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} />
                                        <Line type="monotone" dataKey="co2" stroke="#fbbf24" strokeWidth={2} dot={false} />
                                        <Line type="monotone" dataKey="methane" stroke="#34d399" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Live Agent Feed */}
                        <div className="glass-card p-6 border border-white/10 flex flex-col relative overflow-hidden">
                            <h3 className="text-lg font-display font-bold mb-4 text-gray-300 flex justify-between">
                                <span>Cluster Intelligence Log</span>
                                <span className="text-xs bg-neon-blue/20 text-neon-blue px-2 py-1 rounded">LIVE</span>
                            </h3>
                            <div className="flex-1 overflow-y-hidden relative group">
                                <div className="absolute inset-0 overflow-y-auto space-y-3 custom-scrollbar pr-2">
                                    {feed.map((msg: string, i: number) => (
                                        <div key={i} className="flex gap-3 text-sm p-3 rounded bg-white/5 border border-white/5 hover:border-white/20 transition-colors">
                                            <div className="w-1 h-full min-h-[20px] bg-neon-blue rounded-full" />
                                            <div>
                                                <p className="text-gray-400 text-xs mb-0.5 font-bold font-display uppercase tracking-wider">LATEST</p>
                                                <p className="text-gray-200 font-body">{msg}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side: Climate News Section */}
                <div className="xl:col-span-1">
                    <div className="glass-card p-6 border border-white/10 relative overflow-hidden w-full flex flex-col" style={{ height: 'calc(400px + 32px + 300px)' }}>
                        <div className="flex items-center justify-between mb-6 flex-shrink-0">
                            <h3 className="text-xl font-display font-bold flex items-center gap-2">
                                <Newspaper className="w-5 h-5 text-neon-blue" />
                                Climate News
                            </h3>
                            {newsLoading && (
                                <span className="text-xs text-gray-500 animate-pulse">Loading...</span>
                            )}
                        </div>
                        
                        <div className="flex-1 overflow-y-auto custom-scrollbar" style={{ minHeight: 0, maxHeight: '100%' }}>
                            {newsLoading ? (
                                <div className="space-y-4">
                                    {[1, 2, 3].map((i) => (
                                        <div key={i} className="glass-card p-4 border border-white/10 animate-pulse">
                                            <div className="h-3 bg-white/5 rounded mb-2" />
                                            <div className="h-3 bg-white/5 rounded w-3/4" />
                                        </div>
                                    ))}
                                </div>
                            ) : news.length > 0 ? (
                                <div className="space-y-4">
                                    {news.map((article) => (
                                        <NewsCard key={article.id} article={article} onChatClick={handleChatClick} />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-gray-500">
                                    <Newspaper className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p className="text-sm">No news articles available at this time.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* News Chat Modal */}
            <NewsChatModal
                article={selectedArticle}
                isOpen={isChatModalOpen}
                onClose={handleCloseChat}
            />

        </div>
    );
};

export default OverviewPage;
