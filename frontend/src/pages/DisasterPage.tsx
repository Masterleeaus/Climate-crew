import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield,
    Phone,
    Activity,
    Loader2,
    RefreshCw,
    Building,
    Home,
    Flame,
    Droplets,
    Wind,
    Zap,
    Siren,
    Heart,
    Send,
    Globe,
    ChevronDown,
    ExternalLink,
    Clock,
    Info,
    Crosshair,
    Radar,
    TriangleAlert,
    ShieldCheck,
    CircleAlert,
    Bot,
    User,
    Locate
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_BASE = 'http://localhost:8000';

// ── Types ──────────────────────────────────────────────────

interface RiskBreakdown {
    earthquake: number;
    flood: number;
    fire: number;
    weather: number;
}

interface RiskAssessment {
    status: string;
    overall_risk_level: string;
    overall_risk_score: number;
    risk_breakdown: RiskBreakdown;
    total_alerts: number;
    highest_severity: string;
    recommended_action: string;
    methodology?: Record<string, string>;
    assessed_at?: string;
}

interface Shelter {
    name: string;
    type: string;
    distance_km: number;
    coordinates?: { lat: number; lon: number };
    phone?: string;
    address?: string;
    wheelchair?: string;
}

interface Alert {
    type: string;
    severity: string;
    distance_km?: number;
    magnitude?: number;
    location?: string;
    recommended_action?: string;
    precipitation_24h_mm?: number;
    max_river_discharge_m3s?: number;
    max_temperature_c?: number;
    max_wind_speed_kmh?: number;
    temperature_c?: number;
    humidity_pct?: number;
    wind_speed_kmh?: number;
    brightness?: number;
    confidence?: string;
    satellite?: string;
}

interface EmergencyContacts {
    country: string;
    contacts: Record<string, string>;
    note: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

// ── Quick-access locations ─────────────────────────────────

const PRESETS = [
    { label: 'Papua NG',  lat: '-6.00',  lon: '147.00' },
    { label: 'Tokyo',     lat: '35.68',  lon: '139.69' },
    { label: 'Taipei',    lat: '25.03',  lon: '121.57' },
    { label: 'Santiago',  lat: '-33.45', lon: '-70.66' },
    { label: 'Istanbul',  lat: '41.01',  lon: '28.98' },
    { label: 'Anchorage', lat: '61.22',  lon: '-149.90' },
    { label: 'LA',        lat: '34.05',  lon: '-118.24' },
    { label: 'Jakarta',   lat: '-6.21',  lon: '106.85' },
];

// ── Hazard metadata ────────────────────────────────────────

const HAZARD_META: Record<string, { icon: any; color: string; gradient: string; model: string; unit: string }> = {
    earthquake: {
        icon: Activity,
        color: 'purple',
        gradient: 'from-purple-500/20 to-violet-500/20',
        model: 'Atkinson & Wald (2007) MMI',
        unit: 'MMI Intensity',
    },
    flood: {
        icon: Droplets,
        color: 'blue',
        gradient: 'from-blue-500/20 to-cyan-500/20',
        model: 'Logistic sigmoid (P\u2085\u2080=75mm)',
        unit: 'Exceedance probability',
    },
    fire: {
        icon: Flame,
        color: 'orange',
        gradient: 'from-orange-500/20 to-amber-500/20',
        model: 'Exponential distance-decay',
        unit: 'Thermal exposure',
    },
    weather: {
        icon: Wind,
        color: 'cyan',
        gradient: 'from-cyan-500/20 to-teal-500/20',
        model: 'NWS Heat Index + Beaufort',
        unit: 'Severity index',
    },
};

// ── Component ──────────────────────────────────────────────

const DisasterPage = () => {
    const [lat, setLat] = useState('35.68');
    const [lon, setLon] = useState('139.69');
    const [radiusKm, setRadiusKm] = useState('300');

    const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
    const [alerts, setAlerts] = useState<{
        earthquakes: Alert[];
        fires: Alert[];
        floods: Alert[];
        weather_warnings: Alert[];
        total_alerts?: number;
    } | null>(null);
    const [shelters, setShelters] = useState<Shelter[]>([]);
    const [emergencyContacts, setEmergencyContacts] = useState<EmergencyContacts | null>(null);

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [chatQuery, setChatQuery] = useState('');
    const [isChatting, setIsChatting] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'shelters' | 'chat'>('overview');
    const [showMethodology, setShowMethodology] = useState(false);

    // ── Helpers ──

    const riskColor = (level: string) => {
        switch (level?.toUpperCase()) {
            case 'CRITICAL': return { text: 'text-red-400', bg: 'bg-red-500', border: 'border-red-500/40', ring: 'ring-red-500/30', glow: 'shadow-red-500/20' };
            case 'HIGH': return { text: 'text-orange-400', bg: 'bg-orange-500', border: 'border-orange-500/40', ring: 'ring-orange-500/30', glow: 'shadow-orange-500/20' };
            case 'MODERATE': return { text: 'text-yellow-400', bg: 'bg-yellow-500', border: 'border-yellow-500/40', ring: 'ring-yellow-500/30', glow: 'shadow-yellow-500/20' };
            default: return { text: 'text-emerald-400', bg: 'bg-emerald-500', border: 'border-emerald-500/40', ring: 'ring-emerald-500/30', glow: 'shadow-emerald-500/20' };
        }
    };

    const severityBadge = (severity: string) => {
        const s = severity?.toLowerCase();
        if (s === 'critical') return 'bg-red-500/20 text-red-400 border-red-500/30';
        if (s === 'high') return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
        if (s === 'moderate') return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    };

    // ── Fetchers ──

    const fetchRiskAssessment = async () => {
        try {
            const r = await fetch(`${API_BASE}/disaster/risk-assessment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: parseFloat(lat), longitude: parseFloat(lon), radius_km: parseFloat(radiusKm) }),
            });
            setRiskAssessment(await r.json());
        } catch (e) { console.error('Risk assessment failed:', e); }
    };

    const fetchAlerts = async () => {
        try {
            const r = await fetch(`${API_BASE}/disaster/alerts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: parseFloat(lat), longitude: parseFloat(lon), radius_km: parseFloat(radiusKm) }),
            });
            setAlerts(await r.json());
        } catch (e) { console.error('Alerts fetch failed:', e); }
    };

    const fetchShelters = async () => {
        try {
            const r = await fetch(`${API_BASE}/disaster/shelters`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: parseFloat(lat), longitude: parseFloat(lon), limit: 8 }),
            });
            const data = await r.json();
            setShelters(data.shelters || []);
        } catch (e) { console.error('Shelters fetch failed:', e); }
    };

    const fetchEmergencyContacts = async () => {
        try {
            const r = await fetch(`${API_BASE}/disaster/emergency-contacts/IN`);
            setEmergencyContacts(await r.json());
        } catch (e) { console.error('Emergency contacts fetch failed:', e); }
    };

    const fetchAllData = useCallback(async () => {
        setLoading(true);
        await Promise.all([fetchRiskAssessment(), fetchAlerts(), fetchShelters(), fetchEmergencyContacts()]);
        setLoading(false);
    }, [lat, lon, radiusKm]);

    const handleChat = async () => {
        if (!chatQuery.trim()) return;
        const userMsg = chatQuery.trim();
        setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setChatQuery('');
        setIsChatting(true);
        try {
            const r = await fetch(`${API_BASE}/disaster/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMsg }),
            });
            const data = await r.json();
            setChatMessages(prev => [...prev, { role: 'assistant', content: data.response || 'No response.' }]);
        } catch {
            setChatMessages(prev => [...prev, { role: 'assistant', content: 'Failed to connect to agent.' }]);
        } finally {
            setIsChatting(false);
        }
    };

    useEffect(() => { fetchAllData(); }, []);
    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);

    // ── Total alert count ──
    const totalAlerts = alerts
        ? (alerts.earthquakes?.length || 0) + (alerts.fires?.length || 0) + (alerts.floods?.length || 0) + (alerts.weather_warnings?.length || 0)
        : riskAssessment?.total_alerts || 0;

    // ── Sub-components ──

    const CircularGauge = ({ score, level, size = 200 }: { score: number; level: string; size?: number }) => {
        const r = size / 2 - 16;
        const circumference = 2 * Math.PI * r;
        const offset = circumference - (score / 100) * circumference;
        const rc = riskColor(level);
        return (
            <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
                {/* Background ring */}
                <svg className="absolute" width={size} height={size}>
                    <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                    <motion.circle
                        cx={size / 2} cy={size / 2} r={r} fill="none"
                        strokeWidth="10" strokeLinecap="round"
                        className={`${rc.bg.replace('bg-', 'stroke-')}`}
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 1.5, ease: 'easeOut' }}
                        style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                    />
                </svg>
                {/* Glow */}
                <div className={`absolute rounded-full blur-2xl opacity-20 ${rc.bg}`} style={{ width: size * 0.6, height: size * 0.6 }} />
                {/* Score */}
                <div className="text-center z-10">
                    <motion.div
                        className={`text-5xl font-black ${rc.text}`}
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.3, type: 'spring', stiffness: 100 }}
                    >
                        {score.toFixed(0)}
                    </motion.div>
                    <div className={`text-xs font-bold uppercase tracking-[0.2em] mt-1 ${rc.text}`}>{level}</div>
                    <div className="text-[10px] text-gray-600 mt-1 font-mono">/ 100</div>
                </div>
            </div>
        );
    };

    const HazardCard = ({ hazard, score }: { hazard: string; score: number }) => {
        const meta = HAZARD_META[hazard];
        if (!meta) return null;
        const Icon = meta.icon;
        const pct = Math.min(100, Math.max(0, score));
        const isActive = pct > 0;
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`relative overflow-hidden rounded-2xl border transition-all ${isActive
                    ? `bg-gradient-to-br ${meta.gradient} border-${meta.color}-500/30 shadow-lg shadow-${meta.color}-500/5`
                    : 'bg-[#0a0a0a] border-white/5'
                    }`}
            >
                <div className="p-5">
                    <div className="flex items-start justify-between mb-4">
                        <div className={`p-2.5 rounded-xl ${isActive ? `bg-${meta.color}-500/20` : 'bg-white/5'}`}>
                            <Icon size={20} className={isActive ? `text-${meta.color}-400` : 'text-gray-600'} />
                        </div>
                        <span className={`text-2xl font-black font-mono ${isActive ? `text-${meta.color}-400` : 'text-gray-700'}`}>
                            {pct.toFixed(0)}
                        </span>
                    </div>
                    <div className="mb-1">
                        <span className={`text-sm font-bold capitalize ${isActive ? 'text-white' : 'text-gray-500'}`}>
                            {hazard}
                        </span>
                    </div>
                    <div className="text-[10px] text-gray-600 font-mono mb-3">{meta.model}</div>
                    {/* Progress bar */}
                    <div className="h-1.5 bg-black/30 rounded-full overflow-hidden">
                        <motion.div
                            className={`h-full rounded-full ${isActive ? `bg-${meta.color}-500` : 'bg-gray-800'}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
                        />
                    </div>
                </div>
            </motion.div>
        );
    };

    const AlertCard = ({ alert, category }: { alert: Alert; category: string }) => {
        const meta = HAZARD_META[category] || HAZARD_META.weather;
        const Icon = meta.icon;
        const getDetail = () => {
            if (alert.magnitude) return `M${alert.magnitude}`;
            if (alert.precipitation_24h_mm) return `${alert.precipitation_24h_mm}mm/24h`;
            if (alert.max_river_discharge_m3s) return `${alert.max_river_discharge_m3s} m\u00B3/s`;
            if (alert.max_temperature_c) return `${alert.max_temperature_c}\u00B0C`;
            if (alert.max_wind_speed_kmh) return `${alert.max_wind_speed_kmh} km/h`;
            if (alert.brightness) return `${alert.brightness}K`;
            return alert.type?.replace(/_/g, ' ');
        };
        return (
            <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`p-4 rounded-xl border bg-gradient-to-r ${meta.gradient} border-${meta.color}-500/20 group hover:border-${meta.color}-500/40 transition-all`}
            >
                <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg bg-${meta.color}-500/20 mt-0.5`}>
                        <Icon size={16} className={`text-${meta.color}-400`} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-white text-sm">{getDetail()}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold uppercase ${severityBadge(alert.severity)}`}>
                                {alert.severity}
                            </span>
                            {alert.distance_km != null && (
                                <span className="text-[10px] text-gray-500 font-mono ml-auto">{alert.distance_km} km</span>
                            )}
                        </div>
                        {alert.location && <p className="text-xs text-gray-400 truncate">{alert.location}</p>}
                        {alert.recommended_action && (
                            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{alert.recommended_action}</p>
                        )}
                    </div>
                </div>
            </motion.div>
        );
    };

    const ShelterCard = ({ shelter, index }: { shelter: Shelter; index: number }) => {
        const iconMap: Record<string, any> = {
            hospital: Heart, fire_station: Flame, police: Shield,
            community_centre: Building, shelter: Home,
        };
        const SIcon = iconMap[shelter.type] || Home;
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06 }}
                className="group relative bg-[#0a0a0a] border border-white/5 rounded-2xl p-5 hover:border-emerald-500/30 hover:bg-emerald-500/[0.02] transition-all"
            >
                <div className="flex items-start gap-4">
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 group-hover:bg-emerald-500/20 transition-colors">
                        <SIcon size={20} className="text-emerald-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                            <h3 className="font-bold text-white text-sm leading-tight">{shelter.name}</h3>
                            {shelter.distance_km != null && (
                                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md whitespace-nowrap border border-emerald-500/20">
                                    {shelter.distance_km} km
                                </span>
                            )}
                        </div>
                        <p className="text-xs text-gray-500 capitalize mt-0.5">{shelter.type?.replace(/_/g, ' ')}</p>
                        {shelter.address && shelter.address !== 'Address not available' && (
                            <p className="text-xs text-gray-600 mt-1">{shelter.address}</p>
                        )}
                        <div className="flex items-center gap-3 mt-2.5">
                            {shelter.phone && (
                                <a href={`tel:${shelter.phone}`} className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
                                    <Phone size={11} /> {shelter.phone}
                                </a>
                            )}
                            {shelter.coordinates && (
                                <a
                                    href={`https://www.google.com/maps/dir/?api=1&destination=${shelter.coordinates.lat},${shelter.coordinates.lon}`}
                                    target="_blank" rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
                                >
                                    <ExternalLink size={11} /> Directions
                                </a>
                            )}
                            {shelter.wheelchair && shelter.wheelchair !== 'unknown' && (
                                <span className="text-[10px] text-gray-600">Wheelchair: {shelter.wheelchair}</span>
                            )}
                        </div>
                    </div>
                </div>
            </motion.div>
        );
    };

    const EmptyState = ({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle: string }) => (
        <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 mb-4">
                <Icon size={32} className="text-gray-600" />
            </div>
            <p className="text-sm font-semibold text-gray-400">{title}</p>
            <p className="text-xs text-gray-600 mt-1 max-w-xs">{subtitle}</p>
        </div>
    );

    // ── Render ──

    return (
        <div className="min-h-screen bg-[#020202] text-white p-4 lg:p-6 font-sans">
            {/* ── HEADER ── */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 gap-4"
            >
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 bg-gradient-to-br from-red-500/20 to-orange-500/20 rounded-xl flex items-center justify-center border border-red-500/20">
                            <Siren className="text-red-500" size={24} />
                        </div>
                        {totalAlerts > 0 && (
                            <div className="absolute -top-1.5 -right-1.5 min-w-5 h-5 bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                                <span className="text-[10px] font-bold text-white px-1">{totalAlerts}</span>
                            </div>
                        )}
                    </div>
                    <div>
                        <h1 className="text-xl lg:text-2xl font-black tracking-tight">
                            DISASTER <span className="text-red-500">COMMAND</span>
                        </h1>
                        <p className="text-[10px] text-gray-600 font-mono tracking-[0.2em]">
                            PHYSICS-BASED HAZARD INTELLIGENCE
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                        <span className="text-[10px] font-mono text-emerald-400 font-bold">LIVE</span>
                    </div>
                    <button
                        onClick={fetchAllData}
                        disabled={loading}
                        className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all disabled:opacity-50"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin text-red-400' : 'text-gray-400'} />
                    </button>
                </div>
            </motion.header>

            {/* ── LOCATION BAR ── */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
                className="bg-[#080808] border border-white/[0.06] rounded-2xl p-4 mb-4"
            >
                <div className="flex flex-col gap-3">
                    {/* Input row */}
                    <div className="flex flex-col lg:flex-row gap-3 items-end">
                        <div className="flex-1 grid grid-cols-3 gap-3">
                            <div className="space-y-1">
                                <label className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Lat</label>
                                <div className="relative">
                                    <Crosshair className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-700" size={13} />
                                    <input type="text" value={lat} onChange={(e) => setLat(e.target.value)}
                                        className="w-full bg-black/60 border border-white/[0.06] rounded-lg py-2.5 pl-8 pr-3 text-sm text-white font-mono focus:border-red-500/30 outline-none transition-all" />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Lon</label>
                                <div className="relative">
                                    <Globe className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-700" size={13} />
                                    <input type="text" value={lon} onChange={(e) => setLon(e.target.value)}
                                        className="w-full bg-black/60 border border-white/[0.06] rounded-lg py-2.5 pl-8 pr-3 text-sm text-white font-mono focus:border-red-500/30 outline-none transition-all" />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Radius</label>
                                <div className="relative">
                                    <Radar className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-700" size={13} />
                                    <input type="text" value={radiusKm} onChange={(e) => setRadiusKm(e.target.value)}
                                        className="w-full bg-black/60 border border-white/[0.06] rounded-lg py-2.5 pl-8 pr-3 text-sm text-white font-mono focus:border-red-500/30 outline-none transition-all" />
                                    <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 font-mono">km</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => {
                                    if (navigator.geolocation) {
                                        navigator.geolocation.getCurrentPosition((pos) => {
                                            setLat(pos.coords.latitude.toFixed(4));
                                            setLon(pos.coords.longitude.toFixed(4));
                                        });
                                    }
                                }}
                                className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/[0.06] rounded-lg text-gray-500 hover:text-white transition-all" title="My Location"
                            >
                                <Locate size={14} />
                            </button>
                            <button
                                onClick={fetchAllData}
                                disabled={loading}
                                className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white text-sm font-bold rounded-lg transition-all flex items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? <Loader2 className="animate-spin" size={14} /> : <Radar size={14} />}
                                SCAN
                            </button>
                        </div>
                    </div>

                    {/* Preset locations */}
                    <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
                        <span className="text-[9px] text-gray-700 font-mono uppercase tracking-wider whitespace-nowrap mr-1">Quick:</span>
                        {PRESETS.map((p) => (
                            <button
                                key={p.label}
                                onClick={() => { setLat(p.lat); setLon(p.lon); }}
                                className={`px-2.5 py-1 text-[10px] font-semibold rounded-md border transition-all whitespace-nowrap ${lat === p.lat && lon === p.lon
                                    ? 'bg-red-500/10 text-red-400 border-red-500/30'
                                    : 'bg-white/[0.02] text-gray-500 border-white/[0.04] hover:bg-white/5 hover:text-gray-300'
                                    }`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>

            {/* ── TABS ── */}
            <div className="flex gap-1 mb-5 overflow-x-auto">
                {[
                    { id: 'overview', label: 'Threat Matrix', icon: Shield, badge: null },
                    { id: 'alerts', label: 'Active Alerts', icon: TriangleAlert, badge: totalAlerts || null },
                    { id: 'shelters', label: 'Shelters', icon: ShieldCheck, badge: shelters.length || null },
                    { id: 'chat', label: 'AI Agent', icon: Bot, badge: null },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === tab.id
                            ? 'bg-white/10 text-white border border-white/10'
                            : 'text-gray-500 border border-transparent hover:text-gray-300 hover:bg-white/[0.03]'
                            }`}
                    >
                        <tab.icon size={14} />
                        {tab.label}
                        {tab.badge != null && tab.badge > 0 && (
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${activeTab === tab.id ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-gray-500'}`}>
                                {tab.badge}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* ── CONTENT ── */}
            <AnimatePresence mode="wait">
                {/* ─── OVERVIEW ─── */}
                {activeTab === 'overview' && (
                    <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-5">
                        {/* Top row: Gauge + Hazard cards */}
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                            {/* Circular gauge */}
                            <div className="lg:col-span-4 bg-[#080808] border border-white/[0.06] rounded-2xl p-6 flex flex-col items-center justify-center">
                                {riskAssessment ? (
                                    <>
                                        <div className="text-[9px] text-gray-600 uppercase tracking-[0.2em] font-bold mb-4">Overall Risk</div>
                                        <CircularGauge score={riskAssessment.overall_risk_score} level={riskAssessment.overall_risk_level} />
                                        <div className="text-[9px] text-gray-700 font-mono mt-4 text-center">
                                            P(any) = 1 &minus; &Pi;(1 &minus; P<sub>i</sub>/100)
                                        </div>
                                    </>
                                ) : (
                                    <div className="py-12"><Loader2 className="animate-spin text-gray-700" size={28} /></div>
                                )}
                            </div>

                            {/* 4 hazard cards */}
                            <div className="lg:col-span-8 grid grid-cols-2 lg:grid-cols-4 gap-3">
                                {riskAssessment ? (
                                    Object.entries(riskAssessment.risk_breakdown).map(([hazard, score]) => (
                                        <HazardCard key={hazard} hazard={hazard} score={score} />
                                    ))
                                ) : (
                                    Array.from({ length: 4 }).map((_, i) => (
                                        <div key={i} className="bg-[#0a0a0a] border border-white/5 rounded-2xl p-5 animate-pulse">
                                            <div className="h-10 w-10 bg-white/5 rounded-xl mb-4" />
                                            <div className="h-3 w-16 bg-white/5 rounded mb-2" />
                                            <div className="h-1.5 bg-white/5 rounded-full" />
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Action + Stats row */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                            {/* Recommended Action */}
                            {riskAssessment && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`lg:col-span-2 p-5 rounded-2xl border ${riskColor(riskAssessment.overall_risk_level).border} bg-gradient-to-r ${riskAssessment.overall_risk_level === 'CRITICAL' ? 'from-red-500/10 to-red-500/5' : riskAssessment.overall_risk_level === 'HIGH' ? 'from-orange-500/10 to-orange-500/5' : riskAssessment.overall_risk_level === 'MODERATE' ? 'from-yellow-500/10 to-yellow-500/5' : 'from-emerald-500/10 to-emerald-500/5'}`}
                                >
                                    <div className="flex items-start gap-4">
                                        <div className={`p-2.5 rounded-xl ${riskColor(riskAssessment.overall_risk_level).bg}/20`}>
                                            <Zap size={20} className={riskColor(riskAssessment.overall_risk_level).text} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Recommended Action</div>
                                            <div className="text-sm text-gray-200 leading-relaxed">{riskAssessment.recommended_action}</div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {/* Quick stats + Emergency contacts */}
                            <div className="space-y-4">
                                <div className="bg-[#080808] border border-white/[0.06] rounded-2xl p-4 space-y-2.5">
                                    {[
                                        { icon: CircleAlert, label: 'Active Alerts', value: totalAlerts, color: totalAlerts > 0 ? 'text-red-400' : 'text-gray-500' },
                                        { icon: ShieldCheck, label: 'Shelters Found', value: shelters.length, color: shelters.length > 0 ? 'text-emerald-400' : 'text-gray-500' },
                                        { icon: Radar, label: 'Scan Radius', value: `${radiusKm} km`, color: 'text-gray-400' },
                                    ].map((stat) => (
                                        <div key={stat.label} className="flex items-center justify-between py-1.5">
                                            <div className="flex items-center gap-2">
                                                <stat.icon size={13} className="text-gray-600" />
                                                <span className="text-xs text-gray-500">{stat.label}</span>
                                            </div>
                                            <span className={`text-sm font-bold font-mono ${stat.color}`}>{stat.value}</span>
                                        </div>
                                    ))}
                                </div>

                                {emergencyContacts && (
                                    <div className="bg-gradient-to-br from-red-500/[0.06] to-orange-500/[0.03] border border-red-500/20 rounded-2xl p-4">
                                        <div className="text-[9px] font-bold text-red-400/70 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
                                            <Phone size={10} /> Emergency ({emergencyContacts.country})
                                        </div>
                                        {Object.entries(emergencyContacts.contacts).map(([svc, num]) => (
                                            <div key={svc} className="flex items-center justify-between py-1">
                                                <span className="text-[11px] text-gray-500 capitalize">{svc}</span>
                                                <a href={`tel:${num}`} className="font-mono text-sm font-bold text-white hover:text-red-400 transition-colors">{num}</a>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Methodology (collapsible) */}
                        {riskAssessment?.methodology && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-[#080808] border border-white/[0.04] rounded-2xl overflow-hidden">
                                <button
                                    onClick={() => setShowMethodology(!showMethodology)}
                                    className="w-full flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Info size={13} className="text-gray-600" />
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Scoring Methodology</span>
                                    </div>
                                    <ChevronDown size={14} className={`text-gray-600 transition-transform ${showMethodology ? 'rotate-180' : ''}`} />
                                </button>
                                <AnimatePresence>
                                    {showMethodology && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="px-5 pb-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                                {Object.entries(riskAssessment.methodology).map(([key, val]) => (
                                                    <div key={key} className="p-3 bg-white/[0.02] rounded-lg border border-white/[0.03]">
                                                        <div className="text-[10px] text-gray-400 font-bold uppercase mb-1">{key}</div>
                                                        <div className="text-[11px] text-gray-600 font-mono leading-relaxed">{val}</div>
                                                    </div>
                                                ))}
                                            </div>
                                            {riskAssessment.assessed_at && (
                                                <div className="px-5 pb-3 flex items-center gap-1.5">
                                                    <Clock size={10} className="text-gray-700" />
                                                    <span className="text-[10px] text-gray-700 font-mono">
                                                        {new Date(riskAssessment.assessed_at).toLocaleString()}
                                                    </span>
                                                </div>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        )}
                    </motion.div>
                )}

                {/* ─── ALERTS TAB ─── */}
                {activeTab === 'alerts' && (
                    <motion.div key="alerts" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        {totalAlerts > 0 ? (
                            <div className="space-y-6">
                                {[
                                    { key: 'earthquakes', label: 'Seismic Activity', data: alerts?.earthquakes },
                                    { key: 'fires', label: 'Active Fires', data: alerts?.fires },
                                    { key: 'floods', label: 'Flood Warnings', data: alerts?.floods },
                                    { key: 'weather_warnings', label: 'Extreme Weather', data: alerts?.weather_warnings, hazard: 'weather' },
                                ].filter(s => s.data && s.data.length > 0).map((section) => {
                                    const hazardKey = section.key === 'earthquakes' ? 'earthquake' : section.key === 'fires' ? 'fire' : section.key === 'floods' ? 'flood' : 'weather';
                                    const meta = HAZARD_META[hazardKey];
                                    return (
                                        <div key={section.key}>
                                            <div className="flex items-center gap-2 mb-3">
                                                {meta && <meta.icon size={14} className={`text-${meta.color}-400`} />}
                                                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">{section.label}</h3>
                                                <span className="text-[10px] bg-white/5 text-gray-500 px-2 py-0.5 rounded-full font-mono">{section.data!.length}</span>
                                            </div>
                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
                                                {section.data!.slice(0, 8).map((alert, i) => (
                                                    <AlertCard key={i} alert={alert} category={hazardKey} />
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <EmptyState
                                icon={ShieldCheck}
                                title="No Active Alerts"
                                subtitle="No significant hazards detected within your scan radius. Conditions appear safe."
                            />
                        )}
                    </motion.div>
                )}

                {/* ─── SHELTERS TAB ─── */}
                {activeTab === 'shelters' && (
                    <motion.div key="shelters" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        {shelters.length > 0 ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between mb-2">
                                    <h2 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                        <ShieldCheck size={14} /> Emergency Shelters Nearby
                                    </h2>
                                    <span className="text-[10px] text-gray-600 font-mono">
                                        within 25 km &middot; via OpenStreetMap
                                    </span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {shelters.map((s, i) => (
                                        <ShelterCard key={i} shelter={s} index={i} />
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <EmptyState
                                icon={Home}
                                title="No Shelters Found"
                                subtitle="No emergency shelters found within 25 km. Contact local emergency services for assistance."
                            />
                        )}
                    </motion.div>
                )}

                {/* ─── CHAT TAB ─── */}
                {activeTab === 'chat' && (
                    <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="bg-[#080808] border border-white/[0.06] rounded-2xl flex flex-col" style={{ height: 'calc(100vh - 320px)', minHeight: 420 }}
                    >
                        {/* Chat header */}
                        <div className="px-5 py-3 border-b border-white/[0.04] flex items-center gap-2">
                            <Bot size={16} className="text-red-400" />
                            <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Disaster AI Agent</span>
                            <span className="text-[9px] text-gray-600 font-mono ml-auto">Physics-based analysis</span>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
                            {chatMessages.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-full text-center">
                                    <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/10 mb-4">
                                        <Bot size={28} className="text-red-400/60" />
                                    </div>
                                    <p className="text-sm text-gray-400 font-semibold mb-1">Disaster Management Agent</p>
                                    <p className="text-xs text-gray-600 max-w-sm leading-relaxed">
                                        Ask about disaster risks, evacuation routes, nearby shelters, or emergency contacts for any location.
                                    </p>
                                    <div className="flex flex-wrap gap-2 mt-5 justify-center">
                                        {[
                                            "What's the disaster risk in Delhi?",
                                            "Find shelters near Tokyo",
                                            "Evacuation plan for earthquake",
                                            "Emergency contacts for India",
                                        ].map((prompt) => (
                                            <button
                                                key={prompt}
                                                onClick={() => { setChatQuery(prompt); }}
                                                className="px-3 py-1.5 text-[11px] bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] rounded-lg text-gray-500 hover:text-gray-300 transition-all"
                                            >
                                                {prompt}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {chatMessages.map((msg, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
                                >
                                    {msg.role === 'assistant' && (
                                        <div className="w-7 h-7 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <Bot size={14} className="text-red-400" />
                                        </div>
                                    )}
                                    <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                        ? 'bg-white/10 text-white'
                                        : 'bg-white/[0.03] border border-white/[0.04]'
                                        }`}>
                                        {msg.role === 'assistant' ? (
                                            <div className="prose prose-invert prose-xs max-w-none [&_p]:text-[13px] [&_p]:leading-relaxed [&_p]:text-gray-300 [&_li]:text-[13px] [&_li]:text-gray-300">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        ) : (
                                            <p className="text-sm">{msg.content}</p>
                                        )}
                                    </div>
                                    {msg.role === 'user' && (
                                        <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <User size={14} className="text-gray-400" />
                                        </div>
                                    )}
                                </motion.div>
                            ))}

                            {isChatting && (
                                <div className="flex gap-3">
                                    <div className="w-7 h-7 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                                        <Bot size={14} className="text-red-400" />
                                    </div>
                                    <div className="bg-white/[0.03] border border-white/[0.04] rounded-2xl px-4 py-3">
                                        <div className="flex items-center gap-1.5">
                                            <div className="w-1.5 h-1.5 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-1.5 h-1.5 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-1.5 h-1.5 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>

                        {/* Input */}
                        <div className="px-4 py-3 border-t border-white/[0.04]">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={chatQuery}
                                    onChange={(e) => setChatQuery(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleChat()}
                                    placeholder="Ask about disaster risks, shelters, evacuation..."
                                    className="flex-1 bg-black/40 border border-white/[0.06] rounded-xl py-3 px-4 text-sm text-white placeholder-gray-600 focus:border-red-500/30 outline-none transition-all"
                                />
                                <button
                                    onClick={handleChat}
                                    disabled={isChatting || !chatQuery.trim()}
                                    className="px-4 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white font-bold rounded-xl transition-all disabled:opacity-30"
                                >
                                    {isChatting ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* ── Loading overlay ── */}
            <AnimatePresence>
                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center"
                    >
                        <motion.div
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            className="bg-[#0a0a0a] border border-white/10 rounded-2xl p-8 text-center"
                        >
                            <div className="relative w-16 h-16 mx-auto mb-4">
                                <div className="absolute inset-0 border-2 border-red-500/20 rounded-full" />
                                <div className="absolute inset-0 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                                <Radar size={24} className="absolute inset-0 m-auto text-red-400" />
                            </div>
                            <p className="text-sm font-bold text-white mb-1">Scanning Area</p>
                            <p className="text-xs text-gray-500 font-mono">
                                {lat}, {lon} &middot; {radiusKm}km radius
                            </p>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DisasterPage;
