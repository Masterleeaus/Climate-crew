import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapContainer, TileLayer, Marker, useMapEvents, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import * as L from 'leaflet';
import {
    TrendingUp,
    AlertTriangle,
    Truck,
    BrainCircuit,
    ArrowRight,
    Activity,
    Users,
    Map as MapIcon,
    Cpu,
    Search,
    ZoomIn,
    ZoomOut,
    Anchor,
    DollarSign,
    Layers,
    X,
    Crosshair
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

// Fix Leaflet Default Icon
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom Marker for Target
const targetIcon = new L.DivIcon({
    className: 'custom-div-icon',
    html: `<div style="background-color: #00f7ff; width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 10px #00f7ff; border: 2px solid white;"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
});

// --- TYPES (Matching Backend Models) ---

interface CausalNodeData {
    description: string;
    category: "Physical" | "Economic" | "Social" | "Logistics" | "Root";
    impact_score: number;
    probability?: number;
    time_lag?: string;
    evidence?: string;
    children: CausalNodeData[];
}

interface ActionItem {
    trigger_event: string;
    action: string;
    assigned_to: string;
    priority: "Critical" | "High" | "Medium";
    resource_needed: string[];
}

interface ActionPlan {
    items: ActionItem[];
}

interface MapMarker {
    lat: number;
    lon: number;
    label: string;
    type: "Store" | "Warehouse" | "Vehicle" | "Hazard";
    status: "Safe" | "At Risk" | "Critical";
}

interface KPIGauge {
    label: string;
    value: number;
    unit: string;
    threshold: "Normal" | "Warning" | "Critical";
}

interface DashboardPayload {
    markers: MapMarker[];
    kpis: KPIGauge[];
    news_ticker: string[];
    risk_score: number;
}

interface AuditResponse {
    causal_graph: CausalNodeData;
    action_plan: ActionPlan;
    dashboard_payload: DashboardPayload;
}

// --- MOCK CHART DATA ---
const MOCK_DEMAND_DATA = [
    { day: 'Mon', demand: 4000, supply: 2400 },
    { day: 'Tue', demand: 3000, supply: 5398 },
    { day: 'Wed', demand: 2000, supply: 9800 },
    { day: 'Thu', demand: 2780, supply: 3908 },
    { day: 'Fri', demand: 1890, supply: 4800 },
    { day: 'Sat', demand: 2390, supply: 3800 },
    { day: 'Sun', demand: 3490, supply: 4300 },
];

// --- COMPONENTS ---

const FeatureCard = ({ icon: Icon, title, description, delay }: any) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.5 }}
        className="relative group p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer overflow-hidden backdrop-blur-md"
    >
        <div className="absolute inset-0 bg-gradient-to-br from-neon-blue/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative z-10">
            <div className="w-12 h-12 rounded-full bg-black/50 flex items-center justify-center mb-4 border border-white/10 group-hover:border-neon-blue/50 transition-colors">
                <Icon className="text-neon-blue w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
        </div>
    </motion.div>
);

const CausalNode = ({ x, y, label, type, impact, probability, evidence }: any) => {
    const color = type === 'Logistics' ? '#ef4444' : type === 'Economic' ? '#3b82f6' : type === 'Physical' ? '#10b981' : '#f59e0b';
    const size = 30 + (impact || 0) * 2;
    const prob = probability || 0;

    // Select Icon based on Category
    let Icon = Activity;
    if (type === 'Logistics') Icon = Truck;
    if (type === 'Economic') Icon = DollarSign;
    if (type === 'Physical') Icon = Anchor;
    if (type === 'Social') Icon = Users;
    if (type === 'Root') Icon = AlertTriangle;

    return (
        <motion.g
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            whileHover={{ scale: 1.1, cursor: 'pointer' }}
            className="group"
        >
            {/* Glow Effect for High Impact */}
            {impact > 7 && (
                <circle cx={x} cy={y} r={size + 15} fill="none" stroke={color} strokeOpacity="0.2">
                    <animate attributeName="r" from={size + 5} to={size + 20} dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite" />
                </circle>
            )}

            {/* Probability Ring (dashed) */}
            <circle
                cx={x} cy={y}
                r={size + 5}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeDasharray={`${prob * 100} 100`}
                strokeOpacity="0.5"
                transform={`rotate(-90 ${x} ${y})`}
            />

            {/* Main Circle */}
            <circle cx={x} cy={y} r={size} fill="#0a0a0a" stroke={color} strokeWidth="2" />

            {/* Inner Icon */}
            <foreignObject x={x - 15} y={y - 15} width="30" height="30" style={{ pointerEvents: 'none' }}>
                <div className="flex items-center justify-center h-full w-full">
                    <Icon size={20} color={color} />
                </div>
            </foreignObject>

            {/* Label & Tooltip */}
            <foreignObject x={x - 90} y={y + size + 10} width="180" height="120">
                <div className="flex flex-col items-center group relative">
                    <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-1 bg-${color}/10 border border-${color}/20 text-${color === '#ef4444' ? 'red-500' : color === '#3b82f6' ? 'blue-500' : 'gray-300'}`}>
                        {type} | {(prob * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-center text-white font-bold bg-[#111] rounded-lg px-3 py-2 border border-white/20 shadow-2xl leading-snug w-full relative z-20">
                        {label}
                        {evidence && (
                            <div className="mt-1 text-[9px] text-gray-400 font-mono border-t border-white/10 pt-1">
                                {evidence}
                            </div>
                        )}
                    </div>
                </div>
            </foreignObject>
        </motion.g>
    );
};

const CausalGraph = ({ graphData }: { graphData: CausalNodeData | null }) => {
    const [scale, setScale] = useState(0.65);
    const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 });
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                setContainerDimensions({
                    width: containerRef.current.offsetWidth,
                    height: containerRef.current.offsetHeight
                });
            }
        };

        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // --- SMART LAYOUT ALGORITHM ---
    const NODE_WIDTH = 350; // Balanced spacing
    const LEVEL_HEIGHT = 220;

    // 1. Calculate required width for each subtree
    const getSubtreeWidth = (node: CausalNodeData): number => {
        if (!node.children || node.children.length === 0) return NODE_WIDTH;
        const childrenWidth = node.children.reduce((sum, child) => sum + getSubtreeWidth(child), 0);
        return Math.max(NODE_WIDTH, childrenWidth);
    };

    const nodes: any[] = [];
    const links: any[] = [];

    // 2. Position nodes recursively
    const layoutNode = (
        node: CausalNodeData,
        x: number,
        y: number,
        parentIndex: number | null
    ) => {
        const currentIndex = nodes.length;
        nodes.push({ ...node, x, y });

        if (parentIndex !== null) {
            links.push({ source: parentIndex, target: currentIndex });
        }

        const subtreeWidth = getSubtreeWidth(node);
        // Start placing children from the left edge of this node's allocated area
        let currentX = x - subtreeWidth / 2;

        node.children.forEach((child) => {
            const childWidth = getSubtreeWidth(child);
            const childCenterX = currentX + childWidth / 2;
            layoutNode(child, childCenterX, y + LEVEL_HEIGHT, currentIndex);
            currentX += childWidth;
        });
    };

    if (graphData) {
        // Layout relative to (0,0) as root
        layoutNode(graphData, 0, 0, null);
    }

    const handleWheel = (e: React.WheelEvent) => {
        // e.preventDefault(); // Stop page scroll inside component if possible
        const newScale = Math.min(Math.max(scale + e.deltaY * -0.001, 0.1), 4);
        setScale(newScale);
    };

    return (
        <div
            ref={containerRef}
            className="w-full h-[600px] bg-black/60 backdrop-blur-xl rounded-xl border border-white/10 relative overflow-hidden cursor-move group shadow-2xl"
            onWheel={handleWheel}
        >
            {/* Controls */}
            <div className="absolute bottom-4 right-4 flex gap-2 z-20">
                <button onClick={() => setScale(s => Math.min(s + 0.2, 4))} className="p-2 bg-white/10 rounded-lg hover:bg-white/20 text-white"><ZoomIn size={16} /></button>
                <button onClick={() => setScale(s => Math.max(s - 0.2, 0.1))} className="p-2 bg-white/10 rounded-lg hover:bg-white/20 text-white"><ZoomOut size={16} /></button>
                <button onClick={() => { setScale(0.65); }} className="p-2 bg-white/10 rounded-lg hover:bg-white/20 text-white text-xs font-bold">RESET</button>
            </div>

            <div className="absolute top-4 left-4 z-10 bg-black/80 backdrop-blur px-4 py-2 rounded-full border border-white/10 pointer-events-none">
                <h3 className="text-white font-bold flex items-center gap-2 text-sm uppercase tracking-wider">
                    <BrainCircuit size={16} className="text-neon-blue" /> Risk Propagation Map
                </h3>
            </div>

            {containerDimensions.width > 0 && (
                <motion.div
                    className="w-full h-full"
                    drag
                    dragConstraints={{ left: -3000, right: 3000, top: -2000, bottom: 2000 }}
                    style={{ scale, x: 0, y: 0 }}
                >
                    <svg className="w-full h-full overflow-visible">
                        <defs>
                            <linearGradient id="linkGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor="#333" stopOpacity="0.5" />
                                <stop offset="100%" stopColor="#666" stopOpacity="0.8" />
                            </linearGradient>
                        </defs>

                        <g transform={`translate(${containerDimensions.width / 2}, 100)`}>
                            {/* Bezier Links - Thicker */}
                            {links.map((link, i) => {
                                const sx = nodes[link.source].x;
                                const sy = nodes[link.source].y;
                                const tx = nodes[link.target].x;
                                const ty = nodes[link.target].y;

                                const path = `M ${sx} ${sy} C ${sx} ${(sy + ty) / 2}, ${tx} ${(sy + ty) / 2}, ${tx} ${ty}`;

                                return (
                                    <motion.path
                                        key={i}
                                        d={path}
                                        fill="none"
                                        stroke="url(#linkGradient)"
                                        strokeWidth="3"
                                        initial={{ pathLength: 0, opacity: 0 }}
                                        animate={{ pathLength: 1, opacity: 1 }}
                                        transition={{ duration: 1.5, delay: i * 0.1 }}
                                    />
                                );
                            })}

                            {/* Nodes */}
                            {nodes.map((node, i) => (
                                <CausalNode
                                    key={i}
                                    x={node.x}
                                    y={node.y}
                                    label={node.description}
                                    type={node.category}
                                    impact={node.impact_score}
                                    probability={node.probability}
                                    evidence={node.evidence}
                                />
                            ))}
                        </g>

                        {!graphData && (
                            <text x="50%" y="50%" textAnchor="middle" fill="#555" fontSize="16">Initializing Sensor Network...</text>
                        )}
                    </svg>
                </motion.div>
            )}
        </div>
    );
};

// --- MAP COMPONENTS ---
const MapEvents = ({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) => {
    useMapEvents({
        click(e) {
            onMapClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
};

const RetailPage = () => {
    const [data, setData] = useState<AuditResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [viewMode, setViewMode] = useState<'MAP' | 'DASHBOARD'>('MAP'); // Renamed to MAP
    const [targetPos, setTargetPos] = useState<[number, number]>([28.6139, 77.2090]); // Delhi
    const [pendingScan, setPendingScan] = useState<[number, number] | null>(null);

    const fetchAudit = async (targetLat: number, targetLon: number) => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/retail/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: targetLat, longitude: targetLon })
            });
            const jsonData = await res.json();
            setData(jsonData);

            // Auto switch to dashboard
            setTimeout(() => setViewMode('DASHBOARD'), 800);
        } catch (err) {
            console.error("Failed to fetch retail audit", err);
        } finally {
            setLoading(false);
        }
    };



    const handleMapClick = useCallback((lat: number, lng: number) => {
        console.log("Map Clicked:", lat, lng);
        setPendingScan([lat, lng]);
    }, []);

    const triggerScan = () => {
        if (pendingScan) {
            setTargetPos(pendingScan);
            setPendingScan(null); // Close modal first
            // Start loading process
            fetchAudit(pendingScan[0], pendingScan[1]);
        }
    };

    return (
        <div className="relative min-h-screen bg-black text-white overflow-hidden font-sans">

            {/* --- MAP LAYER --- */}
            <div className={`absolute inset-0 transition-opacity duration-1000 ${viewMode === 'DASHBOARD' ? 'opacity-20 blur-sm' : 'opacity-100'}`}>
                <MapContainer
                    center={[20, 0]}
                    zoom={3}
                    style={{ height: '100%', width: '100%', background: '#050505' }}
                    zoomControl={false}
                >
                    {/* Dark Matter Tiles */}
                    {/* @ts-ignore */}
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />

                    <MapEvents onMapClick={handleMapClick} />

                    {/* Target Markers */}
                    {/* @ts-ignore */}
                    <Marker position={targetPos} icon={targetIcon} />

                    {/* Simulation Markers (Existing Stores) */}
                    {/* @ts-ignore */}
                    <Marker position={[40.7128, -74.0060]} icon={DefaultIcon}>
                        <Popup><div className="text-black">New York Hub</div></Popup>
                    </Marker>
                    {/* @ts-ignore */}
                    <Marker position={[51.5074, -0.1278]} icon={DefaultIcon}>
                        <Popup><div className="text-black">London Hub</div></Popup>
                    </Marker>
                    {/* @ts-ignore */}
                    <Marker position={[35.6762, 139.6503]} icon={DefaultIcon}>
                        <Popup><div className="text-black">Tokyo Hub</div></Popup>
                    </Marker>

                </MapContainer>

                {/* Overlay Grid/Scan lines for effect */}
                <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(0,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px]" />
            </div>

            {/* --- UI LAYER --- */}
            <div className="relative z-10 p-4 md:p-8 h-screen flex flex-col pointer-events-none">

                {/* HEAD HUD */}
                <header className="flex justify-between items-start pointer-events-auto">
                    <div>
                        <motion.h1
                            initial={{ x: -50, opacity: 0 }} animate={{ x: 0, opacity: 1 }}
                            className="text-5xl font-black tracking-tighter mb-2 flex items-center gap-4 drop-shadow-[0_0_15px_rgba(0,247,255,0.5)]"
                        >
                            <MapIcon className="text-neon-blue w-12 h-12" />
                            RETAIL <span className="text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-purple-500">COMMAND v3.0</span>
                        </motion.h1>
                        <div className="ml-2 flex items-center gap-3">
                            <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[10px] font-bold text-emerald-500 tracking-wider">CAUSAL ML ONLINE</span>
                            </div>
                            <span className="text-xs text-gray-400 font-mono tracking-widest uppercase flex items-center gap-2">
                                <Crosshair size={12} className="text-red-500" />
                                TARGET: {targetPos[0].toFixed(4)}, {targetPos[1].toFixed(4)}
                            </span>
                        </div>
                    </div>

                    {/* MODE SWITCHER */}
                    {viewMode === 'DASHBOARD' && (
                        <motion.button
                            initial={{ scale: 0 }} animate={{ scale: 1 }}
                            onClick={() => setViewMode('MAP')}
                            className="bg-white/10 backdrop-blur border border-white/20 p-3 rounded-full hover:bg-white/20 hover:scale-110 transition-all group"
                        >
                            <X className="text-white group-hover:rotate-90 transition-transform" />
                        </motion.button>
                    )}
                </header>


                {/* --- CENTER PROMPT (MAP MODE) --- */}
                <AnimatePresence>
                    {viewMode === 'MAP' && !pendingScan && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="flex-1 flex flex-col items-center justify-center pointer-events-none"
                        >
                            <div className="bg-black/80 backdrop-blur-md border border-white/10 p-8 rounded-3xl text-center max-w-lg pointer-events-auto shadow-[0_0_50px_rgba(0,0,0,0.8)] border-t-4 border-t-neon-blue">
                                <Search className="w-16 h-16 text-neon-blue mx-auto mb-4 animate-pulse" />
                                <h2 className="text-3xl font-bold mb-2 text-white">Select Tactical Zone</h2>
                                <p className="text-gray-400 mb-6">Click anywhere on the map to initiate a deep-scan audit of the local supply chain ecosystem.</p>

                                <div className="flex flex-col gap-2 justify-center items-center min-h-[4rem]">
                                    {/* Placeholder for future content if needed */}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* --- DASHBOARD OVERLAY (DASHBOARD MODE) --- */}
                <AnimatePresence>
                    {viewMode === 'DASHBOARD' && data && (
                        <motion.div
                            initial={{ y: 1000, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: 1000, opacity: 0 }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="absolute inset-x-0 bottom-0 top-32 overflow-y-auto custom-scrollbar pointer-events-auto bg-gradient-to-t from-black via-black/95 to-transparent px-8 pb-32"
                        >
                            <div className="w-full h-24 bg-gradient-to-b from-transparent to-black/50 pointer-events-none sticky top-0 z-10" />

                            <div className="max-w-7xl mx-auto">
                                {/* Feature Cards */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 mt-4">
                                    <FeatureCard
                                        icon={BrainCircuit}
                                        title="Causal Inference"
                                        description="Detect hidden relationships between climate events and supply chain disruptions."
                                        delay={0.1}
                                    />
                                    <FeatureCard
                                        icon={TrendingUp}
                                        title="Demand Forecasting"
                                        description="Hyper-local demand prediction models adjusted for extreme weather events."
                                        delay={0.2}
                                    />
                                    <FeatureCard
                                        icon={Truck}
                                        title="Supply Optimization"
                                        description="Real-time route adjustments and inventory redistribution strategies."
                                        delay={0.3}
                                    />
                                </div>

                                {/* Graph */}
                                <div className="w-full mb-8 animate-fade-in">
                                    <CausalGraph graphData={data.causal_graph} />
                                </div>

                                {/* Stats & Plans */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                                    {/* Action Matrix */}
                                    <div className="bg-[#0a0a0a]/80 backdrop-blur rounded-xl border border-white/10 p-6 flex flex-col h-[500px]">
                                        <div className="flex justify-between items-center mb-6">
                                            <h3 className="text-white font-bold flex items-center gap-2 text-lg">
                                                <Layers size={20} className="text-amber-500" /> Strategic Action Matrix
                                            </h3>
                                            <span className="text-xs bg-amber-500/10 text-amber-500 px-3 py-1 rounded-full animate-pulse font-bold flex items-center gap-2">
                                                <AlertTriangle size={12} />
                                                {data.action_plan.items.length} ACTIVE PROTOCOLS
                                            </span>
                                        </div>
                                        <div className="space-y-3 flex-1 overflow-y-auto custom-scrollbar pr-2">
                                            {data.action_plan.items.map((item, i) => (
                                                <div key={i} className="p-5 rounded-xl bg-white/5 border border-white/5 hover:border-white/20 hover:bg-white/10 transition-all cursor-pointer group">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <h4 className="font-bold text-gray-100 group-hover:text-neon-blue transition-colors text-base">{item.action}</h4>
                                                        <span className={`text-[10px] uppercase font-bold px-2 py-1 rounded-full tracking-wider ${item.priority === 'Critical' ? 'bg-red-500/20 text-red-500' : item.priority === 'High' ? 'bg-orange-500/20 text-orange-500' : 'bg-blue-500/20 text-blue-500'}`}>
                                                            {item.priority}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2 mb-4 text-xs text-gray-400 bg-black/30 p-2 rounded-lg border border-white/5">
                                                        <Activity size={12} className="text-red-400" />
                                                        <span className="font-mono">TRIGGER: {item.trigger_event}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center border-t border-white/5 pt-3">
                                                        <span className="text-xs text-gray-500 flex items-center gap-2"><Users size={12} /> {item.assigned_to}</span>
                                                        <button className="text-xs text-neon-blue flex items-center gap-1 group-hover:translate-x-1 transition-transform font-bold">
                                                            EXECUTE <ArrowRight size={12} />
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Stats & Charts */}
                                    <div className="space-y-6 flex flex-col h-[500px]">
                                        <div className="flex-1 bg-[#0a0a0a]/80 backdrop-blur rounded-xl border border-white/10 p-6 min-h-0 flex flex-col">
                                            <div className="flex justify-between items-center mb-4 flex-shrink-0">
                                                <h3 className="text-white font-bold flex items-center gap-2">
                                                    <Activity size={18} className="text-emerald-500" /> Supply Dynamics
                                                </h3>
                                            </div>
                                            <div className="flex-1 min-h-0 w-full">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <AreaChart data={MOCK_DEMAND_DATA}>
                                                        <defs>
                                                            <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                            </linearGradient>
                                                            <linearGradient id="colorSupply" x1="0" y1="0" x2="0" y2="1">
                                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                                            </linearGradient>
                                                        </defs>
                                                        <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                                                        <XAxis dataKey="day" stroke="#555" tick={{ fill: '#666', fontSize: 12 }} />
                                                        <YAxis stroke="#555" tick={{ fill: '#666', fontSize: 12 }} />
                                                        <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#fff' }} />
                                                        <Area type="monotone" dataKey="demand" stroke="#3b82f6" fillOpacity={1} fill="url(#colorDemand)" strokeWidth={2} />
                                                        <Area type="monotone" dataKey="supply" stroke="#10b981" fillOpacity={1} fill="url(#colorSupply)" strokeWidth={2} />
                                                    </AreaChart>
                                                </ResponsiveContainer>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 h-32 flex-shrink-0">
                                            {data?.dashboard_payload.kpis.map((kpi, i) => (
                                                <div key={i} className="bg-[#0a0a0a]/80 backdrop-blur rounded-xl border border-white/10 p-5 flex flex-col justify-center">
                                                    <p className="text-xs text-gray-500 mb-1 flex items-center gap-2 uppercase tracking-wide font-bold"><Activity size={12} /> {kpi.label}</p>
                                                    <p className={`text-3xl font-black ${kpi.threshold === 'Critical' ? 'text-red-500' : kpi.threshold === 'Warning' ? 'text-amber-500' : 'text-emerald-500'}`}>
                                                        {kpi.value} <span className="text-sm text-gray-600 font-normal">{kpi.unit}</span>
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* --- CONFIRMATION MODAL (MOVED TO ROOT) --- */}
            <AnimatePresence>
                {pendingScan && (
                    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-md pointer-events-auto">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#0a0a0a] border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-[0_0_50px_rgba(0,0,0,0.8)] relative overflow-hidden pointer-events-auto"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-neon-blue/5 to-purple-600/5" />

                            <h3 className="text-2xl font-bold text-white mb-4 relative z-10 flex items-center gap-2">
                                <AlertTriangle className="text-amber-500" /> Confirm Analysis?
                            </h3>
                            <p className="text-gray-400 mb-6 relative z-10">
                                Initiating deep-scan causal analysis at coordinates:
                                <br />
                                <span className="text-neon-blue font-mono font-bold">
                                    {pendingScan[0].toFixed(6)}, {pendingScan[1].toFixed(6)}
                                </span>
                            </p>

                            <div className="flex gap-4 relative z-10">
                                <button
                                    onClick={() => setPendingScan(null)}
                                    className="flex-1 py-3 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 transition-colors font-bold cursor-pointer"
                                >
                                    CANCEL
                                </button>
                                <button
                                    onClick={triggerScan}
                                    className="flex-1 py-3 bg-neon-blue/20 border border-neon-blue/50 text-neon-blue rounded-lg hover:bg-neon-blue/30 transition-colors font-bold shadow-[0_0_15px_rgba(0,247,255,0.3)] cursor-pointer"
                                >
                                    INITIALIZE SCAN
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* --- FULL SCREEN LOADING OVERLAY --- */}
            <AnimatePresence>
                {loading && (
                    <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-black/90 backdrop-blur-xl pointer-events-auto">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            className="flex flex-col items-center"
                        >
                            <div className="relative mb-8">
                                <div className="absolute inset-0 bg-neon-blue/20 blur-xl rounded-full animate-pulse" />
                                <Cpu className="w-24 h-24 text-neon-blue animate-spin relative z-10" />
                            </div>
                            <h2 className="text-3xl font-black text-white tracking-tighter mb-2">
                                ANALYSING <span className="text-neon-blue">SECTOR DATA</span>
                            </h2>
                            <p className="text-emerald-400 font-mono tracking-widest animate-pulse">
                                INGESTING REAL-TIME SIGNALS...
                            </p>
                            <div className="mt-8 w-64 h-1 bg-white/10 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-gradient-to-r from-neon-blue via-emerald-400 to-neon-blue"
                                    initial={{ x: '-100%' }}
                                    animate={{ x: '100%' }}
                                    transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                />
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default RetailPage;
