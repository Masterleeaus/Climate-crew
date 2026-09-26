import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Globe as GlobeIcon,
    Crosshair,
    Loader2,
    MapPin,
    Zap,
    RotateCcw,
    Navigation
} from 'lucide-react';
import Globe, { GlobeMethods } from 'react-globe.gl';
import InsightCard from '../components/InsightCard';
import LocationStatusCard from '../components/LocationStatusCard';
import { useAgentSwarm } from '../hooks/useAgentSwarm';

const IntelSwarmPage: React.FC = () => {
    const globeRef = useRef<GlobeMethods | undefined>(undefined);
    const containerRef = useRef<HTMLDivElement>(null);
    const [globeDimensions, setGlobeDimensions] = useState({ width: 0, height: 0 });

    // Location state
    const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null);
    const [manualLat, setManualLat] = useState('');
    const [manualLng, setManualLng] = useState('');

    // Swarm hook
    const { results, isSwarmRunning, triggerSwarm } = useAgentSwarm();

    // Globe marker data
    const pointsData = selectedLocation
        ? [{ lat: selectedLocation.lat, lng: selectedLocation.lng, size: 0.6, color: '#00f3ff' }]
        : [];

    // Ring pulse at selected location
    const ringsData = selectedLocation
        ? [{ lat: selectedLocation.lat, lng: selectedLocation.lng, maxR: 3, propagationSpeed: 2, repeatPeriod: 1200 }]
        : [];

    // Resize observer for globe container
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                setGlobeDimensions({
                    width: entry.contentRect.width,
                    height: entry.contentRect.height,
                });
            }
        });

        observer.observe(container);
        return () => observer.disconnect();
    }, []);

    // Style the globe on mount
    useEffect(() => {
        if (globeRef.current) {
            const controls = globeRef.current.controls();
            if (controls) {
                controls.autoRotate = true;
                controls.autoRotateSpeed = 0.4;
                controls.enableZoom = true;
            }
            // Set initial POV
            globeRef.current.pointOfView({ lat: 20, lng: 0, altitude: 2.5 }, 0);
        }
    }, [globeRef.current]);

    // Handle globe click
    const handleGlobeClick = useCallback(({ lat, lng }: { lat: number; lng: number }) => {
        setSelectedLocation({ lat, lng });
        setManualLat(lat.toFixed(4));
        setManualLng(lng.toFixed(4));

        // Stop auto-rotate and focus on point
        if (globeRef.current) {
            const controls = globeRef.current.controls();
            if (controls) controls.autoRotate = false;
            globeRef.current.pointOfView({ lat, lng, altitude: 1.8 }, 800);
        }

        // Trigger swarm
        triggerSwarm(lat, lng);
    }, [triggerSwarm]);

    // Handle manual coordinate submission
    const handleManualSubmit = useCallback(() => {
        const lat = parseFloat(manualLat);
        const lng = parseFloat(manualLng);
        if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return;

        setSelectedLocation({ lat, lng });

        if (globeRef.current) {
            const controls = globeRef.current.controls();
            if (controls) controls.autoRotate = false;
            globeRef.current.pointOfView({ lat, lng, altitude: 1.8 }, 800);
        }

        triggerSwarm(lat, lng);
    }, [manualLat, manualLng, triggerSwarm]);

    // Reset everything
    const handleReset = useCallback(() => {
        setSelectedLocation(null);
        setManualLat('');
        setManualLng('');

        if (globeRef.current) {
            const controls = globeRef.current.controls();
            if (controls) controls.autoRotate = true;
            globeRef.current.pointOfView({ lat: 20, lng: 0, altitude: 2.5 }, 800);
        }
    }, []);

    const agentResults = Object.values(results);
    const completedCount = agentResults.filter(r => r.status === 'success').length;
    const totalCount = agentResults.length;

    return (
        <div className="h-full w-full flex flex-col overflow-hidden bg-black">

            {/* Top Bar */}
            <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/80 backdrop-blur-xl z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-neon-blue/20 flex items-center justify-center border border-neon-blue/40">
                        <GlobeIcon className="w-5 h-5 text-neon-blue" />
                    </div>
                    <div>
                        <h1 className="text-lg font-black tracking-[0.15em] text-white">
                            INTEL <span className="text-neon-blue">SWARM</span>
                        </h1>
                        <p className="text-[10px] text-gray-500 font-mono tracking-wider">GLOBAL INTELLIGENCE NETWORK</p>
                    </div>
                </div>

                {/* Manual Coordinate Input */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                        <MapPin className="w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Lat"
                            value={manualLat}
                            onChange={(e) => setManualLat(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleManualSubmit()}
                            className="w-24 bg-transparent text-sm text-white font-mono placeholder-gray-600 outline-none"
                        />
                        <div className="w-px h-4 bg-white/20" />
                        <input
                            type="text"
                            placeholder="Lng"
                            value={manualLng}
                            onChange={(e) => setManualLng(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleManualSubmit()}
                            className="w-24 bg-transparent text-sm text-white font-mono placeholder-gray-600 outline-none"
                        />
                    </div>

                    <button
                        onClick={handleManualSubmit}
                        disabled={isSwarmRunning || !manualLat || !manualLng}
                        className="flex items-center gap-2 px-4 py-2 bg-neon-blue/20 border border-neon-blue/40 rounded-lg text-neon-blue text-sm font-bold tracking-wider hover:bg-neon-blue/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        {isSwarmRunning ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Zap className="w-4 h-4" />
                        )}
                        DEPLOY
                    </button>

                    {selectedLocation && (
                        <button
                            onClick={handleReset}
                            className="p-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                            title="Reset"
                        >
                            <RotateCcw className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">

                {/* Left: 3D Globe */}
                <div ref={containerRef} className="relative w-[45%] flex-shrink-0 bg-black overflow-hidden">
                    {/* Globe */}
                    <Globe
                        ref={globeRef}
                        width={globeDimensions.width}
                        height={globeDimensions.height}
                        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
                        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
                        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
                        atmosphereColor="#00f3ff"
                        atmosphereAltitude={0.2}
                        // Points
                        pointsData={pointsData}
                        pointAltitude="size"
                        pointColor="color"
                        pointRadius={0.5}
                        pointsMerge={false}
                        // Rings
                        ringsData={ringsData}
                        ringColor={() => '#00f3ff'}
                        ringMaxRadius="maxR"
                        ringPropagationSpeed="propagationSpeed"
                        ringRepeatPeriod="repeatPeriod"
                        ringAltitude={0.01}
                        // Interaction
                        onGlobeClick={handleGlobeClick}
                        animateIn={true}
                    />

                    {/* Globe Overlay: Click Prompt */}
                    {!selectedLocation && (
                        <div className="absolute inset-0 pointer-events-none flex items-end justify-center pb-10">
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex items-center gap-2 px-4 py-2 bg-black/60 backdrop-blur-md border border-white/10 rounded-full"
                            >
                                <Crosshair className="w-4 h-4 text-neon-blue animate-pulse" />
                                <span className="text-sm text-gray-300 font-mono">Click anywhere on the globe to deploy swarm</span>
                            </motion.div>
                        </div>
                    )}

                    {/* Globe Overlay: Swarm Running Indicator */}
                    {isSwarmRunning && (
                        <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 bg-black/70 backdrop-blur border border-neon-blue/30 rounded-full">
                            <Loader2 className="w-3 h-3 text-neon-blue animate-spin" />
                            <span className="text-xs text-neon-blue font-mono">
                                SCANNING {completedCount}/{totalCount}
                            </span>
                        </div>
                    )}
                </div>

                {/* Right: Results Panel */}
                <div className="flex-1 border-l border-white/10 overflow-y-auto custom-scrollbar bg-black/50">
                    <AnimatePresence mode="wait">
                        {!selectedLocation ? (
                            /* Empty State */
                            <motion.div
                                key="empty"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="h-full flex flex-col items-center justify-center text-center px-8"
                            >
                                <div className="w-24 h-24 rounded-full border border-white/10 flex items-center justify-center mb-6 relative">
                                    <div className="absolute inset-0 rounded-full border border-dashed border-white/20 animate-[spin_20s_linear_infinite]" />
                                    <Navigation className="w-10 h-10 text-white/20" />
                                </div>
                                <h3 className="text-xl font-bold text-gray-400 mb-2 tracking-wide">AWAITING TARGET</h3>
                                <p className="text-sm text-gray-600 max-w-sm">
                                    Select a coordinate on the globe or enter latitude and longitude manually to deploy the intelligence swarm.
                                </p>
                            </motion.div>
                        ) : (
                            /* Results Grid */
                            <motion.div
                                key="results"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="p-6 space-y-6"
                            >
                                {/* Location Status */}
                                <LocationStatusCard
                                    lat={selectedLocation.lat}
                                    lng={selectedLocation.lng}
                                    agentCount={totalCount}
                                    onClose={handleReset}
                                />

                                {/* Agent Cards Grid */}
                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                                    {agentResults.map((agent, index) => (
                                        <InsightCard
                                            key={agent.agentId}
                                            agentId={agent.agentId}
                                            status={agent.status}
                                            data={agent.data}
                                            delay={0.05 + index * 0.04}
                                        />
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default IntelSwarmPage;
