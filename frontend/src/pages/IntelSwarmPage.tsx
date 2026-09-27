import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe as GlobeIcon, Crosshair, Loader2, MapPin, Search, RotateCcw, Navigation, Database, ShieldCheck } from 'lucide-react';
import Globe, { GlobeMethods } from 'react-globe.gl';
import InsightCard from '../components/InsightCard';
import LocationStatusCard from '../components/LocationStatusCard';
import { useAgentSwarm } from '../hooks/useAgentSwarm';

const IntelSwarmPage: React.FC = () => {
    const globeRef = useRef<GlobeMethods | undefined>(undefined);
    const containerRef = useRef<HTMLDivElement>(null);
    const [globeDimensions, setGlobeDimensions] = useState({ width: 0, height: 0 });
    const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null);
    const [manualLat, setManualLat] = useState('');
    const [manualLng, setManualLng] = useState('');
    const { results, isSwarmRunning, triggerSwarm } = useAgentSwarm();

    const pointsData = selectedLocation ? [{ lat: selectedLocation.lat, lng: selectedLocation.lng, size: 0.6, color: '#00f3ff' }] : [];
    const ringsData = selectedLocation ? [{ lat: selectedLocation.lat, lng: selectedLocation.lng, maxR: 3, propagationSpeed: 2, repeatPeriod: 1200 }] : [];

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;
        const observer = new ResizeObserver(entries => entries.forEach(entry => setGlobeDimensions({ width: entry.contentRect.width, height: entry.contentRect.height })));
        observer.observe(container);
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        if (!globeRef.current) return;
        const controls = globeRef.current.controls();
        if (controls) { controls.autoRotate = true; controls.autoRotateSpeed = 0.4; controls.enableZoom = true; }
        globeRef.current.pointOfView({ lat: 20, lng: 0, altitude: 2.5 }, 0);
    }, []);

    const investigateLocation = useCallback((lat: number, lng: number) => {
        setSelectedLocation({ lat, lng });
        setManualLat(lat.toFixed(4)); setManualLng(lng.toFixed(4));
        if (globeRef.current) {
            const controls = globeRef.current.controls(); if (controls) controls.autoRotate = false;
            globeRef.current.pointOfView({ lat, lng, altitude: 1.8 }, 800);
        }
        triggerSwarm(lat, lng);
    }, [triggerSwarm]);

    const handleGlobeClick = useCallback(({ lat, lng }: { lat: number; lng: number }) => investigateLocation(lat, lng), [investigateLocation]);
    const handleManualSubmit = useCallback(() => {
        const lat = parseFloat(manualLat), lng = parseFloat(manualLng);
        if (Number.isNaN(lat) || Number.isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return;
        investigateLocation(lat, lng);
    }, [manualLat, manualLng, investigateLocation]);
    const handleReset = useCallback(() => {
        setSelectedLocation(null); setManualLat(''); setManualLng('');
        if (globeRef.current) { const controls = globeRef.current.controls(); if (controls) controls.autoRotate = true; globeRef.current.pointOfView({ lat: 20, lng: 0, altitude: 2.5 }, 800); }
    }, []);

    const agentResults = Object.values(results);
    const completedCount = agentResults.filter(r => r.status === 'success').length;
    const totalCount = agentResults.length;

    return <div className="h-full w-full flex flex-col overflow-hidden bg-black">
        <div className="flex-shrink-0 flex flex-col xl:flex-row xl:items-center justify-between gap-4 px-6 py-4 border-b border-white/10 bg-black/80 backdrop-blur-xl z-10">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-400/10 flex items-center justify-center border border-cyan-400/30"><GlobeIcon className="w-5 h-5 text-cyan-300" /></div>
                <div><h1 className="text-lg font-black tracking-[0.12em] text-white">EARTH <span className="text-cyan-300">OBSERVATORY</span></h1><p className="text-[10px] text-gray-500 uppercase tracking-[0.2em]">Geospatial evidence & environmental investigation</p></div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2"><MapPin className="w-4 h-4 text-gray-500"/><input aria-label="Latitude" type="text" placeholder="Latitude" value={manualLat} onChange={e=>setManualLat(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleManualSubmit()} className="w-24 bg-transparent text-sm text-white font-mono placeholder-gray-600 outline-none"/><div className="w-px h-4 bg-white/20"/><input aria-label="Longitude" type="text" placeholder="Longitude" value={manualLng} onChange={e=>setManualLng(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleManualSubmit()} className="w-24 bg-transparent text-sm text-white font-mono placeholder-gray-600 outline-none"/></div>
                <button onClick={handleManualSubmit} disabled={isSwarmRunning||!manualLat||!manualLng} className="flex items-center gap-2 px-4 py-2 bg-cyan-400/10 border border-cyan-400/30 rounded-lg text-cyan-300 text-sm font-bold hover:bg-cyan-400/20 disabled:opacity-30">{isSwarmRunning?<Loader2 className="w-4 h-4 animate-spin"/>:<Search className="w-4 h-4"/>} INVESTIGATE</button>
                {selectedLocation&&<button onClick={handleReset} className="p-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white" title="Reset observation"><RotateCcw className="w-4 h-4"/></button>}
            </div>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            <div ref={containerRef} className="relative lg:w-[48%] min-h-[46vh] lg:min-h-0 flex-shrink-0 bg-black overflow-hidden">
                <Globe ref={globeRef} width={globeDimensions.width} height={globeDimensions.height} globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg" bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png" backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png" atmosphereColor="#00f3ff" atmosphereAltitude={0.2} pointsData={pointsData} pointAltitude="size" pointColor="color" pointRadius={0.5} pointsMerge={false} ringsData={ringsData} ringColor={()=>'#00f3ff'} ringMaxRadius="maxR" ringPropagationSpeed="propagationSpeed" ringRepeatPeriod="repeatPeriod" ringAltitude={0.01} onGlobeClick={handleGlobeClick} animateIn />
                {!selectedLocation&&<div className="absolute inset-x-0 bottom-8 pointer-events-none flex justify-center px-4"><motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} className="max-w-lg px-5 py-3 bg-black/75 backdrop-blur-md border border-white/10 rounded-xl text-center"><div className="flex justify-center items-center gap-2 text-cyan-300"><Crosshair className="w-4 h-4"/><span className="text-sm font-semibold">Select a location to investigate</span></div><p className="text-xs text-gray-500 mt-1">Coordinate specialist agents around one geographic observation point.</p></motion.div></div>}
                {isSwarmRunning&&<div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-2 bg-black/75 backdrop-blur border border-cyan-400/30 rounded-lg"><Loader2 className="w-3 h-3 text-cyan-300 animate-spin"/><span className="text-xs text-cyan-300 font-mono">COLLECTING EVIDENCE {completedCount}/{totalCount}</span></div>}
            </div>

            <div className="flex-1 border-l border-white/10 overflow-y-auto custom-scrollbar bg-black/50">
                <AnimatePresence mode="wait">{!selectedLocation?<motion.div key="empty" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="min-h-full flex flex-col items-center justify-center text-center px-8 py-12"><div className="w-24 h-24 rounded-full border border-white/10 flex items-center justify-center mb-6 relative"><div className="absolute inset-0 rounded-full border border-dashed border-white/20 animate-[spin_20s_linear_infinite]"/><Navigation className="w-10 h-10 text-white/20"/></div><h3 className="text-xl font-bold text-gray-300 mb-2">Choose an observation point</h3><p className="text-sm text-gray-600 max-w-md">Select a coordinate on Earth to gather location-specific environmental evidence through the available specialist agents.</p><div className="grid sm:grid-cols-2 gap-3 max-w-lg mt-8 text-left"><div className="border border-white/10 rounded-xl p-4 bg-white/[0.02]"><Database className="text-cyan-300 w-4 h-4 mb-2"/><div className="text-sm text-white">Evidence inputs</div><div className="text-xs text-gray-600 mt-1">Environmental observations and specialist outputs remain inputs to research, not automatic conclusions.</div></div><div className="border border-white/10 rounded-xl p-4 bg-white/[0.02]"><ShieldCheck className="text-cyan-300 w-4 h-4 mb-2"/><div className="text-sm text-white">Validation required</div><div className="text-xs text-gray-600 mt-1">Findings should be challenged, cross-checked and traced before advancing.</div></div></div></motion.div>:<motion.div key="results" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="p-6 space-y-6"><div><div className="text-[10px] uppercase tracking-[0.22em] text-cyan-300 mb-2">Observation workspace</div><h2 className="text-xl font-bold">Location evidence</h2><p className="text-xs text-gray-500 mt-1">Specialist outputs for this coordinate. Treat each result according to its source, method and uncertainty.</p></div><LocationStatusCard lat={selectedLocation.lat} lng={selectedLocation.lng} agentCount={totalCount} onClose={handleReset}/><div className="grid grid-cols-1 xl:grid-cols-2 gap-4">{agentResults.map((agent,index)=><InsightCard key={agent.agentId} agentId={agent.agentId} status={agent.status} data={agent.data} delay={0.05+index*0.04}/>)}</div></motion.div>}</AnimatePresence>
            </div>
        </div>
    </div>;
};

export default IntelSwarmPage;
